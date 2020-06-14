from sqlalchemy import Boolean, Column, Float, String, Unicode, Time
from models.db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    nick = Column(String)
    is_admin = Column(Boolean, default=False)
    is_use_server = Column(Boolean, default=False)
    ssh_pub_key = Column(Unicode)
    serv_ip = Column(String)
    serv_id = Column(String)
    cpu_usage = Column(Float)
    gpu_usage = Column(Float)
    cpu_temp = Column(Float)
    gpu_temp = Column(Float)
    ram_usage = Column(Float)
    up_time = Column(Time)
    idle_time = Column(Time)
    
    class Config:
        orm_mode = True