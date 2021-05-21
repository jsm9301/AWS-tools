## AWS tools
Build Automatically AWS Infrastructure using boto3
### Step 1
- Install aws CLI module ([Guide](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html))
### Step 2
- Configure your creadentials
```
$ aws configure
```
- Input your access key id, secret key and region
```
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1
```
### Step 3
- Install requirements package
```
pip install -r requirments.txt
```
### Step 4
- Check parameters in `build/default.py`
- ami must be checked(varies by region)
```
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
```
$ python default.py
```