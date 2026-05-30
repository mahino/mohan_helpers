import subprocess
import datetime
import os
import time
import copy

def check_ping(ip_address):
    # Ping the IP address once
    process = subprocess.Popen(['ping', '-c', '1', ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return process.returncode == 0  # Return True if return code is 0 (success), False otherwise

# Example usage

details = {
    "epsilon_start_time": "",
    "epsilon_end_time": "",
    "epsilon_up_time": "",
    "nucalm_start_time": "",
    "nucalm_end_time": "",
    "nucalm_up_time": "",
    "domain_manager_start_time": "",
    "domain_manager_end_time": "",
    "domain_manager_up_time": "",
    "svm_ips": []
}

data = {}

# for j in range(0, 256):
#     hostname = f"10.36.199.{j}"
li = ['10.115.150.10', '10.115.150.14']
for hostname in li:
    patterns = {
        # "nucalm": "Calm is up",
        # "epsilon": "Clearing all keys from redis",
        "domain_manager": "Domain Manager is up"
    }
    if check_ping(hostname):
        print(hostname)
        
        username = 'nutanix'  # Replace with your SSH username
        password = 'nutanix/4u'  # Replace with your SSH password
        copyData = copy.deepcopy(details)
        end = os.popen(f"sshpass -p '{password}' ssh {username}@{hostname} /usr/local/nutanix/cluster/bin/svmips").read().strip()

        # File paths
        ss_up_timings = []
        for file_name in ['domain_manager']:
            remote_path = '/home/nutanix/data/logs/' + file_name + '.out'  # Path to the file on the server
            copy_command = f"sshpass -p '{password}' scp {username}@{hostname}:{remote_path} ."
            os.popen(copy_command)
            time.sleep(1)
            try:
                with open(file_name + '.out') as l:
                    m = f"cat {file_name}.out | grep '{patterns[file_name]}'"
                    start = l.readlines()[0]
                    end_command = f"cat {file_name}.out | grep '{patterns[file_name]}'"
                    if file_name == 'epsilon':
                        end_command += ' | tail -n 1'
                    end = os.popen(end_command).read().strip()
                    if len(end) == 0:
                        print(f"end time not found for {hostname} : {file_name}")
                    else:
                        start_time_str = start.split('Z')[0].strip()
                        start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S,%f')
                        if file_name == 'epsilon':
                            end_time_str = end.split(' ')[0].split('00m')[1]
                            date_str = start_time_str.split(' ')[0]  # Extract the date part from the start time
                            end_time_str = f"{date_str} {end_time_str}"
                            end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
                            if end_time <= start_time:
                                end_time += datetime.timedelta(days=1)
                        else:
                            end_time_str = end.split('(')[1].split(')')[0]
                            end_time = datetime.datetime.strptime(end_time_str, 'at %a %b %d %H:%M:%S GMT %Y')
                        # Calculate the difference
                        ss_up_timings.extend([end_time,start_time])
                        time_diff = end_time - start_time
                        print(f"{file_name} Time difference: {time_diff.total_seconds()}")
                os.popen(f"rm -rf {file_name}.out")  
            except FileNotFoundError:
                print(f"Self Service not enabled for [{hostname}]")
                break
        if len(ss_up_timings) == 4:
            print(ss_up_timings)
            print("Self Service up time: ", (max(ss_up_timings) - min(ss_up_timings)).total_seconds())
        time.sleep(2)
        print("=="*20)
