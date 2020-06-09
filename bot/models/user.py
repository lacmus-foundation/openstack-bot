from pydantic import BaseModel
from datetime import time

class User(BaseModel):
    id: str
    nick: str
    is_use_server: bool = False
    ssh_pub_key: str = None
    serv_ip: str = None
    cpu_usage: float = None
    gpu_usage: float = None
    cpu_temp: float = None
    gpu_temp: float = None
    ram_usage: float = None
    up_time: time = None
    idle_time: time = None