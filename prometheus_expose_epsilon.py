from prometheus_client import Gauge, start_http_server
import subprocess
import json
import time
import re

process_cpu_usage = {}
process_memory_usage = {}
process_memory_mb = {}
load_average = {}

pids = [
    "var/lib/pgsql/11/data/postgresql.conf",
    "usr/bin/redis-serve",
    "home/epsilon/bin/zaffi",
    "home/epsilon/conf/modules/proxy_service.ini",
    "home/epsilon/bin/arjun --worker-id=0",
    "home/epsilon/bin/arjun --worker-id=1",
    "home/epsilon/bin/durga --worker-id=0",
    "home/epsilon/bin/durga --worker-id=1",
    "elastic_search",
    "home/epsilon/bin/indra --worker-id=0",
    "home/epsilon/bin/indra --worker-id=1",
    "home/epsilon/bin/jove",
    "home/epsilon/bin/karan --worker-id=0",
    "home/epsilon/bin/karan --worker-id=1",
    "home/epsilon/bin/narad",
    "spy_0",
    "epsilon-engine:vajra_0"
]

for process_name, pid in pids.items():
    process_cpu_usage[process_name] = Gauge(f'{process_name.replace("/", "_").replace(".", "_").replace(" ", "_").replace("=", "_").replace("-", "_")}_cpu_usage_percent', f'CPU usage percentage for {process_name} (PID {pid})')
    process_memory_usage[process_name] = Gauge(f'{process_name.replace("/", "_").replace(".", "_").replace(" ", "_").replace("=", "_").replace("-", "_")}_memory_usage_percent', f'Memory usage percentage for {process_name} (PID {pid})')
    process_memory_mb[process_name] = Gauge(f'{process_name.replace("/", "_").replace(".", "_").replace(" ", "_").replace("=", "_").replace("-", "_")}_memory_mb', f'Memory usage percentage for {process_name} (PID {pid})')

proxy_child_stats = Gauge('proxy_child_stats', 'proxy child memory and count', ['pid', 'metric'])

def collect_system_metrics():
    try:
        top_output = subprocess.check_output(['top', '-bcn1']).decode('utf-8').splitlines()
        for line in top_output:
            for process_name, pid in pids.items():
                if f" {pid} " in line:
                    parts = line.split()
                    mem_mb = float(parts[5])
                    mem_usage = float(parts[9])
                    cpu_usage = float(parts[8]) 
                    process_cpu_usage[process_name].set(cpu_usage)
                    process_memory_usage[process_name].set(mem_usage)
                    process_memory_mb[process_name].set(mem_mb)
                    print(f"Process {process_name} (PID {pid}): CPU {cpu_usage}%, Memory {mem_usage}%, Memory MB {mem_mb}%")
            if "proxy_service.ini" in line and f" {pids['home/epsilon/conf/modules/proxy_service.ini']} " not in line:
                parts = line.split()
                proxy_child_stats.labels(pid=parts[0], metric='res_mem').set(float(parts[5]))
                proxy_child_stats.labels(pid=parts[0], metric='mem_usage').set(float(parts[9]))
                proxy_child_stats.labels(pid=parts[0], metric='cpu_usage').set(float(parts[8]))
                print(f"Process proxy_child (PID {parts[0]}): CPU {parts[8]}%, Memory {parts[9]}%, Memory MB {parts[5]}%")

    except subprocess.CalledProcessError as e:
        print(f"Error collecting system metrics: {e}")
def main():
    start_http_server(8002)
    print("Metrics server started on port 8002:32552")
    while True:
      collect_system_metrics()
      time.sleep(5)
if __name__ == '__main__':
    main()