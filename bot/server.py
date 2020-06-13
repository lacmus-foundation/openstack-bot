from fastapi import FastAPI, HTTPException, Request, Response, Depends
from sqlalchemy.orm import Session
from models.db import SessionLocal, engine
from models import user, db_user
from controllers import user_controller, openstack_controller
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
    usr.is_use_server = True
    usr.serv_ip = "1.1.1.1"
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
f'''Created server _{server_type}_ for user 
id: *{usr.id}*
name: *{usr.nick}*.

Use command to connect via ssh:
```
$ ssh ubuntu@{usr.serv_ip}
```
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
    usr.is_use_server = False
    usr.serv_ip = None
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