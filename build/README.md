## Default infrastructure on AWS
- Check parameters in `build/default.py`
- ami must be checked(varies by region)
```python
### VPC
region = "us-east-1"
vpc_name = "TEST-VPC"
vpc_cidr = "10.0.0.0/16"
pub_sub_num = 2
pri_sub_num = 2

### EC2
bastion_name = "Bastion"
pem_key_name = "TEST-PEM"
ami = "ami-0d5eff06f840b45e9"
web_inbound_list = [{"cidr": "0.0.0.0/0", "protocol": "tcp", "f_port": 80, "t_port": 80},
                {"cidr": "10.0.0.0/16", "protocol": "tcp", "f_port": 22, "t_port": 22}]
user_name = "ec2-user"
pem_key_path = "./TEST-PEM.pem"

### alb
alb_name = "TEST-ALB"
tgr_name = "TEST-TGR"
```
- Run
```shell script
$ python default.py
```