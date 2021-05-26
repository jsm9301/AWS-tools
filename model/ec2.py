import boto3
from util.utils import *


class DefaultEc2:
    def __init__(self, vpc_id, region="us-east-2"):
        self.ec2 = boto3.resource("ec2", region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.vpc = self.ec2.Vpc(vpc_id)

    def create_sg(self, group_name, desc="None", inbound_list=None):
        if inbound_list is None:
            inbound_list = [{"cidr": "0.0.0.0/0", "protocol": "tcp", "f_port": 22, "t_port": 22}]

        securitygroup = self.ec2.create_security_group(GroupName=group_name,
                                                       Description=desc,
                                                       VpcId=self.vpc.id)
        add_name_tag(securitygroup, group_name)

        for inbound in inbound_list:
            securitygroup.authorize_ingress(CidrIp=inbound.get("cidr"),
                                            IpProtocol=inbound.get("protocol"),
                                            FromPort=inbound.get("f_port"),
                                            ToPort=inbound.get("t_port"))

        return securitygroup

    def create_pem_key(self, pem_key_name):
        with open(pem_key_name+'.pem', 'w') as key_file:
            key_pair = self.ec2.create_key_pair(KeyName=pem_key_name)
            key_pair_out = str(key_pair.key_material)
            key_file.write(key_pair_out)

    def create_ec2(self, ec2_name, subnet_id, sg_id_list, pem_key_name, image_id="ami-077e31c4939f6a2f3", instance_type="t2.micro", associate_p_ip=False):
        instances = self.ec2.create_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            MaxCount=1,
            MinCount=1,
            NetworkInterfaces=[{
                'SubnetId': subnet_id,
                'DeviceIndex': 0,
                'AssociatePublicIpAddress': associate_p_ip,
                'Groups': sg_id_list
            }],
            KeyName=pem_key_name)
        add_name_tag_ec2(self.ec2_client, instances[0].id, ec2_name)

        return instances

    def delete_ec2_by_ids(self, instance_ids):
        self.ec2.instances.filter(InstanceIds=instance_ids).terminate()

        self.ec2_client.get_waiter('instance_terminated') \
            .wait(InstanceIds=instance_ids)

    def delete_key_pair_by_name(self, key_name):
        self.ec2_client.delete_key_pair(KeyName=key_name)

    def delete_sg_by_id(self, group_id):
        self.ec2_client.delete_security_group(GroupId=group_id)

    def release_eip_by_id(self, allocation_id):
        self.ec2_client.release_address(AllocationId=allocation_id)

if __name__ == '__main__':
    d_ec2 = DefaultEc2(vpc_id="", region="us-east-1")

    ### make bastion
    # d_ec2.create_pem_key("TEST-PEM")
    bastion_sg = d_ec2.create_sg("bastion-SG")
    bastion = d_ec2.create_ec2(ec2_name="Bastion-EC2",
                     subnet_id="",
                     sg_id_list=[bastion_sg.id],
                     pem_key_name="TEST-PEM",
                     associate_p_ip=True)

    ### make web server on private subnet
    inbound_list = [{"cidr": "0.0.0.0/0", "protocol": "tcp", "f_port": 80, "t_port": 80},
                    {"cidr": "10.0.0.0/16", "protocol": "tcp", "f_port": 22, "t_port": 22}]
    web_sg = d_ec2.create_sg(group_name="web-SG", inbound_list=inbound_list)

    web_1 = d_ec2.create_ec2(ec2_name="WEB-1",
                     subnet_id="",
                     sg_id_list=[web_sg.id],
                     pem_key_name="TEST-PEM",
                     associate_p_ip=False)
    web_2 = d_ec2.create_ec2(ec2_name="WEB-2",
                     subnet_id="",
                     sg_id_list=[web_sg.id],
                     pem_key_name="TEST-PEM",
                     associate_p_ip=False)

    d_ec2.ec2_client.get_waiter("instance_status_ok").wait(
        InstanceIds=[bastion[0].id, web_1[0].id, web_2[0].id]
    )