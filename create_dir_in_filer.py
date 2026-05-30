import sys
import paramiko
import traceback
import argparse
import string
import random
import time

pline = "\n========================================\n"




def sshFiler(ip,username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip, username=username,password=password, timeout=30)
    except:
        msg='Login to filer %s failed due to Exception:%s'%(ip,traceback.format_exc())
        print(pline + msg + pline)
    return ssh

def create_log_dir(ip,username, password, location):
    dir_created = 0
    ssh = sshFiler(ip, username, password)
    si, so, se = ssh.exec_command('mkdir {}'.format(location))
    exit_status = so.channel.recv_exit_status()
    si, so, se = ssh.exec_command('ls -ltr {}'.format(location))
    exit_status = so.channel.recv_exit_status()
    ls_output = ''.join(so.readlines())
    if 'total 0' in ls_output:
        dir_created = 1
    return dir_created

if __name__ == "__main__":
    # parser=argparse.ArgumentParser()
    # parser.add_argument('-i', '--ip', help='IP of the filer')
    # parser.add_argument('-u', '--username', help='Username of the filer')
    # parser.add_argument('-p', '--password', help='password of the filer')
    # parser.add_argument('-l', '--location', help='location on the server to be created')
    # args=parser.parse_args()

    # ip  = args.ip
    # username = args.username
    # password = args.password
    # location = args.location
    ip = '10.46.1.165'
    username = 'nutanix'
    password = 'nutanix/4u'
    loc = sys.argv[1]
    # if not ip:
    #     ip = '10.46.1.165'
    # if not username:
    #     username = 'nutanix'
    # if not password:
    #     password = 'nutanix/4u'
    # if not location:
    letters = string.ascii_lowercase
    random_string = ''.join(random.choice(letters) for i in range(10))
    location = '/home/nutanix/data/Bugs/MA/NCM/24_3_1/{}'.format(loc)
    locationepsi = '/home/nutanix/data/Bugs/MA/NCM/24_3_1/{}/epsilon'.format(loc)
    locationcalm = '/home/nutanix/data/Bugs/MA/NCM/24_3_1/{}/nucalm'.format(loc)
    # else:
    #     location = '/home/nutanix/data/Bugs/Jignesh/' + args.location
    if create_log_dir(ip, username, password, location):
        print(pline + "Go ahead and copy logs to {} location".format(location) + pline)
    time.sleep(5)
    if create_log_dir(ip, username, password, location):
        print(pline + "Go ahead and copy logs to {} location".format(locationepsi) + pline)
    if create_log_dir(ip, username, password, location):
        print(pline + "Go ahead and copy logs to {} location".format(locationcalm) + pline)
        sys.exit()
    print(pline + "Dir didn't get created, pls check or create manually" + pline)
    

# logbay collect -D=ftp://nutanix@10.46.1.165///home/nutanix/data/Bugs/MA/NCM/24_3_1_3/ENG-751855 -t msp -O run_all=true,msp_cluster_uuid=e769216c-5b06-4666-5471-bf16052de2d3 --duration=-100h