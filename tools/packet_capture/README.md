## Packet Capture on AWS EC2
You can capture the packets on any EC2(Public or Private EC2)
- Check parameters in `tools/packet_capture/packet_capture.py`
```python
region = "{us-east-1}"
bastion_ip = "{enter your bastion IP(public ip address)}"
target_ip = "{enter target IP}"
pem_key_path = "{enter your private pem key}"

pcap_file_name = "{enter packet log file name}"
local_pcap_path = "{enter the pcap save path / default: ./}"
```
### Parameters example
- If public EC2
```python
bastion_ip = None
target_ip = "{enter target IP}"
```
- If private EC2
```python
bastion_ip = "{enter your bastion IP(public ip address)}"
target_ip = "{enter target IP}"
```
### Running
```shell script
$ python packet_capture.py
```
```
SSH into the instance: 127.0.0.1
ssh connected
scp success
packet capture is running...
Do you want to quit and save?(y/n) : 
```
- If you want to stop capturing and save the file enter the `y`
- Then you can get `.pcap` file on your local PC(default path: `./`)
```
SSH into the instance: 127.0.0.1
ssh connected
scp success
packet capture is running...
Do you want to quit and save?(y/n) : y
bye
```