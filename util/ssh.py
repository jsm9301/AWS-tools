import boto3
from scp import SCPClient, SCPException
import paramiko
import time
import sshtunnel
from util.utils import *


class SSHConnector:
    """
    This class have ssh connect, ssh tunneling, scp features to remote server

    Init
       region: region
    """
    def __init__(self, region="us-east-2"):
        self.ec2 = boto3.resource("ec2", region_name=region)

    def _ssh_connect_with_retry(self, ssh, ip_address, retries, pem_key_path, port):
        """Try ssh connect recursive if fail(3 times)"""
        if retries > 3:
            return False
        pri_key = paramiko.RSAKey.from_private_key_file(pem_key_path)
        interval = 5
        try:
            retries += 1
            self.ssh.connect(hostname=ip_address, port=port,
                        username='ec2-user', pkey=pri_key)
            return True
        except Exception:
            time.sleep(interval)

            self._ssh_connect_with_retry(self.ssh, ip_address, retries, pem_key_path, port)

    def connect_ssh(self, instance_id=None, ip_address=None, pem_key_path="./TEST-PEM.pem", port=22):
        """Connect ssh and get session"""
        if not ip_address:
            ip_address = get_ip(self.ec2, instance_id, True)

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self._ssh_connect_with_retry(self.ssh, ip_address, 0, pem_key_path, port):
            print("ssh connected")
        else:
            print("ssh failed")

    def send_file(self, local_path="./TEST-PEM.pem", remote_path="/home/ec2-user/TEST-PEM.pem"):
        """Send file using scp"""
        try:
            with SCPClient(self.ssh.get_transport()) as scp:
                scp.put(local_path, remote_path, preserve_times=True)
        except SCPException:
            pass

    def get_file(self, remote_path, local_path):
        """Get file using scp"""
        try:
            with SCPClient(self.ssh.get_transport()) as scp:
                scp.get(remote_path, local_path)
        except SCPException:
            pass

    def command_delivery(self, commands, is_buf_over=False):
        """Delivery command to remote server"""
        stdin, stdout, stderr = self.ssh.exec_command(commands)

        if not is_buf_over:
            print(stdout.read())
            print(stderr.read())

    def tunneling(self, host, host_port, pem_key_path,
                  remote_ip, remote_port, user="ec2-user",
                  local_ip="127.0.0.1", local_port=10022):
        """ssh tunneling to private server that don't have public ip address"""

        return sshtunnel.open_tunnel(
            (host, host_port),
            ssh_username=user,
            ssh_pkey=pem_key_path,
            remote_bind_address=(remote_ip, remote_port),
            local_bind_address=(local_ip, local_port)
    )


if __name__ == '__main__':
    wi = SSHConnector(region="us-east-1")

    # ### connect bastion
    # wi.connect_ssh(instance_id="", pem_key_path="../build/TEST-PEM.pem")
    #
    # ### send pem key to bastion
    # wi.send_pem_key_with_id(pem_key_path="../build/TEST-PEM.pem")

    ### tunneling web server and install nginx

    bastion_id = ""
    instance_list = ["", ""]
    user = ""
    pem_key_path = ""
    print(get_ip(wi.ec2, bastion_id, True))
    print(get_ip(wi.ec2, instance_list[0], False))
    for instance_id in instance_list:
        with wi.tunneling(host=get_ip(wi.ec2, bastion_id, True),
                     host_port=22,
                     user=user,
                     pem_key_path=pem_key_path,
                     remote_ip=get_ip(wi.ec2, instance_id, False),
                     remote_port=22) as tunnel:

            tunnel.start()
            wi.connect_ssh(ip_address="127.0.0.1", port=10022, pem_key_path=pem_key_path)
            wi.command_delivery("sudo amazon-linux-extras install nginx1 -y && sudo service nginx start")
            tunnel.stop()

