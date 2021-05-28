import boto3


class ELB:
    """
    This class have create, register and delete features about Elastic Load Balancer

    init
        region: region
    """
    def __init__(self, region="us-east-2"):
        self.elb_client = boto3.client(service_name="elbv2", region_name=region)

    def create_elb(self, elb_name, subnet_list, sg_list, type="application", schema="internet-facing"):
        """
        Create ELB

        :param elb_name: elb name
        :param subnet_list: subnet id list to install(alb: More than one required)
        :param sg_list: security group id list to mapping
        :param type: elb type(application|network|gateway)
        :param schema: elb schema(internet-facing|internal)
        :return: load balancer informations(dict)
        """
        return self.elb_client.create_load_balancer(Name=elb_name,
                                                    Subnets=subnet_list,
                                                    SecurityGroups=sg_list,
                                                    Type=type,
                                                    Scheme=schema)

    def create_tgr(self, tgr_name, vpc_id, protocol="HTTP", port=80):
        """
        Create target group

        :param tgr_name: target group name
        :param vpc_id: vpc id
        :param protocol: the protocol to use for routing traffic to the targets
        :param port: the port to use for routing to the target
        :return: target group informations(dict)
        """
        return self.elb_client.create_target_group(Name=tgr_name,
                                                   Protocol=protocol,
                                                   Port=port,
                                                   VpcId=vpc_id)

    def register_targets(self, targets, tgr_arn):
        """
        Register target(instance) to target group

        :param targets: target instance id list
        :param tgr_arn: load balancer arn
        :return: register metadata(unused)
        """
        targets_list = [dict(Id=target) for target in targets]

        return self.elb_client.register_targets(TargetGroupArn=tgr_arn, Targets=targets_list)

    def create_listener(self, elb_arn, tgr_arn, protocol="HTTP", port=80):
        """
        Create listener to map with elb

        :param elb_arn: elb arn
        :param tgr_arn: target group arn
        :param protocol: the protocol for connections from clients to the load balancer
        :param port: the port on which the load balancer is listening
        :return: listener informations(dict)
        """
        return self.elb_client.create_listener(LoadBalancerArn=elb_arn,
                                               Protocol=protocol,
                                               Port=port,
                                               DefaultActions=[{'Type': 'forward',
                                                                'TargetGroupArn': tgr_arn}])

    def delete_elb_by_arn(self, elb_arn):
        """
        Delete elb by elb arn

        :param elb_arn: elb arn
        :return: None
        """
        self.elb_client.delete_load_balancer(LoadBalancerArn=elb_arn)

    def delete_tgr_by_arn(self, tgr_arn):
        """
        delete target group by target group arn

        :param tgr_arn: target group arn
        :return: None
        """
        self.elb_client.delete_target_group(TargetGroupArn=tgr_arn)


if __name__ == '__main__':
    elb = ELB(region="us-east-1")

    ### create ELB
    elb_response = elb.create_elb(elb_name="TEST-ALB",
                   subnet_list=["", ""],
                   sg_list=[""])
    elb_arn = elb_response['LoadBalancers'][0]['LoadBalancerArn']

    ### create target group
    tgr_response = elb.create_tgr(tgr_name="TEST-TGR",
                                  vpc_id="")
    tgr_arn = tgr_response['TargetGroups'][0]['TargetGroupArn']

    ### register targets to target group
    elb.register_targets(targets=["", ""], tgr_arn=tgr_arn)

    ### register target group to elb
    elb.create_listener(elb_arn=elb_arn, tgr_arn=tgr_arn)

    print("DNS is : {}".format(elb_response["LoadBalancers"][0]["DNSName"]))