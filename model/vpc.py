import boto3
import logging
from util.utils import *


class DefaultVPC:
    def __init__(self, region="us-east-2"):
        self.logger = logging.getLogger("logger")
        self.logger.setLevel(logging.INFO)

        stream_hander = logging.StreamHandler()
        self.logger.addHandler(stream_hander)

        self.ec2 = boto3.resource("ec2", region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.region = region
        self.pub_sub_list = []
        self.pri_sub_list = []

    def _get_cidr_pre(self, cidr_block):
        tmp = cidr_block.split('/')
        cidr_list = cidr_block.split(".")
        cidr_octet = int(int(tmp[1]) / 8)

        result = ""
        for i in range(cidr_octet):
            result += cidr_list[i] + "."

        return result, cidr_octet

    def _get_sub_cidr_list(self, end, start=1):
        cidr_list = []
        for i in range(start, end):
            result = ""
            if self.cidr_octet == 1:
                result = "{}{}.0.0/16".format(self.sub_cidr_pre, str(i))
            elif self.cidr_octet == 2:
                result = "{}{}.0/24".format(self.sub_cidr_pre, str(i))

            cidr_list.append(result)

        return cidr_list

    def _get_az(self, num):
        if num % 2 == 0:
            return "a"
        return "c"

    def create_VPC(self, cidr_block, vpc_name="TEST-VPC"):
        self.sub_cidr_pre, self.cidr_octet = self._get_cidr_pre(cidr_block)

        self.vpc = self.ec2.create_vpc(CidrBlock=cidr_block)

        add_name_tag(self.vpc, vpc_name)
        self.vpc.wait_until_available()

        self.logger.info("======== created VPC ========")

        return self

    def create_sub(self, pub_sub_num=2, pri_sub_num=2):
        pub_cidr_list = self._get_sub_cidr_list(end=pub_sub_num + 1, start=1)
        pri_cidr_list = self._get_sub_cidr_list(start=pub_sub_num + 1, end=pub_sub_num + pri_sub_num + 1)

        for i in range(len(pub_cidr_list)):
            subnet = self.ec2.create_subnet(CidrBlock=pub_cidr_list[i],
                                            VpcId=self.vpc.id,
                                            AvailabilityZone="{}{}".format(self.region, self._get_az(i)))

            add_name_tag(subnet, "PubSub-{}{}".format(str(i + 1), self._get_az(i)))

            self.pub_sub_list.append(subnet)

        for i in range(len(pri_cidr_list)):
            subnet = self.ec2.create_subnet(CidrBlock=pri_cidr_list[i],
                                            VpcId=self.vpc.id,
                                            AvailabilityZone="{}{}".format(self.region, self._get_az(i)))

            add_name_tag(subnet, "PriSub-{}{}".format(str(i + 1), self._get_az(i)))

            self.pri_sub_list.append(subnet)

        self.logger.info("======== created all Subnets ========")

        return self

    def create_ig(self):
        self.ig = self.ec2.create_internet_gateway()
        add_name_tag(self.ig, "IGW")

        self.vpc.attach_internet_gateway(InternetGatewayId=self.ig.id)

        self.logger.info("======== created internet Gateway ========")

        return self

    def set_ig_rtb(self):
        ig_rtb = self.vpc.create_route_table()
        add_name_tag(ig_rtb, "IG-RTB")

        ig_rtb.create_route(
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=self.ig.id
        )

        for subnet in self.pub_sub_list:
            ig_rtb.associate_with_subnet(SubnetId=subnet.id)

        return self

    def _create_eip(self):
        return self.ec2_client.allocate_address(Domain='vpc')

    def create_nat(self, subnet_id=None):
        nat_eip = self._create_eip()

        if not subnet_id:
            subnet_id = self.pub_sub_list[1].id

        self.nat = self.ec2_client.create_nat_gateway(AllocationId=nat_eip['AllocationId'],
                                                      SubnetId=subnet_id)

        self.logger.info("======== waiting for NAT Gateway ========")

        self.ec2_client.get_waiter('nat_gateway_available')\
            .wait(NatGatewayIds=[self.nat['NatGateway']['NatGatewayId']])

        self.logger.info("======== created NAT Gateway ========")

        return self

    def set_nat_rtb(self):
        nat_rtb = self.vpc.create_route_table()
        add_name_tag(nat_rtb, "NAT-RTB")

        nat_rtb.create_route(
            DestinationCidrBlock='0.0.0.0/0',
            NatGatewayId=self.nat['NatGateway']['NatGatewayId']
        )

        for subnet in self.pri_sub_list:
            nat_rtb.associate_with_subnet(SubnetId=subnet.id)

        return self

    def delete_nat_by_id(self, nat_id):
        try:
            self.ec2_client.delete_nat_gateway(NatGatewayId=nat_id)
            self.ec2_client.get_waiter('nat_gateway_available') \
                .wait(Filters=[
                {
                    'Name': 'state',
                    'Values': [
                        'deleted',
                    ]
                }, {
                    'Name': 'nat-gateway-id',
                    'Values': [
                        nat_id,
                    ]
                },
            ])
        except:
            pass

    def delete_vpc_by_id(self, vpc_id):
        self.ec2_client.delete_vpc(VpcId=vpc_id)

if __name__ == '__main__':
    vpc = DefaultVPC(region="us-east-1")
    vpc.create_VPC(cidr_block="10.0.0.0/16")
    vpc.create_sub()
    vpc.create_ig()
    vpc.set_ig_rtb()
    vpc.create_nat(subnet_id=vpc.pub_sub_list[1].id)
    vpc.set_nat_rtb()
