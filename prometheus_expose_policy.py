from prometheus_client import Gauge, start_http_server
import subprocess
import json
import time
import os
import re

process_cpu_usage = {}
process_memory_usage = {}
process_memory_mb = {}
load_average = {}

process_names = [
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

policy_res = Gauge('policy_services_stats', 'Policy memory usage in RES', ['pid', 'process', 'namespace', 'container', 'command', "type"])

for process_name in process_names:
    process_cpu_usage[process_name] = Gauge(f'{process_name.replace("/", "_").replace(".", "_").replace(" ", "_").replace("=", "_").replace("-", "_")}_cpu_usage_percent', f'CPU usage percentage for {process_name}.')
    process_memory_usage[process_name] = Gauge(f'{process_name.replace("/", "_").replace(".", "_").replace(" ", "_").replace("=", "_").replace("-", "_")}_memory_usage_percent', f'Memory usage percentage for {process_name}.')
    process_memory_mb[process_name] = Gauge(f'{process_name.replace("/", "_").replace(".", "_").replace(" ", "_").replace("=", "_").replace("-", "_")}_memory_mb', f'Memory usage percentage for {process_name}.')

proxy_child_stats = Gauge('proxy_child_stats', 'proxy child memory and count', ['pid', 'metric'])

def dump_stats(process_name, pid, cpu_usage, mem_usgae, res_mem):
    process_cpu_usage[process_name].set(cpu_usage)
    process_memory_usage[process_name].set(mem_usgae)
    process_memory_mb[process_name].set(res_mem)
    print(f"Process {process_name} (PID {pid}): CPU {float(cpu_usage)}%, Memory {mem_usgae}%, Memory MB {res_mem}")

def collect_system_metrics():
    proxy_services = {}
    try:
        top_output = subprocess.check_output(['top', '-bwcn1']).decode('utf-8').splitlines()
        for line in top_output:
            for process_name in process_names:
                if process_name in line:
                    parts = line.split()
                    if 'proxy_service' in process_name:
                        proxy_services[eval(parts[0])] = {"cpu_usage": parts[8], "mem_usgae": parts[9], "res_mem": parts[5]}
                        continue
                    dump_stats(process_name, parts[0], float(parts[8]), float(parts[9]), float(parts[5]))
                    break
        proxy_service_main_pid = min(proxy_services)
        dump_stats("home/epsilon/conf/modules/proxy_service.ini", str(proxy_service_main_pid), proxy_services[proxy_service_main_pid]['cpu_usage'], proxy_services[proxy_service_main_pid]['mem_usgae'], proxy_services[proxy_service_main_pid]['res_mem'])
        del proxy_services[proxy_service_main_pid]
        for proxy_c_pid in proxy_services:
            proxy_child_stats.labels(pid=parts[0], metric='cpu_usage').set(proxy_services[proxy_c_pid]["cpu_usage"])
            proxy_child_stats.labels(pid=parts[0], metric='mem_usage').set(proxy_services[proxy_c_pid]["mem_usgae"])
            proxy_child_stats.labels(pid=parts[0], metric='res_mem').set(proxy_services[proxy_c_pid]["res_mem"])
            print(f"Process proxy_child (PID {proxy_c_pid}): CPU {proxy_services[proxy_c_pid]['mem_usgae']}%, Memory {proxy_services[proxy_c_pid]['mem_usgae']}%, Memory MB {proxy_services[proxy_c_pid]['res_mem']}")

    except subprocess.CalledProcessError as e:
        print(f"Error collecting system metrics: {e}")

def policy_collect_system_metrics():
    target_pods = [
        ("ncm-tunnel-server-6b7748ccd9-fwlt7", "openssh-server", "b", ['sshd.pam']),
        ("ncm-tunnel-server-6b7748ccd9-fwlt7", "tunnelserver", "bc", ['/home/tunnelserver/bin/tunnelserver']),
        ("ncm-policy-7b6687dd7d-xgrpb", "ncm-policy", "bc", ['leo', 'terraform_plum_v1 -host=localhost -port=4258', 'terraform_plum_v1 -host=localhost -port=4257', 'plum', 'agni', 'ganga', 'kali', 'email/v1/app.pyc --host localhost --port 4259', 'email/v1/app.pyc --host localhost --port 4260', 'approval_v1 -host=localhost -port=4257', 'approval_v1 -host=localhost -port=4258']),
        ("ncm-scheduler-85f9fb8bd6-tdphk", "ncm-scheduler", "bc", ['/home/epsilon/bin/chronos --swagger-file', 'chronos_supervisorevents.py --port 2814', 'chronos --worker-id=0', '/home/epsilon/bin/jove', 'chronos_startup.sh'])
    ]
    
    for pod, container, flags, processes in target_pods:
        print(f"Collecting metrics from pod: {pod}, container: {container}")
        try:
            # Execute the top command
            cmd = f"kubectl exec -n ntnx-ncm-self-service {pod} -c {container} -- top -{flags} -w 256 -n 1"
            output = os.popen(cmd).read().strip()

            # Parse top output
            starting_line = 0
            for idx, line in enumerate(output.split('\n')):
                if 'PID' in line:
                    pid_idx = line.split().index('PID')
                    res_idx = line.split().index('RES')
                    cpu_idx = line.split().index('%CPU')
                    mem_perc_idx = line.split().index('%MEM')
                    cmd_idx = line.split().index('COMMAND')
                    starting_line = idx + 1
                    break

            for line in output.split('\n')[starting_line:]:
                for process_name in processes:
                    if process_name in line:
                        parts = line.split()
                        print(parts)
                        print(" ".join(parts[cmd_idx:]))
                        res_value = parts[res_idx]
                        if res_value[-1] == 'm':
                            res_value = float(res_value[:-1]) * 1024
                        elif res_value[-1] == 'g':
                            res_value = float(res_value[:-1]) * 1024 *  1024
                        policy_res.labels(
                            pid=parts[pid_idx],
                            process=process_name,
                            namespace="ntnx-ncm-self-service",
                            container=container,
                            command=" ".join(parts[cmd_idx:]),
                            type="mem_rss"
                        ).set(res_value)
                        policy_res.labels(
                            pid=parts[pid_idx],
                            process=process_name,
                            namespace="ntnx-ncm-self-service",
                            container=container,
                            command=" ".join(parts[cmd_idx:]),
                            type="mem_perc"
                        ).set(float(parts[mem_perc_idx].replace('K', '')))
                        policy_res.labels(
                            pid=parts[pid_idx],
                            process=process_name,
                            namespace="ntnx-ncm-self-service",
                            container=container,
                            command=" ".join(parts[cmd_idx:]),
                            type="cpu_perc"
                        ).set(float(parts[cpu_idx].replace('K', '')))
                        print(f"Metrics collected: {parts}")
                        

        except Exception as e:
            print(f"Error collecting metrics: {e}")

def main():
    start_http_server(8002)
    print("Metrics server started on port 8002:32552")
    while True:
      collect_system_metrics()
      policy_collect_system_metrics()
      time.sleep(5)
if __name__ == '__main__':
    main()