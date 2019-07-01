from __future__ import print_function

import math
import grpc
import sys
import os
import time
import datetime
import subprocess

#So the cartesi GRPC modules are in path
import sys
sys.path.insert(0,'core-manager/cartesi-grpc/py')

import core_pb2
import cartesi_base_pb2
import core_pb2_grpc
import manager_high_pb2
import manager_high_pb2_grpc
import manager_low_pb2
import manager_low_pb2_grpc
import traceback
import json
import argparse
#from IPython import embed

SLEEP_TIME = 5
DEFAULT_PORT = 50051
DEFAULT_ADD = 'localhost'

TEST_SESSION_ID = "test_new_session_id"
START = "start"
BACKING = "backing"
LENGTH = "length"
SHARED = "shared"
LABEL = "label"
BOOTARGS = "bootargs"

CONTAINER_SERVER = False

TEST_RAM = {
    LENGTH: 1 << 20,
    BACKING: "kernel.bin"
}

CONTAINER_BASE_PATH = "/root/host/"
NATIVE_BASE_PATH = "{}/test-files/".format(os.path.dirname(os.path.realpath(__file__)))

DEBUG_STEP_FROM = None
DEBUG_STEP_FROM_FILENAME = "step_from_{}_output.json"
DEBUG_RUN_UP_TO = None
DEBUG_RUN_UP_TO_FILENAME = "run_up_to_{}_output.json"

def make_new_session_request():
    files_dir = NATIVE_BASE_PATH
    if (CONTAINER_SERVER):
        files_dir = CONTAINER_BASE_PATH
    ram_msg = cartesi_base_pb2.RAM(length=TEST_RAM[LENGTH], backing=files_dir + TEST_RAM[BACKING])
    machine_msg = cartesi_base_pb2.MachineRequest(ram=ram_msg)
    return manager_high_pb2.NewSessionRequest(session_id=TEST_SESSION_ID, machine=machine_msg)

def address(add):
    #TODO: validate address
    return add

def port_number(port):
    try:
        int_port = int(port)
        if not(0 <= int_port <= 65535):
            raise argparse.ArgumentTypeError("Please provide a valid port from 0 to 65535")
    except:
        raise argparse.ArgumentTypeError("Please provide a valid port from 0 to 65535")
    return port

def positive_integer(num):
    try:
        int_num = int(num)
        if not(0 <= int_num):
            raise argparse.ArgumentTypeError("Please provide a valid positive value to step from ")
    except:
        raise argparse.ArgumentTypeError("Please provide a valid positive value to step from ")
    return int_num

def get_args():
    parser = argparse.ArgumentParser(description='GRPC client to the high level emulator API (core manager)')
    parser.add_argument('--address', '-a', type=address, dest='address', default=DEFAULT_ADD, help="Core manager GRPC server address")
    parser.add_argument('--port', '-p', type=port_number, dest='port', default=DEFAULT_PORT, help="Core manager GRPC server port")
    parser.add_argument('--container', '-c', action="store_true", dest="container_server", help="Core manager GPRC server is running from docker container")
    parser.add_argument('--debug_step_from', '-s', type=positive_integer, dest="debug_step_from", help="When set, this programs steps from the provided cycle number and dumps the GRPC output in json format to file")
    parser.add_argument('--debug_run_up_to', '-r', type=positive_integer, dest="debug_run_up_to", help="When set, this programs runs up to the provided cycle number and dumps the GRPC output in json format to file")
    parser.add_argument('--debug_step_from_dump_filename', '-sf', dest="debug_step_from_filename", help="Custom filename for step dump files")
    parser.add_argument('--debug_run_up_to_dump_filename', '-rf', dest="debug_run_up_to_filename", help="Custom filename for run dump files")
    parser.add_argument('--session_id', '-i', dest="session_id", help="Custom session id")
    parser.add_argument('--ram_backing', '-rb', dest="ram_backing", help="file to use as RAM backing")

    args = parser.parse_args()

    global CONTAINER_SERVER
    global DEBUG_STEP_FROM
    global DEBUG_STEP_FROM_FILENAME
    global DEBUG_RUN_UP_TO
    global DEBUG_RUN_UP_TO_FILENAME
    global TEST_SESSION_ID
    global TEST_RAM
    
    CONTAINER_SERVER = args.container_server

    if args.ram_backing:
        TEST_RAM[BACKING] = args.ram_backing
    
    if args.session_id:        
        TEST_SESSION_ID = args.session_id

    if (args.debug_step_from != None):
        DEBUG_STEP_FROM = args.debug_step_from
                
        if (args.debug_step_from_filename != None):
            DEBUG_STEP_FROM_FILENAME = args.debug_step_from_filename
        else:
            DEBUG_STEP_FROM_FILENAME = DEBUG_STEP_FROM_FILENAME.format(DEBUG_STEP_FROM)

    if (args.debug_run_up_to != None):   
        DEBUG_RUN_UP_TO = args.debug_run_up_to
        
        if (args.debug_run_up_to_filename != None):
            DEBUG_RUN_UP_TO_FILENAME = args.debug_run_up_to_filename
        else:
            DEBUG_RUN_UP_TO_FILENAME = DEBUG_RUN_UP_TO_FILENAME.format(DEBUG_RUN_UP_TO)
            
    return (args.address, args.port)

