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

@cron.interval_schedule(seconds=config.interval)
def make_metrics_report(idle_start_time: datetime = _idle_start_time, config: Config = config):
    '''
    Процедура берет следующие метрики и отправляет их на сервер.

    ip:        внешний ip в сети, (string)
    cpu_temp:  температура самого горячего cpu в °С, (Float)
    gpu_temp:  температура самой горячей gpu в °С, (Float)
    cpu_usage: среднее исполнение cpu в %, (float)
    gpu_usage: среднее исполнение gpu в %, (float) 
    ram_usage: использование памяти в %, (float) 
    idle_time: время простоя dd:hh:mm:ss:ms.ms, (str)
                - Если использование ресурсов меньше трешхолда то время простоя растет, иначе обнуляется
    up_time:   время работы dd:hh:mm:ss:ms.ms, (str)
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
        'cpu_temp':  float(cpu_temp),
        'gpu_temp':  float(gpu_temp),
        'cpu_usage': float(cpu_usage),
        'gpu_usage': float(gpu_usage),
        'ram_usage': float(ram_usage),
        'up_time':   str(up_time),
        'idle_time': str(idle_time)
    }
    print(f'report: {report}')
    headers = {'content-type': 'application/json'}
    try:
        response = requests.post(config.server, json=report, headers=headers, timeout=5)
        if response.status_code != 200:
            raise Exception(f"can not send report: {response.status_code}")
    except Exception as e:
        print(str(e), flush=True)

@app.get('/api/v1/metrics')
async def get_metrics(idle_start_time: datetime = _idle_start_time, config: Config = config):
    '''
    Процедура берет следующие метрики и возвращает их.

    ip:        внешний ip в сети, (string)
    cpu_temp:  температура самого горячего cpu в °С, (Float)
    gpu_temp:  температура самой горячей gpu в °С, (Float)
    cpu_usage: среднее исполнение cpu в %, (float)
    gpu_usage: среднее исполнение gpu в %, (float) 
    ram_usage: использование памяти в %, (float) 
    idle_time: время простоя dd:hh:mm:ss:ms.ms, (str)
                - Если использование ресурсов меньше трешхолда то время простоя растет, иначе обнуляется
    up_time:   время работы dd:hh:mm:ss:ms.ms, (str)
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
        'cpu_temp':  float(cpu_temp),
        'gpu_temp':  float(gpu_temp),
        'cpu_usage': float(cpu_usage),
        'gpu_usage': float(gpu_usage),
        'ram_usage': float(ram_usage),
        'up_time':   str(up_time),
        'idle_time': str(idle_time)
    }
    return report