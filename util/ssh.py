import logging
import boto3
from scp import SCPClient, SCPException
import paramiko
import time
import sshtunnel
from util.utils import *


class SSHConnector:
    def __init__(self, region="us-east-2"):
        self.logger = logging.getLogger("logger")
        self.logger.setLevel(logging.INFO)

        stream_hander = logging.StreamHandler()
        self.logger.addHandler(stream_hander)

        self.ec2 = boto3.resource("ec2", region_name=region)

    def _ssh_connect_with_retry(self, ssh, ip_address, retries, pem_key_path, port):
        if retries > 3:
            return False
        pri_key = paramiko.RSAKey.from_private_key_file(pem_key_path)
        interval = 5
        try:
            retries += 1
            self.logger.info('SSH into the instance: {}'.format(ip_address))
            self.ssh.connect(hostname=ip_address, port=port,
                        username='ec2-user', pkey=pri_key)
            return True
        except Exception as e:
            self.logger.error(e)

            time.sleep(interval)

            self.logger.info('Retrying SSH connection to {}'.format(ip_address))
            self._ssh_connect_with_retry(self.ssh, ip_address, retries, pem_key_path, port)

    def connect_ssh(self, instance_id=None, ip_address=None, pem_key_path="./TEST-PEM.pem", port=22):
        if not ip_address:
            ip_address = get_ip(self.ec2, instance_id, True)

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self._ssh_connect_with_retry(self.ssh, ip_address, 0, pem_key_path, port):
            self.logger.info("ssh connected")
        else:
            self.logger.info("ssh failed")

    def send_file(self, local_path="./TEST-PEM.pem", remote_path="/home/ec2-user/TEST-PEM.pem"):
        try:
            with SCPClient(self.ssh.get_transport()) as scp:
                scp.put(local_path, remote_path, preserve_times=True)
                self.logger.info("scp success")
        except SCPException:
            self.logger.error("scp failed")

    def get_file(self, remote_path, local_path):
        try:
            with SCPClient(self.ssh.get_transport()) as scp:
                scp.get(remote_path, local_path)
        except SCPException:
            self.logger.error("scp failed")

    def command_delivery(self, commands, is_buf_over=False):
        stdin, stdout, stderr = self.ssh.exec_command(commands)

        if not is_buf_over:
            self.logger.info(stdout.read())
            self.logger.info(stderr.read())

    def tunneling(self, host, host_port, pem_key_path,
                  remote_ip, remote_port, user="ec2-user",
                  local_ip="127.0.0.1", local_port=10022):

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

