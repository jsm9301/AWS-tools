from model.ec2 import DefaultEc2
from model.vpc import DefaultVPC
from model.elb import ELB
from util.ssh import SSHConnector
from util.utils import *
from util.decorators import *


class DefaultBuilder:
    """
    This class will provisioning automatically default infrastructure when we do PoC
    Architecture: https://user-images.githubusercontent.com/20178616/119307386-99735e80-bca6-11eb-984a-4bf086808bb9.png

    Init
        region: region
        vpc_cidr: CIDR block to make VPC
        vpc_name: VPC name
        pub_sub_num: number of public subnet
        pri_sub_num: number of private subnet
        ami: EC2 ami id
        bastion_subnet: subnet index to install bastion
        bastion_name: bastion ec2 name
        pem_key_name: key pair name
        web_inbound_list: inbound list for web security group
        user_name: EC2 user name(default: ec2-user)
        pem_key_path: key pair path
        alb_name: load balancer name
        tgr: target group name
    """
    def __init__(self, region, vpc_cidr, vpc_name,
                 pub_sub_num, pri_sub_num, ami, bastion_subnet,
                 bastion_name, pem_key_name, web_inbound_list,
                 user_name, pem_key_path, alb_name, tgr_name):

        self.web_list = []

        self.default_vpc = None
        self.region = region
        self.vpc_cidr = vpc_cidr
        self.vpc_name = vpc_name
        self.pub_sub_num = pub_sub_num
        self.pri_sub_num = pri_sub_num
        self.bastion_subnet = bastion_subnet
        self.ami = ami
        self.bastion_name = bastion_name
        self.pem_key_name = pem_key_name
        self.web_inbound_list = web_inbound_list
        self.user_name = user_name
        self.pem_key_path = pem_key_path
        self.alb_name = alb_name
        self.tgr_name = tgr_name

    def _set_vpc(self):
        """Create VPC resources(subnet, routing table, internet gateway, NAT)"""
        default_vpc = DefaultVPC(region=self.region) \
            .create_VPC(cidr_block=self.vpc_cidr, vpc_name=self.vpc_name) \
            .create_sub(pub_sub_num=self.pub_sub_num, pri_sub_num=self.pri_sub_num) \
            .create_ig() \
            .set_ig_rtb() \
            .create_nat() \
            .set_nat_rtb()

        self.default_vpc = default_vpc

    def _set_bastion_ec2(self):
        """Create bastion EC2 on public subnet"""
        default_ec2 = DefaultEc2(region=self.region, vpc_id=self.default_vpc.vpc.id)

        ### make bastion
        default_ec2.create_pem_key(pem_key_name=self.pem_key_name)

        bastion_sg = default_ec2.create_sg(group_name="Bastion-SG")

        subnet_id = self.default_vpc.pub_sub_list[self.bastion_subnet].id
        bastion = default_ec2.create_ec2(ec2_name=self.bastion_name,
                                         subnet_id=subnet_id,
                                         sg_id_list=[bastion_sg.id],
                                         pem_key_name=self.pem_key_name,
                                         associate_p_ip=True,
                                         image_id=self.ami)

        self.bastion = bastion[0]
        self.default_ec2 = default_ec2

    def _set_web_ec2(self):
        """
        Create Web Server EC2 on all private subnet
        If you have 2 private subnets, then this function will build a EC2 each
        """
        ### make web server on private subnet
        self.web_sg = self.default_ec2.create_sg(group_name="web-SG", inbound_list=self.web_inbound_list)

        subnet_list = self.default_vpc.pri_sub_list
        for i in range(len(subnet_list)):
            web = self.default_ec2.create_ec2(ec2_name="WEB-{}".format(i),
                                              subnet_id=subnet_list[i].id,
                                              sg_id_list=[self.web_sg.id],
                                              pem_key_name=self.pem_key_name,
                                              associate_p_ip=False,
                                              image_id=self.ami)

            self.web_list.append(web[0])

    @Printer(pre="ec2 instances", post="Created ec2 instances")
    def _check_ec2(self):
        """Wait all EC2 running"""
        all_instance_ids = [self.bastion.id]
        for web in self.web_list:
            all_instance_ids.append(web.id)

        self.default_ec2.ec2_client.get_waiter("instance_status_ok") \
            .wait(InstanceIds=all_instance_ids)

    def _install_nginx(self):
        """Connect to web server on private subnet and install nginx server"""
        ssh = SSHConnector(region=self.region)

        for web in self.web_list:
            with ssh.tunneling(host=get_ip(ssh.ec2, self.bastion.id, True),
                               host_port=22,
                               user=self.user_name,
                               pem_key_path=self.pem_key_path,
                               remote_ip=get_ip(ssh.ec2, web.id, False),
                               remote_port=22) as tunnel:
                tunnel.start()
                ssh.connect_ssh(ip_address="127.0.0.1", port=10022, pem_key_path=self.pem_key_path)
                ssh.command_delivery("sudo amazon-linux-extras install nginx1 -y && sudo service nginx start")
                tunnel.stop()

    def _set_alb(self):
        """
        Create application load balancer and target group
        Register target and Listener
        """
        elb = ELB(region=self.region)

        ### create ELB
        pub_sub_list = [sub.id for sub in self.default_vpc.pub_sub_list]
        elb_response = elb.create_elb(elb_name=self.alb_name,
                                      subnet_list=pub_sub_list,
                                      sg_list=[self.web_sg.id])
        elb_arn = elb_response['LoadBalancers'][0]['LoadBalancerArn']

        ### create target group
        tgr_response = elb.create_tgr(tgr_name=self.tgr_name,
                                      vpc_id=self.default_vpc.vpc.id)
        tgr_arn = tgr_response['TargetGroups'][0]['TargetGroupArn']

        ### register targets to target group
        target_list = [web.id for web in self.web_list]
        elb.register_targets(targets=target_list, tgr_arn=tgr_arn)

        ### register target group to elb
        elb.create_listener(elb_arn=elb_arn, tgr_arn=tgr_arn)

        print("DNS is : {}".format(elb_response["LoadBalancers"][0]["DNSName"]))

    def build(self):
        """Build default infrastructure"""
        self._set_vpc()
        self._set_bastion_ec2()
        self._set_web_ec2()
        self._check_ec2()
        self._install_nginx()
        self._set_alb()


