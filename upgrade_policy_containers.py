#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Anshuman Singh
# Created Date: Sun May 30 18:54:00 PDT 2021
# =============================================================================

import sys
import getopt
import paramiko
import logging
import time


logging.basicConfig(
    stream=sys.stdout, level=logging.INFO,
    format='%(levelname)s - %(message)s'
)


POLICY_IMAGE_URL = "http://10.40.64.33/GoldImages/Calm-Policy-Engine/docker/"
POLICY_VM_USER_NAME = "nutanix"
POLICY_VM_PASSWORD = "nutanix/4u"


class SSH:
    def __init__(self, policy_vm_ip, port=22):
        self.host = policy_vm_ip
        self.user = POLICY_VM_USER_NAME
        self.password = POLICY_VM_PASSWORD
        self.port = port
        self.client = self.create_ssh_handler()

    def create_ssh_handler(self, timeout=600):
        # Logging into policy vm
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            self.host, self.port, self.user, self.password, timeout=timeout
        )
        return ssh

    def execute(self, cmd):
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, get_pty=True)

            # Wait till to get output of command execution
            logging.debug("Waiting till command '{0}' gets executed ... ".format(cmd))

            while not (stdout.channel.closed and stderr.channel.closed):
                time.sleep(1)

            stdout = str(stdout.read())
            stderr = str(stderr.read())

            return stdin, stdout, stderr
        except Exception as exception:
            logging.error("Error during command {0} execution. Error is {1}".format(cmd, exception))
            self.client.close()


