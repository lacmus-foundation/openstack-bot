from fastapi import FastAPI, HTTPException, Request, Response, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from models.db import SessionLocal, engine
from models import user, db_user
from controllers import user_controller, openstack_controller
from time import sleep
import config
import requests
import json


# init
db_user.Base.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def is_request_valid(req: Request):
    try:
        r_from = await req.form()
        print(r_from, flush=True)
        is_token_valid = r_from['token'] == config.token and r_from['channel_id'] == config.channel_id
    except:
        is_token_valid = False
        response_url = r_from['response_url']
        data = { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'''You must be a member of the Lacmus community (#proj_rescuer_la) in order to be able to receive GPUs for training.
You can find and join our project in the #ml4sg channel or write to *@gosha20777* to get more info.
Powered by https://immers.cloud''' 
            }
        requests.post(response_url, json=data)
    return is_token_valid

async def create_server(server_params: dict, usr: user.User, r_from: dict, db: Session):
    response_url = r_from['response_url']

    server_id = await openstack_controller.create_server(usr=usr, 
                                                flavor=server_params['flavor'], 
                                                image=server_params['image'], 
                                                network=server_params['network'])
    if server_id == None:
        response_url = r_from['response_url']
        data = { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: can\'t finish operation for user \nid: *{usr.id}*\nname: *{usr.nick}*\nopenstack eror.' 
            }
        requests.post(response_url, json=data)
        return

    usr.serv_id = server_id
    usr.is_use_server = True
    rows = await user_controller.update_user_info(db=db, usr=usr)
    if rows < 0:
        response_url = r_from['response_url']
        data = { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: cant update info about \nuser id: *{usr.id}*\nname: *{usr.nick}*.' 
            }
        requests.post(response_url, json=data)
        return

    response_url = r_from['response_url']
    
    count = 0
    data = {
            'response_type': 'in_thread',
            'type': 'mrkdwn',
            'text': f'Start creating server *{server_id}* for user\nid: *{usr.id}*\nname: *{usr.nick}*.'
    }
    requests.post(response_url, json=data)

    while count < 900:
        info = await openstack_controller.get_server_info(server_id=server_id)
        if count > 30 and count % 60 == 0:
            data = {
            'response_type': 'in_thread',
            'type': 'mrkdwn',
            'text': f'Creating server status: {info["status"]}.'
            }
            requests.post(response_url, json=data)

        if info['status'] == 'ACTIVE':
            usr.serv_id = info['id']
            usr.serv_ip = info['ip']
            
            rows = await user_controller.update_user_info(db=db, usr=usr)
            if rows < 0:
                data = { 
                    'response_type': 'in_thread',
                    'type': 'mrkdwn', 
                    'text': f'Error: cant update info about \nuser id: *{usr.id}*\nname: *{usr.nick}*.' 
                }
                requests.post(response_url, json=data)
                break

            data = { 
                'response_type': 'in_thread',
                'type': 'mrkdwn', 
                'text': f'''Setver is ready to use!
Server id: *{info['id']}*
Server ip: *{info['ip']}*
Server status: *{info['status']}*

Use command to connect:
```
$ ssh ubuntu@{info['ip']}
```
'''
            }
            requests.post(response_url, json=data)
            break

        if info['status'] == 'BUILD':
            count = count + 1
            sleep(1)
            continue

        data = { 
                'response_type': 'in_thread',
                'type': 'mrkdwn', 
                'text': f'''Error: creating server error
Server id: *{info['id']}*
Server ip: *{info['ip']}*
Server status: *{info['status']}*
'''
            }
        requests.post(response_url, json=data)
        return

    data = { 
                'response_type': 'in_thread',
                'type': 'mrkdwn', 
                'text': 'Error: creating server timeout.'
            }
    requests.post(response_url, json=data)

async def set_ssh_key(r_from: dict, usr: user.User, db: Session):
    # todo: update or create keypair in openstack
    usr.ssh_pub_key = r_from['text']
    if not await openstack_controller.create_keypair(usr=usr):
        response_url = r_from['response_url']
        data = { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: cant create openstack keypair for user\nid: *{usr.id}*\nname: *{usr.nick}*.' 
            }
        requests.post(response_url, json=data)
        return

    # update user key
    rows = await user_controller.update_user_info(db=db, usr=usr)
    if rows < 0:
        response_url = r_from['response_url']
        data = { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: cant update info about \nuser id: *{usr.id}*\nname: *{usr.nick}*.' 
            }
        requests.post(response_url, json=data)
        return

    response_url = r_from['response_url']
    data = { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Set ssh public key for \nuser id: *{usr.id}*\nname: *{usr.nick}*.\n\n`{usr.ssh_pub_key}`' 
            }
    requests.post(response_url, json=data)

