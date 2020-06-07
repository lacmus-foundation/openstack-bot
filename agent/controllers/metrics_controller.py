import socket
import psutil
import GPUtil
from pyspectator.computer import Computer
from pyspectator.processor import Cpu
from datetime import datetime, timedelta

def get_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except Exception as e:
        log_error(Exception(f"Cont get ip: {str(e)}"))
        return None

def get_cpu_temp():
    try:
        cpu = Cpu(monitoring_latency=1)
        with cpu:
            return cpu.temperature
    except Exception as e:
        log_error(Exception(f"Cont get cpu_temp: {str(e)}"))
        return None

def get_cpu_usage():
    try:
        return psutil.cpu_percent(interval=1)
    except Exception as e:
        log_error(Exception(f"Cont get cpu_usage: {str(e)}"))
        return None

def get_gpu_temp():
    try:
        gpus = GPUtil.getGPUs()
        gpu_temp = 0.0
        for gpu in gpus:
            gpu_temp = max(gpu.temperature, gpu_temp)
        return gpu_temp
    except Exception as e:
        log_error(Exception(f"Cont get gpu_temp: {str(e)}"))
        return None

def get_gpu_usage():
    try:
        gpus = GPUtil.getGPUs()
        gpu_usage = 0.0
        for gpu in gpus:
            gpu_usage = gpu_usage + gpu.load
        return gpu_usage * 100 / len(gpus) 
    except Exception as e:
        log_error(Exception(f"Cont get gpu_usage: {str(e)}"))
        return None

def get_ram_usage():
    try:
        return psutil.virtual_memory()[2]
    except Exception as e:
        log_error(Exception(f"Cont get ram_usage: {str(e)}"))
        return None

def get_up_time():
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            return str(timedelta(seconds = uptime_seconds))
    except Exception as e:
        log_error(Exception(f"Cont get up_time: {str(e)}"))
        return None

def is_idle(cpu_usage: float, gpu_usage: float, ram_usage: float, threshold: int = 5):
    if gpu_usage < threshold and gpu_usage < threshold and ram_usage < threshold:
        return True
    else:
        return False

def log_error(e: Exception):
    #todo: write to log
    print(str(e), flush=True)   