def dump_run_response_to_file(run_resp):
    resp_dict = {"summaries": [], "hashes": []}

    for val in run_resp.summaries:
        resp_dict["summaries"].append({
                                          'tohost': val.tohost,
                                          'mcycle': val.mcycle
                                      })
    for val in run_resp.hashes:
        resp_dict["hashes"].append("{}".format(val.content.hex()))

    json_dump = json.dumps(resp_dict, indent=4, sort_keys=True)

    with open(DEBUG_RUN_UP_TO_FILENAME, 'w') as dump_file:
        dump_file.write(json_dump)

def dump_step_response_to_file(access_log):

    access_log_dict = {'accesses':[], 'notes':[], 'brackets':[]}

    for note in access_log.log.notes:
        access_log_dict['notes'].append(note)

    for bracket in access_log.log.brackets:
        access_log_dict['brackets'].append(
                {
                    'type':
                    cartesi_base_pb2._BRACKETNOTE_BRACKETNOTETYPE.values_by_number[bracket.type].name,
                    'where': bracket.where,
                    'text' : bracket.text
                })

    for access in access_log.log.accesses:
        access_dict = {
                    'read': "{}".format(access.read.content.hex()),
                    'written' : "{}".format(access.written.content.hex()),
                    'operation' : cartesi_base_pb2._ACCESSOPERATION.values_by_number[access.operation].name,
                    'proof' : {
                            'address': access.proof.address,
                            'log2_size': access.proof.log2_size,
                            'target_hash': "{}".format(access.proof.target_hash.content.hex()),
                            'root_hash': "{}".format(access.proof.root_hash.content.hex()),
                            'sibling_hashes' : []
                        }
                }

        for sibling in access.proof.sibling_hashes:
            access_dict['proof']['sibling_hashes'].append("{}".format(sibling.content.hex()))

        access_log_dict['accesses'].append(access_dict)

    #Putting the access log data structure inside a list to conform to the format expected by the programs that consume this log
    json_dump = json.dumps([access_log_dict], indent=4, sort_keys=True)

    with open(DEBUG_STEP_FROM_FILENAME, 'w') as dump_file:
        dump_file.write(json_dump)

def run():
    responses = []
    srv_add, srv_port = get_args() 
    conn_str = "{}:{}".format(srv_add, srv_port)
    print("Connecting to server in " + conn_str)
    with grpc.insecure_channel(conn_str) as channel:
        stub_low = manager_low_pb2_grpc.MachineManagerLowStub(channel)
        stub_high = manager_high_pb2_grpc.MachineManagerHighStub(channel)
        try:
            #NEW SESSION
            print("\n\n\nNEW SESSION TESTS\n\n\n")

            #Test new session
            print("Asking to create a new session")
            response = stub_high.NewSession(make_new_session_request())
            print("Server response:\n{}".format(response))
            print("Initial hash in hex: 0x{}".format(response.content.hex()))
            if (DEBUG_RUN_UP_TO != None):
                print("Running up to {}".format(DEBUG_RUN_UP_TO))
                final_cycles = [DEBUG_RUN_UP_TO]
                run_req = manager_high_pb2.SessionRunRequest(session_id=TEST_SESSION_ID, final_cycles=final_cycles)
                run_resp = stub_high.SessionRun(run_req)
                print("Server response from run:\n{}".format(run_resp))
                dump_run_response_to_file(run_resp)
                print(run_resp.hashes[0].content.hex())
            if (DEBUG_STEP_FROM != None):
                print("Stepping from {}".format(DEBUG_STEP_FROM))
                step_req = manager_high_pb2.SessionStepRequest(session_id=TEST_SESSION_ID, initial_cycle=DEBUG_STEP_FROM)
                step_resp = stub_high.SessionStep(step_req)
                print("Server response from step:\n{}".format(step_resp))
                dump_step_response_to_file(step_resp)
            #embed()
        except Exception as e:
            print("An exception occurred:")
            print(e)
            print(type(e))

if __name__ == '__main__':
    start = time.time()
    print("Starting at {}".format(time.ctime()))
    run()
    print("Ending at {}".format(time.ctime()))
    delta = time.time() - start
    print("Took {} seconds to execute".format(datetime.timedelta(seconds=delta)))
