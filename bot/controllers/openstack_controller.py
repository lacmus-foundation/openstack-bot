from sshpubkeys import SSHKey
from models import user
import openstack 

async def create_keypair(usr: user.User):
    try:
        conn = openstack.connect()
        conn.create_keypair(name=f'{usr.id}_{usr.nick}', public_key=usr.ssh_pub_key)
        conn.close()
        return True
    except:
        if conn != None:
            conn.close()
        return False

async def create_server(usr: user.User, flavor: str, image: str, network: str):
    try:
        conn = openstack.connect()
        server = conn.create_server(name=f'{usr.id}_{usr.nick}', image=image, flavor=flavor, network=network, key_name=f'{usr.id}_{usr.nick}')
        conn.close()
        return server['id']
    except:
        if conn != None:
            conn.close()
        return None

async def delete_server(server_id: str):
    try:
        conn = openstack.connect()
        is_deleted = conn.delete_server(name_or_id=server_id, wait=True)
        conn.close()
        return is_deleted
    except:
        if conn != None:
            conn.close()
        return False

async def get_server_info(server_id: str):
    try:
        conn = openstack.connect()
        server = conn.get_server_by_id(server_id)
        conn.close()
        return { 'name': server['name'], 'ip': server['accessIPv4'], 'status': server['status'] }
    except:
        if conn != None:
            conn.close()
        return None

async def validate_ssh(ssh_pub: str):
    ssh = SSHKey(ssh_pub)
    try:
        ssh.parse()
        return True
    except:
        return False