#########
# Utils
#########

def add_name_tag(obj, name):
    """
    add name tag for `boto3.resource` object

    :param obj: target object
    :param name: name(string)
    :return: None
    """
    obj.create_tags(Tags=[{"Key": "Name", "Value": name}])

def add_name_tag_ec2(ec2_client, instance_id, name):
    """
    add name tag for `boto3.client('ec2')` object

    :param ec2_client: target ec2 client object
    :param instance_id: target instance id
    :param name: name(string)
    :return: None
    """
    ec2_client.create_tags(
        Resources=
        [instance_id],
        Tags=[
            {
                'Key': 'Name',
                'Value': name,
            }
        ]
    )

def get_ip(ec2, instance_id, is_pub):
    """
    get ec2 instance ip address

    :param ec2: target ec2 resource object
    :param instance_id: target ec2 instance id
    :param is_pub: True: public ip address, False: private ip address
    :return: public or private ip address
    """
    instance = ec2.Instance(id=instance_id)
    instance.wait_until_running()
    current_instance = list(ec2.instances.filter(InstanceIds=[instance_id]))

    if is_pub:
        return current_instance[0].public_ip_address
    return current_instance[0].private_ip_address