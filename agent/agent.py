import requests
import argparse
import json
from controllers import metrics_controller as metrics
from fastapi import FastAPI, HTTPException, Request, Response
from apscheduler.scheduler import Scheduler
from config import Config
from datetime import datetime

# global params
global _idle_start_time
global config

app = FastAPI()

cron = Scheduler(daemon=True)
cron.start()

config = Config()
_idle_start_time = datetime.now()

@cron.interval_schedule(seconds=5)
def tame_metrics(idle_start_time: datetime = _idle_start_time, config: Config = config):
    '''
    ip: external ip (string)
    cpuTemp:  температура самого горячего ядра °С (Float)
    gpuTemp: температура самой горячей gpu
    cpuUsage: среднее исполнение в долях, (float)
    gpuUsage: среднее исполнение в долях, (float) 
    ramUssage: в долях (float) 
    idleTime: время простоя, dd-hh-mm-ss. Если использование ресурсов меньше трешхолда то прибовояю время, если больше трешхолда то обнуляю его
    upTime: время работы.
    '''
    ip = metrics.get_ip()
    cpu_temp = metrics.get_cpu_temp()
    cpu_usage = metrics.get_cpu_usage()
    gpu_temp = metrics.get_gpu_temp()
    gpu_usage = metrics.get_gpu_usage()
    ram_usage = metrics.get_ram_usage()
    up_time = metrics.get_up_time()
    if metrics.is_idle(cpu_usage, gpu_usage, ram_usage, 5):
        idle_time = datetime.now() - idle_start_time
    else:
        _idle_start_time = datetime.now()
        idle_time = _idle_start_time - _idle_start_time
    report = {
        'ip': ip,
        'cpu_temp': cpu_temp,
        'gpu_temp': gpu_temp,
        'cpu_usage': cpu_usage,
        'gpu_usage': gpu_usage,
        'ram_usage': ram_usage,
        'up_time': up_time,
        'idle_time': str(idle_time)
    }
    print(f'report: {report}')
    headers = {'content-type': 'application/json'}
    try:
        response = requests.post(config.server, json=report, headers=headers, timeout=5)
        if response.status_code != 200:
            raise Exception(f"can not send teport: {response.status_code}")
    except Exception as e:
        print(str(e), flush=True)