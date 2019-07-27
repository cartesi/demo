import sys
import yaml
import argparse
import binascii

BASE_CONFIG_FILE = "base_dispatcher_config.yaml"
CONTRACTS_DEPLOYMENT_INFO_FILE = "deployed_dispute_contracts.yaml"
OUTPUT_CONFIG_FILE = "dispatcher_config.yaml"
BASE_ABI_PATH = "/opt/cartesi/blockchain/abis/"
USER_ADD = None

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

    args = parser.parse_args()

    global BASE_CONFIG_FILE
    global OUTPUT_CONFIG_FILE
    global USER_ADD

    if args.base_config_file:
        BASE_CONFIG_FILE = args.base_config_file

    if args.output_config_file:
        OUTPUT_CONFIG_FILE = args.output_config_file

    if (args.user_add != None):
        USER_ADD = args.user_add

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

def load_contracts_deployment_info():
    with open(CONTRACTS_DEPLOYMENT_INFO_FILE, 'r') as contracts_deployment_info_file:
        try:
            return yaml.safe_load(contracts_deployment_info_file)
        except yaml.YAMLError as exc:
            print("Error trying to load contracts deployment info yaml:")
            print(exc)
            sys.exit(1)

def write_dynamic_confs(conf_yaml):
    dep_info_yaml = load_contracts_deployment_info()
    return replace_deployed_info_in_base_config(conf_yaml, dep_info_yaml)

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

