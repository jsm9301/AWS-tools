## AWS tools
- Build Automatically AWS Infrastructure using boto3
  - `build/default.py`
- Packet capture features on AWS EC2
  - `tools/packet_capture.py`
## Get Set
- Need to set before use these tools
### Step 1
- Install aws CLI module ([Guide](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html))
### Step 2
- Configure your creadentials
```shell script
$ aws configure
```
- Input your access key id, secret key and region
```shell script
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1
```
### Step 3
- Install requirements package
```shell script
pip install -r requirments.txt
```