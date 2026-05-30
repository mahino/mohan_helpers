from prometheus_client import Gauge, start_http_server
import json
import subprocess
import time
import re
import signal

top_stats_start = "ST: TOP STATS START"
top_stats_end = "ST: TOP STATS END"
top_mem_stats_start = "ST: TOP MEMORY STATS START"
top_mem_stats_end = "ST: TOP MEMORY STATS END"
pids_start = "ST: PROCESS IDs START"
pids_end = "ST: PROCESS IDs END"

calm_pids = {}
final_result = {}

micro_servie_stats = Gauge(
    "micro_services_stats",
    "micro memory usage in RES",
    ["pid", "process", "name_space", "container_name", "command", "type"],
)

idf_res_mem = Gauge("idf_res_mem", "generic stats: idf_res_mem")
entity_stats = Gauge(
    "entity_stats", "Entity memory and count", ["entity_type", "metric"]
)
top_20_cpu_stats = Gauge(
    "top_20_cpu_stats",
    "Top 20 CPU consumping proceses",
    ["pid", "name_space", "container_name", "command", "type"],
)
top_20_mem_stats = Gauge(
    "top_20_mem_stats",
    "Top 20 CPU consumping proceses",
    ["pid", "name_space", "container_name", "command", "type"],
)

calm_idf_ip = None
common_idf_ip = None

tunnel_pod_name = None
policy_pod_name = None
scheduler_pod_name = None


def get_top_cpu_processes(process_lines, pid_idx, cpu_idx, cmd_idx):
    processes = []
    for line in process_lines:
        parts = line.split()
        if len(parts) < 12:
            continue
        pid = parts[pid_idx]
        cpu = parts[cpu_idx]
        try:
            cpu = float(cpu)
        except ValueError as e:
            print(f"ERROR: Value error during cpu data processing [{e}]")
            continue
        command = " ".join(parts[cmd_idx:])
        processes.append((pid, cpu, command))
    processes.sort(key=lambda x: x[1], reverse=True)
    top_20 = processes[:20]
    return top_20


def get_top_memory_processes(process_lines, pid_idx, res_idx, cmd_idx):
    processes = []
    for line in process_lines:
        parts = line.split()
        if len(parts) < 12:
            continue
        pid = parts[pid_idx]
        mem = parts[res_idx]
        try:
            mem = float(mem)
        except ValueError:
            print(mem)
            value, unit = mem[:-1], mem[-1:].upper()
            value = float(value)
            if unit == "G":
                mem = value * 1024 * 1024
                print("MEM", mem)
            elif unit == "M":
                mem = value * 1024
            else:
                continue
        command = " ".join(parts[cmd_idx:])
        processes.append((pid, mem, command))
    processes.sort(key=lambda x: x[1], reverse=True)

    top_20 = processes[:20]
    print(json.dumps(top_20))
    return top_20


def replace_string(string):
    return (
        string.replace("/", "_")
        .replace(".", "_")
        .replace(" ", "_")
        .replace("=", "_")
        .replace("-", "_")
        .replace(":", "_")
        .replace("+", "___")
    )


def set_values(pid, process_name, name_space, conainer_name, command, type, value):
    process_name = replace_string(process_name)
    name_space = replace_string(name_space)
    conainer_name = replace_string(conainer_name)
    command = replace_string(command)

    micro_servie_stats.labels(
        pid=pid,
        process=process_name,
        name_space=name_space,
        container_name=conainer_name,
        command=command,
        type=type,
    ).set(value)