class Policy:
    def __init__(self, policy_vm, branch="master"):
        #self.branch = branch
        self.policy_image_url = POLICY_IMAGE_URL + str(branch) + "/policy.tar"
        self.policy_epsilon_image_url = POLICY_IMAGE_URL + str(branch) + "/policy-epsilon.tar"
        self.chronos_image_url = POLICY_IMAGE_URL + str(branch) + "/chronos.tar"
        self.policy_loc = "~/installer/policy"
        self.policy_epsilon_loc = "~/installer/policy-epsilon"
        self.chronos_loc = "~/installer/chronos"
        self.ssh_handler = SSH(policy_vm)

    def stop_policy_containers(self, container):
        logging.info("Stopping {0} container.".format(container))

        policy_containers_stop_script_path = {
            "policy": self.policy_loc + "/stop.sh",
            "policy-epsilon": self.policy_epsilon_loc + "/stop.sh",
            "chronos": self.chronos_loc + "/stop.sh"
        }

        # Execute command to stop container
        cmd = "sh " + policy_containers_stop_script_path.get(container)
        _, stdout, stderr = self.ssh_handler.execute(cmd)

        if not len(stdout):
            logging.error(stderr)
        else:
            logging.info("Stopped {0} container".format(container))

        return True, None

    def __remove_container(self, container):
        logging.info("Removing {0} container".format(container))

        # Execute command to remove container
        container_rm_cmd = "docker rm " + str(container)
        _, stdout, stderr = self.ssh_handler.execute(container_rm_cmd)

        if not len(stdout):
            logging.error(stderr)
        else:
            logging.info("Removed {0} container.".format(container))

        return True, None

    def __stop_and_remove_container(self, container):
        # Stop the container
        res, err = self.stop_policy_containers(container)
        if not res:
            return None, err

        # Remove the container
        res, err = self.__remove_container(container)
        if not res:
            return None, err

        return True, None

    def remove_containers(self, containers):
        """
        This routine will remove list of containers
        Args:
            containers(list): Container names / id
        """
        if not isinstance(containers, list):
            return None, "Containers {0} are not list type. Type is {1}".format(
                containers, type(containers)
            )

        for container in containers:
            res, err = self.__stop_and_remove_container(container)

            if not res:
                return None, err

        return True, None

    def __remove_image(self, image):
        logging.info("Removing {0} image".format(image))

        # Execute docker command to remove container
        image_rm_cmd = "docker rmi " + str(image)
        _, stdout, stderr = self.ssh_handler.execute(image_rm_cmd)

        if not len(stdout):
            logging.error(stderr)
        else:
            logging.info("Removed {0} image.".format(image))

        return True, None

    def remove_images(self, images):
        """
        This routine will remove list of images
        Args:
            images(list): Image names
        """
        for image in images:
            res, err = self.__remove_image(image)

            if not res:
                return None, err

        return True, None

    def __remove_policy_tar_file(self, path):
        logging.info("Removing {0} file".format(path))

        # Execute command to delete policy / policy-epsilon tar file
        cmd = "rm %s" % path
        self.ssh_handler.execute(cmd)

        logging.info("Removed {0} file".format(path))

        return True, None

    def remove_policy_tar_files(self):
        policy_tar_loc = {
            "policy": self.policy_loc + "/policy.tar",
            "policy-epsilon": self.policy_epsilon_loc + "/policy-epsilon.tar",
            "chronos": self.chronos_loc + "/chronos.tar"
        }

        for tar_file_path in policy_tar_loc.values():
            res, err = self.__remove_policy_tar_file(tar_file_path)

            if not res:
                return None, err

        return True, None

    def __install_wget_package(self):
        # Check whether wget package is installed or not in policy-vm machine
        cmd = "sudo yum list installed wget"
        _, stdout, _ = self.ssh_handler.execute(cmd)

        if not stdout.find("wget") != -1:
            # Install wget package on policy-vm machine
            logging.info("wget package is not installed on policy-vm. Installing it ... ")
            _, stdout, _ = self.ssh_handler.execute("yes | sudo yum install wget")

            if not (stdout.find("Complete") != -1):
                logging.error("wget package installation is failed. Error is: {0}".format(stdout))
                return None, stdout
        else:
            logging.debug("wget package is already installed")

        return True, None

    def download_tar_file(self, path, url):
        logging.info("Tar file {0} is downloading...".format(url))

        _, stdout, stderr = self.ssh_handler.execute("wget -P {0} {1}".format(str(path), str(url)))

        output_msg = stdout
        if not len(stdout):
            output_msg = stderr

        output_msg = "".join(output_msg)
        if not (output_msg and output_msg.find("saved") != -1):
            logging.error("{0} tar file download is failed. Error is {1}".format(path, output_msg))
            return None, "{0} tar file download is failed. Error is {1}".format(path, output_msg)
        else:
            logging.info("Tar file {0} is downloaded".format(url))

        return True, None

    def download_policy_tar_files(self):
        res, err = self.__install_wget_package()
        if not res:
            return None, err

        policy_image_url = {
            "policy": self.policy_image_url,
            "policy-epsilon": self.policy_epsilon_image_url,
            "chronos": self.chronos_image_url,
        }

        policy_tar_file_loc = {
            "policy": self.policy_loc,
            "policy-epsilon": self.policy_epsilon_loc,
            "chronos": self.chronos_loc,
        }

        for name, image_url in policy_image_url.items():
            res, err = self.download_tar_file(
                policy_tar_file_loc.get(name), image_url
            )

            if not res:
                return None, err

        return True, None

    def load_policy_image_from_tar(self):
        policy_tar_files = {
            "policy": self.policy_loc + "/policy.tar",
            "policy-epsilon": self.policy_epsilon_loc + "/policy-epsilon.tar",
            "chronos": self.chronos_loc + "/chronos.tar"
        }

        for tar_file_path in policy_tar_files.values():
            logging.info("Loading image from {}".format(tar_file_path))
            _, stdout, _ = self.ssh_handler.execute("docker load -i %s" % str(tar_file_path))

            if not (stdout.find("Loaded image") != -1):
                return None, "Loading image from tar file is failed for {0}. Error is: {1}".format(
                    tar_file_path, stdout
                )
            else:
                logging.info("Loaded image from {}".format(tar_file_path))

        return True, None

    def create_policy_containers(self):
        create_script_path = {
            "policy": self.policy_loc + "/create.sh",
            "policy-epsilon": self.policy_epsilon_loc + "/create.sh",
            "chronos": self.chronos_loc + "/create.sh"
        }

        for key, path in create_script_path.items():
            logging.info("Creating {} container".format(key))

            _, stdout, _ = self.ssh_handler.execute("sh %s" % str(path))

            if not (stdout.find("Created and started") != -1):
                return None, "Creating policy container is failed, {0}. Error is {1}".format(key, stdout)
            else:
                logging.info("Created {} container".format(key))

        return True, None

    def wait_till_policy_container_goes_to_healthy_state(self, timeout=300):
        create_action_timeout = time.time() + timeout

        policy_health_status = None
        policy_epsilon_health_status = None
        chronos_health_status = None

        while policy_health_status != "healthy" or policy_epsilon_health_status != "healthy" or chronos_health_status != "healthy":

            _, policy_stdout, _ = self.ssh_handler.execute(
                "docker inspect --format='{{json .State.Health.Status}}' policy"
            )
            _, policy_epsilon_stdout, policy_epsilon_stderr = self.ssh_handler.execute(
                "docker inspect --format='{{json .State.Health.Status}}' policy-epsilon"
            )
            _, chronos_stdout, chronos_stderr = self.ssh_handler.execute(
                "docker inspect --format='{{json .State.Health.Status}}' chronos"
            )
            policy_health_status = "healthy" if policy_stdout.find("healthy") != -1 else policy_stdout
            policy_epsilon_health_status = "healthy" if policy_epsilon_stdout.find("healthy") != -1 else \
                policy_epsilon_stdout
            chronos_health_status = "healthy" if chronos_stdout.find("healthy") != -1 else chronos_stdout

            logging.info("Current state of policy container: {0}".format(policy_health_status))
            logging.info("Current state of policy-epsilon container: {0}".format(policy_epsilon_health_status))
            logging.info("Current state of chronos container: {0}".format(chronos_health_status))

            if time.time() > create_action_timeout or \
                    (policy_health_status == "healthy" and policy_epsilon_health_status == "healthy" and chronos_health_status == "healthy"):
                break

            time.sleep(10)

        if policy_health_status == "healthy" and policy_epsilon_health_status == "healthy" and chronos_health_status == "healthy":
            return True, None
        else:
            return None, "Container are not in healthy state. Policy state: {0}, Policy-epsilon state: {1}, Chronos state: {2}".format(
                policy_health_status, policy_epsilon_health_status, chronos_health_status
            )

    def upgrade_container(self):
        try:
            print("\n=================================")
            print("Removing policy containers...")
            print("=================================\n")
            # Remove policy containers
            res, err = self.remove_containers(["policy", "policy-epsilon", "chronos"])
            if not res:
                return err

            print("\n=================================")
            print("Removing policy images...")
            print("=================================\n")
            # remove policy images
            res, err = self.remove_images(["policy", "policy-epsilon", "chronos"])
            if not res:
                return err

            # Remove the tar file.
            print("\n=================================")
            print("Removing policy tar files...")
            print("=================================\n")
            res, err = self.remove_policy_tar_files()
            if not res:
                return None, err

            # Download the tar file
            print("\n=================================")
            print("Downloading policy tar files...")
            print("=================================\n")
            res, err = self.download_policy_tar_files()
            if not res:
                return None, err

            # Load docker image from policy tar file
            print("\n=================================")
            print("Loading policy images...")
            print("=================================\n")
            res, err = self.load_policy_image_from_tar()
            if not res:
                return None, err

            # Start policy and policy-epsilon container
            print("\n=================================")
            print("Start policy containers...")
            print("=================================\n")
            res, err = self.create_policy_containers()
            if not res:
                return None, err

            # Wait till policy containers go to healthy state
            print("\n=================================")
            print("Waiting till policy containers go to healthy state ...")
            print("=================================\n")
            res, err = self.wait_till_policy_container_goes_to_healthy_state()
            if not res:
                return None, err

        finally:
            # Close the ssh session
            self.ssh_handler.client.close()

        if not res:
            return None, err
        else:
            return True, None

