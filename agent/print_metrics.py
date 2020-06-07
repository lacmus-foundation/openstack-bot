import socket
import psutil
import GPUtil
from pyspectator.processor import Cpu
from datetime import datetime, timedelta
import time

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.connect(("8.8.8.8", 80))
    print(f'ip: {str(s.getsockname()[0])}')

cpu = Cpu(monitoring_latency=1)
with cpu:
    print(f'cpu temp: {cpu.temperature}') 

print(f'cpu usage: {psutil.cpu_percent(interval=1)}')

gpus = GPUtil.getGPUs()
gpu_temp = 0.0
gpu_usage = 0.0
for gpu in gpus:
    gpu_temp = max(gpu.temperature, gpu_temp)
    gpu_usage = gpu_usage + gpu.load
print(f'gpu temp: {gpu_temp}')
print(f'gpu usage: {gpu_usage * 100 / len(gpus)}')


print(f'ram usage: {psutil.virtual_memory()[2]}')

with open('/proc/uptime', 'r') as f:
    uptime_seconds = float(f.readline().split()[0])
    uptime_string = str(timedelta(seconds = uptime_seconds))

print(f'up time: {uptime_string}')
