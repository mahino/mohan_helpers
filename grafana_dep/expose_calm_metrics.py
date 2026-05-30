from prometheus_client import Gauge, start_http_server
import os
import subprocess
import time
process_cpu_usage = {}
process_memory_usage = {}
process_memory_mb = {}

process_names = [
    "/home/calm/bin/algalon",
    "/home/calm/bin/eos",
    "/home/calm/bin/goiris",
    "/home/calm/bin/helios",
    "hercules/app.pyc --process_num=0",
    "hercules/app.pyc --process_num=1",
    "/home/calm/bin/jove",
    "calm/server/styx"
]
for process_name in process_names:
    process_cpu_usage[process_name] = Gauge(f'{process_name.replace("/", "_").replace(".", "_").replace(" ", "_").replace("=", "_").replace("-", "_")}_cpu_usage_percent', f'CPU usage percentage for {process_name}')
    process_memory_usage[process_name] = Gauge(f'{process_name.replace("/", "_").replace(".", "_").replace(" ", "_").replace("=", "_").replace("-", "_")}_memory_usage_percent', f'Memory usage percentage for {process_name}')
    process_memory_mb[process_name] = Gauge(f'{process_name.replace("/", "_").replace(".", "_").replace(" ", "_").replace("=", "_").replace("-", "_")}_memory_mb', f'Memory usage percentage for {process_name}')
entity_stats = Gauge('entity_stats', 'Entity memory and count', ['entity_type', 'metric'])
styx_child_stats = Gauge('styx_child_stats', 'styx child memory and count', ['pid', 'metric'])
idf_res_mem = Gauge('idf_res_mem', 'generic stats: idf_res_mem')

def dump_stats(process_name, pid, cpu_usage, mem_usgae, res_mem):
    process_cpu_usage[process_name].set(cpu_usage)
    process_memory_usage[process_name].set(mem_usgae)
    process_memory_mb[process_name].set(res_mem)
    print(f"Process {process_name} (PID {pid}): CPU {float(cpu_usage)}%, Memory {mem_usgae}%, Memory MB {res_mem}")

def collect_system_metrics():
    styx_process = {}
    try:
        top_output = subprocess.check_output(['top', '-bwcn1']).decode('utf-8').splitlines()
        for line in top_output:
            for process_name in process_names:
                if process_name in line:
                    parts = line.split()
                    if process_name == 'calm/server/styx':
                        styx_process[eval(parts[0])] = {"cpu_usage": parts[8], "mem_usgae": parts[9], "res_mem": parts[5]}
                        continue
                    dump_stats(process_name, parts[0], float(parts[8]), float(parts[9]), float(parts[5]))
                    break
        styx_main_pid = min(styx_process)
        dump_stats("calm/server/styx", str(styx_main_pid), styx_process[styx_main_pid]['cpu_usage'], styx_process[styx_main_pid]['mem_usgae'], styx_process[styx_main_pid]['res_mem'])
        del styx_process[styx_main_pid]
        for styx_c_pid in styx_process:
            styx_child_stats.labels(pid=styx_c_pid, metric='cpu_usage').set(styx_process[styx_c_pid]["cpu_usage"])
            styx_child_stats.labels(pid=styx_c_pid, metric='mem_usgae').set(styx_process[styx_c_pid]["mem_usgae"])
            styx_child_stats.labels(pid=styx_c_pid, metric='res_mem').set(styx_process[styx_c_pid]["res_mem"])
            print(f"Process styx_child (PID {styx_c_pid}): CPU {styx_process[styx_c_pid]['cpu_usage']}%, Memory {styx_process[styx_c_pid]['mem_usgae']}%, Memory MB {styx_process[styx_c_pid]['res_mem']}")

        s = os.popen('elinks -dump calm_idf_ip:2027 | grep -A1 "Resident" | grep "Size(MB)" -B1 | grep "Resident" | awk \'{print $2}\'').read().strip()
        print("idf res mem(MB): " + s.replace('|', ''))
        idf_res_mem.set(float(s.replace('|', '')))

        s = os.popen("elinks calm_idf_ip:2027/detailed_unevictable_cache_stats").read().strip().split('\n')
        for i in s[7::2]:
          r = i.replace('|',' ').split()
          print(r[0] + ' mem(MB): ' +  r[1])
          print(r[0] + ' #entities: ' +  r[2])
          entity_stats.labels(entity_type=r[0], metric='mem').set(float(r[1]))
          entity_stats.labels(entity_type=r[0], metric='entities').set(float(r[2]))
          if 'Total' in i:
            break

        s = os.popen("elinks common_idf_ip:2027/detailed_unevictable_cache_stats").read().strip().split('\n')
        for i in s[7::2]:
          r = i.replace('|',' ').split()
          if r[0] == 'task':
            print(r[0] + ' mem(MB): ' +  r[1])
            print(r[0] + ' #entities: ' +  r[2])
            entity_stats.labels(entity_type=r[0], metric='mem').set(float(r[1]))
            entity_stats.labels(entity_type=r[0], metric='entities').set(float(r[2]))
            break
    except subprocess.CalledProcessError as e:
        print(f"Error collecting system metrics: {e}")
def main():
    start_http_server(8001)
    print("Metrics server started on port 8001")
    while True:
      collect_system_metrics()
      time.sleep(5)
if __name__ == '__main__':
    main()
