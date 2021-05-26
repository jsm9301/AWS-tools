import boto3


class ELB:
    def __init__(self, region="us-east-2"):
        self.elb_client = boto3.client(service_name="elbv2", region_name=region)

    def create_elb(self, elb_name, subnet_list, sg_list, type="application", schema="internet-facing"):
        return self.elb_client.create_load_balancer(Name=elb_name,
                                                    Subnets=subnet_list,
                                                    SecurityGroups=sg_list,
                                                    Type=type,
                                                    Scheme=schema)

    def create_tgr(self, tgr_name, vpc_id, protocol="HTTP", port=80):
        return self.elb_client.create_target_group(Name=tgr_name,
                                                   Protocol=protocol,
                                                   Port=port,
                                                   VpcId=vpc_id)

    def register_targets(self, targets, tgr_arn):
        targets_list = [dict(Id=target) for target in targets]

        return self.elb_client.register_targets(TargetGroupArn=tgr_arn, Targets=targets_list)

    def create_listener(self, elb_arn, tgr_arn, protocol="HTTP", port=80):
        return self.elb_client.create_listener(LoadBalancerArn=elb_arn,
                                               Protocol=protocol,
                                               Port=port,
                                               DefaultActions=[{'Type': 'forward',
                                                                'TargetGroupArn': tgr_arn}])

    def delete_elb_by_arn(self, elb_arn):
        self.elb_client.delete_load_balancer(LoadBalancerArn=elb_arn)

    def delete_tgr_by_arn(self, tgr_arn):
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