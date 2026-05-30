# Disclaimer: Usage of this tool must be under the guidance of Nutanix Support or an authorized partner
# Summary: This file contains code to resume collection for all endpoints.
# It calls the perfmon API /api/aiops/v4.r0.a1/perfmon/target/instance/$actions/resume and waits for the task to complete.
# Version of the script: Version 1
# Compatible software version(s): NCM 1.5
# Steps to run:
# 1. Copy the script to /home/nutanix/bin directory
# 2. Run the script using the command: python3 resume_endpoints.py
# 3. You can optionally define logfile path using the flag --logfile=<log_file_path>
# Copyright (c) 2025 Nutanix Inc. All rights reserved.
# Authors: arpit.gupta@nutanix.com



import os
import sys
import time
import base64
import getpass

VIRTUALENV_PATH = "/home/nutanix/cluster/.venv/bin/bin/python3.9"
if os.path.exists(VIRTUALENV_PATH):
    if os.environ.get("PYTHON_TARGET_VERSION") is None:
        os.environ["PYTHON_TARGET_VERSION"] = "3.9"
    if os.environ.get("PYTHON_TARGET_PATH") is None:
        os.environ["PYTHON_TARGET_PATH"] = VIRTUALENV_PATH

import env

import json
import gflags
import urllib.request
import urllib.parse

import util.base.log as log

gflags.DEFINE_string(
    "resume_logfile",
    "/home/nutanix/data/logs/resume_endpoints.log",
    "Log file for resume password script logs.",
)


FLAGS = gflags.FLAGS

USERNAME = ""
PASSWORD = ""
NC_FQDN = ""

STATE_SUCCEEDED = "SUCCEEDED"
STATE_FAILED = "FAILED"


def make_request(url, method="GET", data=None):
    import ssl

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req_body = urllib.parse.urlencode(data) if data else None
    req = None
    if req_body:
        req = urllib.request.Request(url, method=method, data=req_body.encode())
    else:
        req = urllib.request.Request(url, method=method)

    req.add_header("Content-Type", "application/json")
    auth_header = base64.b64encode(bytes(f"{USERNAME}:{PASSWORD}".encode("utf-8")))
    req.add_header("Authorization", f"Basic {auth_header.decode('utf-8')}")
    res = urllib.request.urlopen(req, context=ctx)
    body = res.read()
    json_body = json.loads(body)
    return json_body


def main():
    global USERNAME, PASSWORD, NC_FQDN
    USERNAME = input("nc username: ")
    PASSWORD = getpass.getpass("nc password: ")
    NC_FQDN = input("nc fqdn: ")

    try:
        url = f"https://ncm.services.{NC_FQDN}/api/aiops/v4.r0.a1/perfmon/target/instance/$actions/resume"
        print(f"resuming all endpoints, url: {url}")
        resp = make_request(url, method="POST", data={})
        task_id = resp.get("task_uuid")
        log.INFO(f"task id: {task_id}")

        success, error = poll_task(task_id)

        if success:
            print("successfully resumed all endpoints")
        else:
            print(f"task to resume endpoints failed, {error} \n\n Please contact Nutanix Support")
    except Exception as e:
        print(f"failed to resume all endpoints, Please contact Nutanix Support")
        log.ERROR(f"failed to call perfmon API to resume endpoint, err: {e}")


def poll_task(task_id):
    url = f"https://ncm.services.{NC_FQDN}/api/prism/v4.0/config/tasks/ZXJnb24=:{task_id}"
    print(f"polling task url: {url}")
    done = False
    status = False
    res = {}

    try:
        while not done:
            print(f"polling task ...")
            res = make_request(url, method="GET")
            data = res.get("data")
            status = data.get("status")
            done = status == STATE_SUCCEEDED or status == STATE_FAILED
            if not done:
                time.sleep(10)
            # maybe if failed then read the error message and throw it as exception
    except Exception as e:
        log.ERROR("failed to poll task, %s" % e)
        return False, e

    return done, None


if __name__ == "__main__":
    try:
        FLAGS(sys.argv)
        log.initialize(FLAGS.resume_logfile)
        main()
    except Exception as ex:
        print("Exception : %s" % ex)
        sys.exit(1)