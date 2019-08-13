"""
Copyright 2019 Cartesi Pte. Ltd.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

import sys
import yaml
import argparse
import binascii
import subprocess
import traceback

BASE_CONFIG_FILE = "base_dispatcher_config.yaml"
CONTRACTS_DEPLOYMENT_INFO_FILE = "blockchain-node/exported-node-files/deployed_dispute_contracts.yaml"
OUTPUT_CONFIG_FILE = "dispatcher_config.yaml"
BASE_ABI_PATH = "/opt/cartesi/blockchain/abis/"
DOCKERIZED_ADD_DIR = "/root/host"
USER_ADD = None
OVERRIDE_BLOCKCHAIN_NODE = False
OVERRIDE_WORKING_MM = False
OVERRIDE_DEFECTIVE_MM = False
DOCKERIZED = False

def address(add_str):
    try:
        test_str = add_str
        if (add_str[0:2] == "0x"):
            test_str = add_str[2:]
        else:
            add_str = "0x" + add_str
        binascii.unhexlify(test_str)
        return add_str
    except:
        raise argparse.ArgumentTypeError("Please provide a valid 64-characters long hexadecimal address")

def get_args():
    parser = argparse.ArgumentParser(description='Simple cli program to dynamically generate the dispatcher configuration file by merging a base config file with another file that contains contracts addresses, user addresses and abi references')
    parser.add_argument('--base_config_file', '-b', dest='base_config_file', help="Specify the name of the dispatcher base config file to use (Default: base_dispatcher_config.yaml)")
    parser.add_argument('--output_config_file', '-o', dest='output_config_file', help="Specify the output name of the dispatcher config file (Default: dispatcher_config.yaml)")
    parser.add_argument('--user_address', '-ua', type=address, dest='user_add', help="User address to override the ones provided in deployed_dispute_contracts.yaml file")
    set_machine_manager_parser = parser.add_mutually_exclusive_group(required=False)
    set_machine_manager_parser.add_argument('--working_machine_manager', '-wmm', dest='working_mm', action='store_true', default=False, help="Override emulator address to point to the working machine manager (Default: False)")
    set_machine_manager_parser.add_argument('--defective_machine_manager', '-dmm', dest='defective_mm', action='store_true', default=False, help="Override emulator address to point to the defective machine manager (Default: False)")
    parser.add_argument('--override_blockchain_node', '-obn', dest='override_bn', action='store_true', default=False, help="Override the blockchain node address. Should only be used with the bundled ganache-based docker container (Default: False)")
    parser.add_argument('--dockerized', '-d', dest='dockerized', action='store_true', default=False, help="Specify that this app is being execute within a docker container (Default: False)")


    args = parser.parse_args()

    global BASE_CONFIG_FILE
    global OUTPUT_CONFIG_FILE
    global USER_ADD
    global OVERRIDE_BLOCKCHAIN_NODE
    global OVERRIDE_WORKING_MM
    global OVERRIDE_DEFECTIVE_MM
    global DOCKERIZED

    if args.dockerized:
        DOCKERIZED = True

    if args.base_config_file:
        BASE_CONFIG_FILE = args.base_config_file

    if args.output_config_file:
        OUTPUT_CONFIG_FILE = args.output_config_file

    if (args.user_add != None):
        USER_ADD = args.user_add

    if (args.working_mm):
        OVERRIDE_WORKING_MM = True

    if (args.defective_mm):
        OVERRIDE_DEFECTIVE_MM = True

    if (args.override_bn):
        OVERRIDE_BLOCKCHAIN_NODE = True

def replace_deployed_info_in_base_config(conf_yaml, dep_info_yaml):
    conf_yaml['concerns']=[]

    for concern in dep_info_yaml['concerns']:
        replaced_concern = {}

        if USER_ADD:
            replaced_concern['user_address'] = USER_ADD
        else:
            replaced_concern['user_address'] = concern['user_address']
        replaced_concern['contract_address'] = concern['contract_address']

        abi_name = concern['abi'].split('/')[-1]
        replaced_concern['abi'] = BASE_ABI_PATH + abi_name

        #Checking if it is the main concern or not
        if abi_name == "ComputeInstantiator.json":
            conf_yaml['main_concern'] = replaced_concern
        else:
            conf_yaml['concerns'].append(replaced_concern)
    return conf_yaml

def replace_docker_addresses(conf_yaml):
    if OVERRIDE_BLOCKCHAIN_NODE:
        conf_yaml['url'] = "http://{}:8545".format(get_container_ip_address('ephemeral-cartesi-blockchain-node'))

    if OVERRIDE_WORKING_MM:
        conf_yaml['emulator_transport']['address'] = "{}".format(get_container_ip_address('ephemeral-machine-manager'))

    if OVERRIDE_DEFECTIVE_MM:
        conf_yaml['emulator_transport']['address'] = "{}".format(get_container_ip_address('ephemeral-defective-machine-manager'))

    return conf_yaml

def get_container_ip_address(container_name):

    add = ""

    #Making docker inspect command or dig depending on whether running from docker container
    if DOCKERIZED:
        cmd_line = ["cat", "{}/{}.add".format(DOCKERIZED_ADD_DIR, container_name)]
    else:
        cmd_line = ["docker", "inspect", "-f", "'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'", container_name]

    try:
        print("Executing: {}".format(' '.join(cmd_line)))
        #Running docker inspect command to recover container address
        proc = subprocess.Popen(cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out, err = proc.communicate()

        if (proc.returncode == 0):
            add = out.decode("utf-8").strip()
            if not DOCKERIZED:
                add = add[1:-1]
            print("Output for inspecting {} container address: {}".format(container_name, add))

        else:
            print("Error inspecting {} container address:".format(container_name))
            print("Stdout:{}\n\n".format(out.decode("utf-8")))
            print("Stderr:{}\n\n".format(err.decode("utf-8")))

    except Exception as e:
        print("An error ocurred when trying to recover the docker cointaner address for container {}".format(container_name))
        print(traceback.format_exc())
        sys.exit(1)

    return add

def load_contracts_deployment_info():
    with open(CONTRACTS_DEPLOYMENT_INFO_FILE, 'r') as contracts_deployment_info_file:
        try:
            return yaml.safe_load(contracts_deployment_info_file)
        except yaml.YAMLError as exc:
            print("Error trying to load contracts deployment info yaml:")
            print(exc)
            sys.exit(1)

def write_dynamic_confs(conf_yaml):
    #Loading yaml with contracts deployment information
    dep_info_yaml = load_contracts_deployment_info()

    #Replacing that information
    conf_yaml = replace_deployed_info_in_base_config(conf_yaml, dep_info_yaml)

    #Replacing blockchain node and machine emulator containers address if required to
    conf_yaml = replace_docker_addresses(conf_yaml)
    return conf_yaml

get_args()

loaded_yaml = None
custom_yaml = None

with open(BASE_CONFIG_FILE, 'r') as base_yaml_file:
    try:
        loaded_yaml = yaml.safe_load(base_yaml_file)
    except yaml.YAMLError as exc:
        print("Error trying to load yaml base configuration:")
        print(exc)
        sys.exit(1)

    custom_yaml = write_dynamic_confs(loaded_yaml)

    print("Dumping final configuration to file:\n{}".format(yaml.dump(custom_yaml, default_flow_style=False)))

    with open(OUTPUT_CONFIG_FILE, 'w') as custom_yaml_file:
        yaml.dump(custom_yaml, custom_yaml_file, default_flow_style=False)

