from fastapi import FastAPI, HTTPException, Request, Response, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from models.db import SessionLocal, engine
from models import user, db_user
from controllers import user_controller, openstack_controller
from time import sleep
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
        is_token_valid = r_from['token'] == '7t5eol79LFxKNCQ9Eaa6Fqnt'
        #os.environ['SLACK_VERIFICATION_TOKEN']
    except:
        is_token_valid = False
    return is_token_valid

def server_status_report(server_id: str, respone_url: str, usr: user.User, db: Session = Depends(get_db)):
    count = 0
    while count < 120:
        info = await openstack_controller.get_server_info(server_id=server_id)
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
            break
    data = { 
                'response_type': 'in_thread',
                'type': 'mrkdwn', 
                'text': 'Error: creating server timeout.'
            }
            requests.post(response_url, json=data)
            break

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
- `/create-server [SERVER_TYPE]` - _create a new server for currnt user_
  - _*SERVER_TYPE:*_
{server_types_msg}- `/stop-server` - _stop andlete server_

_If you want de a different server configuration - write to administrators:_ *@gosha20777*, *@ei-grad*
'''
        }

@app.post('/api/v1/command/set-ssh')
async def set_ssh_command(req: Request, db: Session = Depends(get_db)):
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

    # todo: update or create keypair in openstack

    # update user key
    usr.ssh_pub_key = r_from['text']
    rows = await user_controller.update_user_info(db=db, usr=usr)
    if rows < 0:
        return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: cant update info about \nuser id: *{usr.id}*\nname: *{usr.nick}*.' 
            }

    return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Set ssh public key for \nuser id: *{usr.id}*\nname: *{usr.nick}*.\n\n`{usr.ssh_pub_key}`' 
            }

@app.post('/api/v1/command/create-server')
async def create_server_command(req: Request, db: Session = Depends(get_db)):
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
    server_id = await openstack_controller.create_server(user=usr, 
                                                flavor=server_params['flavor'], 
                                                image=server_params['image'], 
                                                network=server_params['network'])
    if server_id == None:
        return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: cant finish operation for user \nid: *{usr.id}*\nname: *{usr.nick}*\nopenstack eror.' 
            }
    usr.serv_id = server_id
    usr.is_use_server = True
    rows = await user_controller.update_user_info(db=db, usr=usr)
    if rows < 0:
        return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: cant update info about \nuser id: *{usr.id}*\nname: *{usr.nick}*.' 
            }
    respone_url = r_from['response_url']
    background_tasks.add_task(server_status_report, server_id, respone_url, usr)

    return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': 
f'''Start creating server _{server_type}_ for user 
id: *{usr.id}*
name: *{usr.nick}*.
'''
            }

@app.post('/api/v1/command/stop-server')
async def stop_server_command(req: Request, db: Session = Depends(get_db)):
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
    
    # todo: update or stop and delete openstack server
    if not await openstack_controller.delete_server(server_id=usr.serv_id):
        return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: cant delete server \nserver id: *{usr.serv_id}*\nserver ip: *{usr.serv_ip}*.' 
            }

    usr.is_use_server = False
    usr.serv_ip = None
    usr.serv_id = None
    rows = await user_controller.update_user_info(db=db, usr=usr)
    if rows < 0:
        return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': f'Error: cant update info about \nuser id: *{usr.id}*\nname: *{usr.nick}*.' 
            }

    return { 
            'response_type': 'in_thread',
            'type': 'mrkdwn', 
            'text': 
f'''Stop and delete server user 
id: *{usr.id}*
name: *{usr.nick}*.
'''
            }