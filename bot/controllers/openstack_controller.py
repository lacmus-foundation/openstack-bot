# import openstack...
from sshpubkeys import SSHKey

async def create_keypair(user: str, ssh_pub: str):
    pass

async def create_server(server_id: str):
    pass

async def stop_server(server_id: str):
    pass

async def delete_server(server_id: str):
    pass

async def get_server_status(server_id: str):
    pass

async def validate_ssh(ssh_pub: str):
    ssh = SSHKey(ssh_pub)
    try:
        ssh.parse()
        return True
    except:
        return False