async def delete_server(r_from: dict, usr: user.User, db: Session):
    # todo: update or stop and delete openstack server
    if not await openstack_controller.delete_server(server_id=usr.serv_id):
        response_url = r_from['response_url']
        data = { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: cant delete server \nserver id: *{usr.serv_id}*\nserver ip: *{usr.serv_ip}*.' 
            }
        requests.post(response_url, json=data)

    usr.is_use_server = False
    usr.serv_ip = None
    usr.serv_id = None
    rows = await user_controller.update_user_info(db=db, usr=usr)
    if rows < 0:
        response_url = r_from['response_url']
        data = { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: cant update info about \nuser id: *{usr.id}*\nname: *{usr.nick}*.' 
            }
        requests.post(response_url, json=data)
        return

    response_url = r_from['response_url']
    data = { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': 
f'''Stop and delete server for user 
id: *{usr.id}*
name: *{usr.nick}*.
'''
            }
    requests.post(response_url, json=data)
    return

@app.post('/api/v1/command/usage')
async def usage_command(req: Request):
    if not await is_request_valid(req):
        raise HTTPException(400, detail='invalid token')
    server_types = json.load(open('config.json', 'r'))
    server_types_msg = ""

    for server_type in server_types:
        server_types_msg = server_types_msg + f"    - `{server_type}` - {server_types[server_type]['description']}\n"

    return { 
        'response_type': 'in_thread',
        'type': 'mrkdwn',
        'text':
f'''
*Bot usage:*
- `/set-ssh-key [SSH_PUBLIC_KEY]` - _create or update keypair with your ssh key_
- `/create-server [SERVER_TYPE]` - _create a new server for current user_
  - _*SERVER_TYPE:*_
{server_types_msg}- `/stop-server` - _stop and dlete server_

_If you want a different server configuration - write to administrators:_ *@gosha20777*, *@ei-grad*
Powered by https://immers.cloud
'''
        }

@app.post('/api/v1/command/set-ssh')
async def set_ssh_command(req: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not await is_request_valid(req):
        raise HTTPException(400, detail='invalid token')
    r_from = await req.form()
    if not await openstack_controller.validate_ssh(r_from['text']):
        return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: invalid ssh-key: `{r_from["text"]}`.' 
            }

    db_usr = await user_controller.get_user(db=db, id=r_from['user_id'])
    usr = await user_controller.db_user2user(usr=db_usr)
    if usr == None:
        #create user
        usr = user.User(
            id=r_from['user_id'],
            nick=r_from['user_name']
        )
        db_usr = await user_controller.create_user(db=db, usr=usr)
    
    background_tasks.add_task(set_ssh_key, r_from=r_from, usr=usr, db=db)
    return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': 'Start working:-)' 
            }
    

@app.post('/api/v1/command/create-server')
async def create_server_command(req: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not await is_request_valid(req):
        raise HTTPException(400, detail='invalid token')
    r_from = await req.form()
    server_type = r_from['text']
    try:
        server_types = json.load(open('config.json', 'r'))
        server_params = server_types[server_type]
    except:
        return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: invalid SERVER_TYPE: {server_type}.\nSee `/usage` command for more info.' 
            }

    db_usr = await user_controller.get_user(db=db, id=r_from['user_id'])
    usr = await user_controller.db_user2user(usr=db_usr)
    if usr == None:
        return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'''Error: user with id: `{r_from["user_id"]}`, name: {r_from["user_name"]} have no registered ssh public key. Use `/set-ssh-key` command. \nSee `/usage` command for more info.'''
            }
    if usr.is_use_server:
        return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': 
f'''Error: user 
id: *{usr.id}*
name: *{usr.nick}*
already have server. 

- use command to connect via ssh:
```
$ ssh ubuntu@{usr.serv_ip}
```
- or stop your server using `/stop-server` connamd and create it again.
See `/usage` command for more info.
'''
            }

    # todo: update or create openstack server
    background_tasks.add_task(create_server, server_params, usr, r_from, db)
    return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': 'Start working:-)' 
            }

@app.post('/api/v1/command/stop-server')
async def stop_server_command(req: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not await is_request_valid(req):
        raise HTTPException(400, detail='invalid token')
    r_from = await req.form()

    db_usr = await user_controller.get_user(db=db, id=r_from['user_id'])
    usr = await user_controller.db_user2user(usr=db_usr)
    if usr == None:
        return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'''Error: user\nid: *{r_from["user_id"]}*,\nname: *{r_from["user_name"]}*\nhave no registered ssh public key. Use `/set-ssh-key` command. \nSee `/usage` command for more info.'''
            }
    if not usr.is_use_server:
        return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'''Error: user\nid: *{r_from["user_id"]}*,\nname: *{r_from["user_name"]}*\nhave no servers. Use `/create-server` command. \nSee `/usage` command for more info.'''
            }
    
    background_tasks.add_task(delete_server, r_from=r_from, usr=usr, db=db)
    return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': 'Start working:-)' 
            }

@app.post('/api/v1/monitoring')
async def stop_server_command():
    return