def main():
    calm_idf_ip = None
    common_idf_ip = None
    tunnel_pod_name = None
    policy_pod_name = None
    scheduler_pod_name = None
    final_result["top_20_cpu_stats"] = []
    final_result["top_20_mem_stats"] = []
    target_pods = [
        (
            "ntnx-ncm-self-service",
            "ncm-calm-2",
            "ncm-calm",
            [
                f"echo {top_stats_start}",
                "top -bc -w 256 -n 1",
                f"echo {top_stats_end}",
                f"echo {top_mem_stats_start}",
                "top -bc -w 256 -n 1 -o %MEM",
                f"echo {top_mem_stats_end}",
                f"echo {pids_start}",
                "source /home/calm/venv3/bin/activate && status",
                f"echo {pids_end}",
            ],
        ),
        (
            "ntnx-ncm-self-service",
            None,
            "ncm-policy",
            [
                f"echo {top_stats_start}",
                "top -bc -w 256 -n 1",
                f"echo {top_stats_end}",
                f"echo {top_mem_stats_start}",
                "top -bc -w 256 -n 1 -o %MEM",
                f"echo {top_mem_stats_end}",
                f"echo {pids_start}",
                "source /home/policy/venv3/bin/activate && status",
                f"echo {pids_end}",
            ],
        ),
        (
            "ntnx-ncm-self-service",
            None,
            "ncm-scheduler",
            [
                f"echo {top_stats_start}",
                "top -bc -w 256 -n 1",
                f"echo {top_stats_end}",
                f"echo {top_mem_stats_start}",
                "top -bc -w 256 -n 1 -o %MEM",
                f"echo {top_mem_stats_end}",
                f"echo {pids_start}",
                "source /home/epsilon/venv3/bin/activate && status",
                f"echo {pids_end}",
            ],
        ),
        (
            "ntnx-ncm-self-service",
            None,
            "openssh-server",
            [
                f"echo {top_stats_start}",
                "top -b -w 256 -n 1",
                f"echo {top_stats_end}",
            ],
        ),
        (
            "ntnx-ncm-self-service",
            None,
            "tunnelserver",
            [
                f"echo {top_stats_start}",
                "top -bc -w 256 -n 1",
                f"echo {top_stats_end}",
            ],
        ),
        (
            "ntnx-ncm-common",
            "ncm-epsilon-0",
            "ncm-epsilon",
            [
                f"echo {top_stats_start}",
                "top -bc -w 256 -n 1",
                f"echo {top_stats_end}",
                f"echo {top_mem_stats_start}",
                "top -bc -w 256 -n 1 -o %MEM",
                f"echo {top_mem_stats_end}",
                f"echo {pids_start}",
                "source /home/epsilon/venv3/bin/activate && status",
                f"echo {pids_end}",
            ],
        )
    ]

    for name_space, pod, container_name, commands in target_pods:
        if container_name in ["tunnelserver", "openssh-server"]:
            if tunnel_pod_name == None:
                tunnel_pod_name = subprocess.run(
                    "kubectl get pods -n ntnx-ncm-self-service | grep tunnel | awk '{print $1}'",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                tunnel_pod_name = tunnel_pod_name.stdout.strip()
            pod = tunnel_pod_name
        elif container_name == "ncm-scheduler":
            if scheduler_pod_name == None:
                scheduler_pod_name = subprocess.run(
                    "kubectl get pods -n ntnx-ncm-self-service | grep scheduler | awk '{print $1}'",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                scheduler_pod_name = scheduler_pod_name.stdout.strip()
            pod = scheduler_pod_name
        elif container_name == "ncm-policy":
            if policy_pod_name == None:
                policy_pod_name = subprocess.run(
                    "kubectl get pods -n ntnx-ncm-self-service | grep policy | awk '{print $1}'",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                policy_pod_name = policy_pod_name.stdout.strip()
            pod = policy_pod_name
        commands = ";".join(commands)
        cmd = f"kubectl exec -n {name_space} {pod} -c {container_name} -- bash -i -c '{commands}'"
        print(cmd)
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=20
            )
        except subprocess.TimeoutExpired:
            print("ERROR: Command timed out")
            break
        output = result.stdout.strip()
        pattern = re.compile(
            rf"^.*{top_stats_start}.*$[\s\S]*?^.*{top_stats_end}.*$", re.MULTILINE
        )
        mem_pattern = re.compile(
            rf"^.*{top_mem_stats_start}.*$[\s\S]*?^.*{top_mem_stats_end}.*$",
            re.MULTILINE,
        )
        top_data = pattern.search(output)
        top_mem_data = mem_pattern.search(output)

        if top_data == None:
            print(f"INFO: top data not found [{name_space} - {container_name}]")
            top_data = []
        else:
            top_data = top_data.group(0).split("\n")
        if top_mem_data == None:
            print(f"INFO: top mem data not found [{name_space} - {container_name}]")
            top_mem_data = []
        else:
            top_mem_data = top_mem_data.group(0).split("\n")
        pid_pattern = re.compile(
            rf"^.*{pids_start}.*$[\s\S]*?^.*{pids_end}.*$", re.MULTILINE
        )
        pids_data = pid_pattern.search(output)
        if pids_data != None:
            pids_data = pids_data.group(0)
            for pid_data in pids_data.split("\n"):
                pid_data = pid_data.split()
                if len(pid_data) == 1:
                    continue
                try:
                    if pid_data[1] == "RUNNING":
                        calm_pids[pid_data[3][:-1]] = pid_data[0]
                        if pid_data[0] == "superevents":
                            calm_pids[pid_data[3][:-1]] = (
                                container_name + ":superevents"
                            )
                except IndexError as e:
                    print(pid_data)
                    print(f"ERROR: Index error during processing pids data [{e}]")
                    break
        starting_line = 0
        for idx, line in enumerate(top_data):
            if "PID" in line:
                pid_idx = line.split().index("PID")
                res_idx = line.split().index("RES")
                cpu_idx = line.split().index("%CPU")
                mem_perc_idx = line.split().index("%MEM")
                cmd_idx = line.split().index("COMMAND")
                starting_line = idx + 1
                break
        mem_starting_line = 0
        for idx, line in enumerate(top_mem_data):
            if "PID" in line:
                mem_starting_line = idx + 1
                break

        for pid_stats in top_data[starting_line:]:
            pid_stats = pid_stats.split()
            if pid_stats[pid_idx] in calm_pids or container_name in [
                "openssh-server",
                "tunnelserver",
            ]:
                restart_value = 0
                restart_hold = 0
                if container_name in ["openssh-server", "tunnelserver"]:
                    service_name = (
                        replace_string(" ".join(pid_stats[cmd_idx:]))
                        + "_"
                        + pid_stats[pid_idx]
                    )
                else:
                    service_name = calm_pids[pid_stats[pid_idx]]
                    if service_name in final_result:
                        if final_result[service_name].get('restart_hold', 0):
                            restart_value = 1
                            restart_hold = 0
                        if final_result[service_name]["pid"] != pid_stats[pid_idx]:
                            restart_hold = 1
                            restart_value = 1

                final_result[service_name] = {
                    "pid": pid_stats[pid_idx],
                    "cpu_perc": pid_stats[cpu_idx],
                    "mem_perc": pid_stats[mem_perc_idx],
                    "mem_rss": pid_stats[res_idx],
                    "command": " ".join(pid_stats[cmd_idx:]),
                    "service_name": service_name,
                    "restart": restart_value,
                    "container_name": container_name,
                    "name_space": name_space,
                    "restart_hold": restart_hold
                }

        if container_name in ["openssh-server", "tunnelserver"]:
            continue

        top_20_cpu_processes = get_top_cpu_processes(
            top_data[starting_line:], pid_idx, cpu_idx, cmd_idx
        )

        top_20_memory_processes = get_top_memory_processes(
            top_mem_data[mem_starting_line:], pid_idx, res_idx, cmd_idx
        )
        print("KILER", top_20_memory_processes)

        # Print top 10 CPU-consuming processes
        print("=" * 50)
        print(f"{'PID':<8} {'CPU%':<8} {'Command'}")
        print("=" * 50)

        for pid, cpu, command in top_20_cpu_processes:
            top_20_cpu_stats.labels(
                pid=pid,
                name_space=name_space,
                container_name=container_name,
                command=command,
                type="cpu_perc",
            ).set(float(cpu))

            print(f"{pid:<8} {cpu:<8.2f} {command}")
            top_20_dict = {
                "pid": pid,
                "cpu_perc": cpu,
                "command": command,
                "container_name": container_name,
                "name_space": name_space,
            }
            final_result["top_20_cpu_stats"] = top_20_dict

        print("\n" + "=" * 50 + "\n")

        # Print top 10 memory-consuming processes
        print("=" * 50)
        print(f"{'PID':<8} {'MEM%':<8} {'Command'}")
        print("=" * 50)
        for pid, mem, command in top_20_memory_processes:
            top_20_mem_stats.labels(
                pid=pid,
                name_space=name_space,
                container_name=container_name,
                command=command,
                type="memory",
            ).set(float(mem))

            print(f"{pid:<8} {mem:<8.2f} {command}")
            top_20_mem_dict = {
                "pid": pid,
                "mem_rss": mem,
                "command": command,
                "container_name": container_name,
                "name_space": name_space,
            }
            final_result["top_20_mem_stats"] = top_20_mem_dict

    for process in final_result:
        if process in ("top_20_cpu_stats", "top_20_mem_stats"):
            continue
        process = final_result[process]
        rss_value = process["mem_rss"]
        if rss_value[-1] == "m":
            rss_value = float(rss_value[:-1]) * 1024
        elif rss_value[-1] == "g":
            rss_value = float(rss_value[:-1]) * 1024 * 1024
        set_values(
            process["pid"],
            process["service_name"],
            process["name_space"],
            process["container_name"],
            process["command"],
            "mem_rss",
            rss_value,
        )
        set_values(
            process["pid"],
            process["service_name"],
            process["name_space"],
            process["container_name"],
            process["command"],
            "mem_perc",
            float(process["mem_perc"].replace("K", "")),
        )
        set_values(
            process["pid"],
            process["service_name"],
            process["name_space"],
            process["container_name"],
            process["command"],
            "cpu_perc",
            float(process["cpu_perc"].replace("K", "")),
        )
        set_values(
            process["pid"],
            process["service_name"],
            process["name_space"],
            process["container_name"],
            process["command"],
            "restarts",
            float(process["restart"]),
        )

    if calm_idf_ip is None:
        try:
            calm_idf_ip = subprocess.run(
                "kubectl get svc -n ntnx-ncm-datastore ss-idf | grep idf  | awk '{print $3}'",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            calm_idf_ip = calm_idf_ip.stdout.strip()
        except subprocess.TimeoutExpired as e:
            print(f"ERROR: Command timed out: [{e}]")
    if common_idf_ip is None:
        try:
            common_idf_ip = subprocess.run(
                "kubectl get svc -n ntnx-ncm-datastore idf | grep idf  | awk '{print $3}'",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            common_idf_ip = common_idf_ip.stdout.strip()
        except subprocess.TimeoutExpired as e:
            print(f"ERROR: Command timed out [{e}]")

    s = subprocess.run(
        f"elinks -dump {calm_idf_ip}:2027"
        + ' | grep -A1 "Resident" | grep "Size(MB)" -B1 | grep "Resident" | awk \'{print $2}\'',
        shell=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    s = s.stdout.strip()
    s = re.sub(r"[^0-9.]", "", s)
    if len(s) != 0:
        idf_res_mem.set(float(s.replace("|", "")))

        s = subprocess.run(
            f"elinks {calm_idf_ip}:2027/detailed_unevictable_cache_stats",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        s = s.stdout.strip().splitlines()
        for i in s[7::2]:
            pat = next((j for j in i if j != " "), None)
            r = i.replace(pat, " ").split()
            entity_stats.labels(entity_type=r[0], metric="mem").set(float(r[1]))
            entity_stats.labels(entity_type=r[0], metric="entities").set(float(r[2]))
            if "Total" in i:
                break

        s = subprocess.run(
            f"elinks {common_idf_ip}:2027/detailed_unevictable_cache_stats",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        s = s.stdout.strip().splitlines()
        for i in s[7::2]:
            pat = next((j for j in i if j != " "), None)
            r = i.replace(pat, " ").split()
            if r[0] == "task":
                entity_stats.labels(entity_type=r[0], metric="mem").set(float(r[1]))
                entity_stats.labels(entity_type=r[0], metric="entities").set(
                    float(r[2])
                )
                break
    else:
        print("WARN: elinks intallation failed, install elinks")


if __name__ == "__main__":
    start_http_server(8003)
    print("Metrics server started on port 8002:32552")
    while True:
        start_time = time.time()
        main()
        print(json.dumps(final_result))
        while time.time() < start_time + 15:
            print("WAIT: sleeping ")
            time.sleep(1)
        # Reap zombie processes
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