if __name__ == '__main__':
    ## params
    ### VPC
    region = "ap-northeast-2"
    vpc_name = "TEST-VPC"
    vpc_cidr = "10.0.0.0/16"
    pub_sub_num = 2
    pri_sub_num = 2

    ### EC2
    bastion_name = "Bastion"
    bastion_subnet = 0
    pem_key_name = "TEST-PEM"
    ami = "ami-0f2c95e9fe3f8f80e"
    web_inbound_list = [{"cidr": "0.0.0.0/0", "protocol": "tcp", "f_port": 80, "t_port": 80},
                        {"cidr": "10.0.0.0/16", "protocol": "tcp", "f_port": 22, "t_port": 22}]
    user_name = "ec2-user"
    pem_key_path = "./TEST-PEM.pem"

    ### alb
    alb_name = "TEST-ALB"
    tgr_name = "TEST-TGR"

    ### Build Default infra
    DefaultBuilder(region=region, vpc_name=vpc_name, vpc_cidr=vpc_cidr,
                   pub_sub_num=2, pri_sub_num=2, bastion_subnet=bastion_subnet, ami=ami, bastion_name=bastion_name,
                   pem_key_name=pem_key_name, web_inbound_list=web_inbound_list,
                   user_name=user_name, pem_key_path=pem_key_path, alb_name=alb_name,
                   tgr_name=tgr_name) \
        .build()
