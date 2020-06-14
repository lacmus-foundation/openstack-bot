from sqlalchemy.orm import Session
from models import user, db_user

async def create_user(db: Session, usr: user.User, is_admin: bool = False):
    db_usr = db_user.User(
        id=usr.id,
        nick=usr.nick,
        is_admin=is_admin,
        is_use_server=usr.is_use_server,
        ssh_pub_key=usr.ssh_pub_key,
        serv_ip=usr.serv_ip,
        serv_id=usr.serv_id,
        cpu_usage=usr.cpu_usage,
        gpu_usage=usr.gpu_usage,
        cpu_temp=usr.cpu_temp,
        gpu_temp=usr.gpu_temp,
        ram_usage=usr.ram_usage,
        up_time=usr.up_time,
        idle_time=usr.idle_time
    )
    db.add(db_usr)
    db.commit()
    db.refresh(db_usr)
    return db_usr

async def get_user(db: Session, id: str):
    return db.query(db_user.User).filter(db_user.User.id == id).first()

async def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(db_user.User).offset(skip).limit(limit).all()

async def update_user_info(db: Session, usr: user.User):
    rows = db.query(db_user.User).filter(db_user.User.id == usr.id).update(
        {
            db_user.User.is_use_server: usr.is_use_server,
            db_user.User.ssh_pub_key:   usr.ssh_pub_key,
            db_user.User.serv_ip:       usr.serv_ip,
            db_user.User.serv_id:       usr.serv_id,
            db_user.User.cpu_usage:     usr.cpu_usage,
            db_user.User.gpu_usage:     usr.gpu_usage,
            db_user.User.cpu_temp:      usr.cpu_temp,
            db_user.User.gpu_temp:      usr.gpu_temp,
            db_user.User.ram_usage:     usr.ram_usage,
            db_user.User.up_time:       usr.up_time,
            db_user.User.idle_time:     usr.idle_time
        })
    db.commit()
    return rows

async def update_user_admin_status(db: Session, id: str, is_admin: bool):
    rows = db.query(db_user.User).filter(db_user.User.id == id).update(
        {
            db_user.User.is_admin: is_admin
        })
    db.commit()
    return rows

async def remove_user(db: Session, id: str):
    rows = db.query(db_user.User).filter(db_user.User.id == id).delete()
    db.commit()
    return rows

async def db_user2user(usr: db_user.User):
    if usr == None:
        return None

    return user.User(
        id=usr.id,
        nick=usr.nick,
        is_use_server=usr.is_use_server,
        ssh_pub_key=usr.ssh_pub_key,
        serv_ip=usr.serv_ip,
        serv_id=usr.serv_id,
        cpu_usage=usr.cpu_usage,
        gpu_usage=usr.gpu_usage,
        cpu_temp=usr.cpu_temp,
        gpu_temp=usr.gpu_temp,
        ram_usage=usr.ram_usage,
        up_time=usr.up_time,
        idle_time=usr.idle_time
    )