def usage():
    print("\nArguments should be: \n")
    print("python upgrade_policy_containers.py --branch=3.5.0 --policy-vm=\n")
    print("    policy-vm: Policy vm IP")
    print("    branch: Branch name (master / 3.3.0 / 3.2.0). Default is master")
    print("\n")

def main():
    # Options
    options = "hpb:"

    # Long options
    long_options = [
        "help",
        "policy-vm=",
        "branch=",
    ]

    policy_vm_ip = None
    branch_name = "master"

    try:
        # Parsing argument
        argumentList = sys.argv[1:]
        arguments, values = getopt.getopt(argumentList, options, long_options)

        if not len(arguments):
            usage()
            sys.exit(2)

        # checking each argument
        for arg_type, arg_val in arguments:
            if arg_type in ("--help", "-h"):
                usage()
                sys.exit(2)

            elif arg_type in ("--policy-vm", "-p"):
                policy_vm_ip = arg_val

            elif arg_type in ("--branch", "-b"):
                branch_name = arg_val

            else:
                usage()
                sys.exit(2)

    except Exception:
        usage()
        sys.exit(2)

    policy = Policy(policy_vm_ip, branch_name)
    try:
        res, err = policy.upgrade_container()

        if not res:
            logging.error("Policy container Upgradation is failed. Error is {0}".format(err))
        else:
            logging.info("\nPolicy container Upgradation is successful\n")
    except Exception as exception:
        logging.error("Policy container Upgradation is failed. Error is {0}".format(exception))

if __name__ == "__main__":
    main()
