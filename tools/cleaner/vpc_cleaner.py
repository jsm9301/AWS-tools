from model.ec2 import DefaultEc2
from model.vpc import DefaultVPC
from model.elb import ELB
from util.decorators import *


class VPCCleaner:
    """
    This class have delete all vpc resources features

    Init
        vpc_id: vpc id to delete
        region: region
    """
    def __init__(self, vpc_id, region="us-east-1"):
        self.d_vpc = DefaultVPC(region=region)
        self.d_ec2 = DefaultEc2(vpc_id=vpc_id, region=region)
        self.d_elb = ELB(region=region)
        self.vpc_id = vpc_id
        self.vpc = self.d_ec2.vpc

    @Printer(post="Deleted all Load Balancers")
    def delete_all_elb(self):
        """Delete all elb"""
        response = self.d_elb.elb_client.describe_load_balancers()
        for lb in response.get("LoadBalancers"):
            self.d_elb.delete_elb_by_arn(lb.get("LoadBalancerArn"))

        return self

    @Printer(post="Deleted all Target Groups")
    def delete_all_tgr(self):
        """Delete all target group on elb"""
        response = self.d_elb.elb_client.describe_target_groups()
        for tgr in response.get("TargetGroups"):
            self.d_elb.delete_tgr_by_arn(tgr.get("TargetGroupArn"))

        return self

    @Printer(post="Deleted all EC2")
    def delete_all_ec2(self):
        """Terminate all EC2"""
        instance_ids = []
        response = self.d_ec2.ec2_client.describe_instances()
        for reservation in response.get("Reservations"):
            for instance in reservation.get("Instances"):
                instance_ids.append(instance.get("InstanceId"))

        self.d_ec2.delete_ec2_by_ids(instance_ids)

        return self

    @Printer(post="Deleted all key pairs")
    def delete_all_key_pair(self):
        """Delete all key pair"""
        response = self.d_ec2.ec2_client.describe_key_pairs()
        for key in response.get("KeyPairs"):
            self.d_ec2.delete_key_pair_by_name(key.get("KeyName"))

        return self

    @Printer(post="Deleted all Security Groups")
    def delete_all_sg(self):
        """Delete all security group"""
        response = self.d_ec2.ec2_client.describe_security_groups()
        for group in response.get("SecurityGroups"):
            if group.get("GroupName") != "default":
                self.d_ec2.delete_sg_by_id(group.get("GroupId"))

        return self

    @Printer(post="Deleted all NAT Gateway")
    def delete_all_nat(self):
        """Delete all NAT Gateway"""
        response = self.d_vpc.ec2_client.describe_nat_gateways()
        for nat in response.get("NatGateways"):
            self.d_vpc.delete_nat_by_id(nat.get("NatGatewayId"))

        return self

    @Printer(post="Release all EIP")
    def release_all_eip(self):
        """Release all EIP"""
        response = self.d_ec2.ec2_client.describe_addresses()
        for eip in response.get("Addresses"):
            self.d_ec2.release_eip_by_id(eip.get("AllocationId"))

        return self

    @Printer(post="Deleted VPC")
    def delete_vpc(self):
        """Delete resources(subnets, routing table, vpc) on VPC"""
        for gw in self.vpc.internet_gateways.all():
            self.vpc.detach_internet_gateway(InternetGatewayId=gw.id)
            gw.delete()

        for rt in self.vpc.route_tables.all():
            for rta in rt.associations:
                if not rta.main:
                    rta.delete()

            for r in rt.routes:
                try:
                    r.delete()
                except:
                    pass

            try:
                rt.delete()
            except:
                pass

        for subnet in self.vpc.subnets.all():
            for interface in subnet.network_interfaces.all():
                interface.delete()
            subnet.delete()

        self.d_vpc.delete_vpc_by_id(self.vpc_id)

        return self


if __name__ == '__main__':
    ### Params
    region = "ap-northeast-2"
    vpc_id = "vpc-0d6841a3914124596"

    VPCCleaner(vpc_id=vpc_id, region=region) \
        .delete_all_elb() \
        .delete_all_ec2() \
        .delete_all_tgr() \
        .delete_all_key_pair() \
        .delete_all_nat() \
        .release_all_eip() \
        .delete_all_sg() \
        .delete_vpc()
