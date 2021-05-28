from util.ssh import SSHConnector
import atexit


class RemotePCAP:
    """
    This class have packet capture features
    - You can get packet capture logs on EC2 that have public ip
    - Also you can get packet capture logs on private EC2 server
        - using ssh tunneling, scp

    Init
        region: region
        target_ip: target ip address to packet capturing
        pem_key_path: key pair path to connecting
        pcap_file_name: packet capture log file name
        p_kill_script: script file to kill tcpdump process
        eth: ethernet interface to packet capturing
        bastion_ip: bastion ip address to connecting private server(default: None)
        user_name: user name on server(default: ec2-user)
        local_pcap_path: local path to save packet capture logs
    """
    def __init__(self, region, target_ip, pem_key_path, pcap_file_name,
                 p_kill_script, eth="eth0", bastion_ip=None, user_name="ec2-user",
                 local_pcap_path="./"):
        self.ssh_connector = SSHConnector(region=region)
        self.target_ip = target_ip
        self.pem_key_path = pem_key_path
        self.pcap_file_name = pcap_file_name
        self.p_kill_script = p_kill_script
        self.eth = eth
        self.bastion_ip = bastion_ip
        self.user_name = user_name
        self.local_pcap_path = local_pcap_path

        self.remote_kill_script = "/home/ec2-user/kill_tcpdump.sh"

        self.tunnel = None
        if self.bastion_ip is None:
            self.ssh_connector.connect_ssh(ip_address=self.target_ip, pem_key_path=self.pem_key_path)
        else:
            self.tunnel = self.ssh_connector.tunneling(host=self.bastion_ip,
                                         host_port=22,
                                         user=self.user_name,
                                         pem_key_path=self.pem_key_path,
                                         remote_ip=self.target_ip,
                                         remote_port=22)
            self.tunnel.start()
            self.ssh_connector.connect_ssh(ip_address="127.0.0.1", port=10022, pem_key_path=self.pem_key_path)

    def install_tcpdump(self):
        """Install tcpdump package on server"""
        self.ssh_connector.command_delivery(commands="sudo yum install tcpdump -y")

    def start(self):
        """Start packet capture on server"""
        self.ssh_connector.send_file(local_path=self.p_kill_script, remote_path=self.remote_kill_script)

        self.ssh_connector.command_delivery(commands="sudo nohup tcpdump -i {} -w {}".format(self.eth, self.pcap_file_name), is_buf_over=True)

    def stop(self):
        """Stop packet capture process and save logs on local PC"""
        # kill tcpdump process
        self.ssh_connector.command_delivery(commands=". {}".format(self.remote_kill_script))

        # get pcap file
        self.ssh_connector.get_file(remote_path="/home/ec2-user/{}".format(self.pcap_file_name),
                                    local_path=self.local_pcap_path)

        self.ssh_connector.ssh.close()

        if self.tunnel:
            self.tunnel.stop()

if __name__ == '__main__':
    ### Params
    region = "{us-east-1}"
    bastion_ip = "{enter your bastion IP(public ip address)}"
    target_ip = "{enter target IP}"
    pem_key_path = "{enter your private pem key}"

    pcap_file_name = "{enter packet log file name}"
    local_pcap_path = "./"

    ### start packet capture
    r_pcap = RemotePCAP(region=region, target_ip=target_ip,
                        pem_key_path=pem_key_path, p_kill_script="../../scripts/kill_tcpdump.sh",
                        pcap_file_name=pcap_file_name, bastion_ip=bastion_ip, local_pcap_path=local_pcap_path)

    r_pcap.install_tcpdump()

    atexit.register(r_pcap.stop)
    r_pcap.start()

    answer = ""
    while True:
        if answer == "y":
            print("bye")
            break
        print("packet capture is running...")
        answer = input("Do you want to quit and save?(y/n) : ")