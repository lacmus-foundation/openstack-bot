from sqlalchemy.orm import Session
from models import user, db_user

async def create_user(db: Session, user: user.User, is_admin: bool = False):
    db_usr = db_user.User(
        id=user.id,
        nick=user.nick,
        is_admin=is_admin,
        is_use_server=user.is_use_server,
        ssh_pub_key=user.ssh_pub_key,
        serv_ip=user.serv_ip,
        cpu_usage=user.cpu_usage,
        gpu_usage=user.gpu_usage,
        cpu_temp=user.cpu_temp,
        gpu_temp=user.gpu_temp,
        ram_usage=user.ram_usage,
        up_time=user.up_time,
        idle_time=user.idle_time
    )
    db.add(db_usr)
    db.commit()
    db.refresh(db_usr)
    return db_usr

async def get_user(db: Session, id: str):
    return db.query(db_user.User).filter(db_user.User.id == id).first()

async def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(db_user.User).offset(skip).limit(limit).all()

async def update_user_info(db: Session, user: user.User):
    rows = db.query(db_user.User).filter(db_user.User.id == user.id).update(
        {
            db_user.User.is_use_server: user.is_use_server,
            db_user.User.ssh_pub_key:   user.ssh_pub_key,
            db_user.User.serv_ip:       user.serv_ip,
            db_user.User.cpu_usage:     user.cpu_usage,
            db_user.User.gpu_usage:     user.gpu_usage,
            db_user.User.cpu_temp:      user.cpu_temp,
            db_user.User.gpu_temp:      user.gpu_temp,
            db_user.User.ram_usage:     user.ram_usage,
            db_user.User.up_time:       user.up_time,
            db_user.User.idle_time:     user.idle_time
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