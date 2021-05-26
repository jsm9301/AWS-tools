import logging
from model.ec2 import DefaultEc2
from model.vpc import DefaultVPC
from model.elb import ELB


class VPCCleaner:
    def __init__(self, vpc_id, region="us-east-1"):
        self.logger = logging.getLogger("logger")
        self.logger.setLevel(logging.INFO)

        stream_hander = logging.StreamHandler()
        self.logger.addHandler(stream_hander)

        self.d_vpc = DefaultVPC(region=region)
        self.d_ec2 = DefaultEc2(vpc_id=vpc_id, region=region)
        self.d_elb = ELB(region=region)
        self.vpc_id = vpc_id
        self.vpc = self.d_ec2.vpc

    def delete_all_elb(self):
        response = self.d_elb.elb_client.describe_load_balancers()
        for lb in response.get("LoadBalancers"):
            self.d_elb.delete_elb_by_arn(lb.get("LoadBalancerArn"))

            self.logger.info("======== Deleted Load Balancer : {} ========".format(lb.get("LoadBalancerName")))

        return self

    def delete_all_tgr(self):
        response = self.d_elb.elb_client.describe_target_groups()
        for tgr in response.get("TargetGroups"):
            self.d_elb.delete_tgr_by_arn(tgr.get("TargetGroupArn"))

            self.logger.info("======== Deleted Target Group : {} ========".format(tgr.get("TargetGroupName")))

        return self

    def delete_all_ec2(self):
        instance_ids = []
        response = self.d_ec2.ec2_client.describe_instances()
        for reservation in response.get("Reservations"):
            for instance in reservation.get("Instances"):
                instance_ids.append(instance.get("InstanceId"))

        self.d_ec2.delete_ec2_by_ids(instance_ids)

        self.logger.info("======== Deleted all EC2 ========")

        return self

    def delete_all_key_pair(self):
        response = self.d_ec2.ec2_client.describe_key_pairs()
        for key in response.get("KeyPairs"):
            self.d_ec2.delete_key_pair_by_name(key.get("KeyName"))

        self.logger.info("======== Deleted all key pair ========")

        return self

    def delete_all_sg(self):
        response = self.d_ec2.ec2_client.describe_security_groups()
        for group in response.get("SecurityGroups"):
            if group.get("GroupName") != "default":
                self.d_ec2.delete_sg_by_id(group.get("GroupId"))

        return self

    def delete_all_nat(self):
        response = self.d_vpc.ec2_client.describe_nat_gateways()
        for nat in response.get("NatGateways"):
            print(nat.get("NatGatewayId"))
            self.d_vpc.delete_nat_by_id(nat.get("NatGatewayId"))

            self.logger.info("======== Deleted NAT Gateway : {} ========".format(nat.get("NatGatewayId")))

        return self

    def release_all_eip(self):
        response = self.d_ec2.ec2_client.describe_addresses()
        for eip in response.get("Addresses"):
            self.d_ec2.release_eip_by_id(eip.get("AllocationId"))

        return self

    def delete_vpc(self):
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
    region = ""
    vpc_id = ""

    VPCCleaner(vpc_id=vpc_id, region=region) \
        .delete_all_elb() \
        .delete_all_ec2() \
        .delete_all_tgr() \
        .delete_all_key_pair() \
        .delete_all_nat() \
        .release_all_eip() \
        .delete_all_sg() \
        .delete_vpc()
