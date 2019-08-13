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
sys.path.insert(0,'machine-manager/machine-emulator/lib/grpc-interfaces/py')

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
DEFAULT_ADD = 'localhost:50051'

TEST_SESSION_ID = "test_new_session_id"
START = "start"
BACKING = "backing"
LENGTH = "length"
SHARED = "shared"
LABEL = "label"
BOOTARGS = "bootargs"

CONTAINER_SERVER = False

TEST_ROM = {
    BOOTARGS: "console=hvc0 rootfstype=ext2 root=/dev/mtdblock0 rw {} -- /bin/sh -c 'echo test && touch /mnt/output/test && cat /mnt/job/demo.sh && /mnt/job/demo.sh && echo test2' && cat /mnt/output/out",
    BACKING: "rom-linux.bin"
}

TEST_RAM = {
    LENGTH: 64 << 20, #2**26 or 67108864
    BACKING: "kernel.bin"
}

CONTAINER_BASE_PATH = "/root/host/"
NATIVE_BASE_PATH = "{}/test-files/".format(os.path.dirname(os.path.realpath(__file__)))
OUTPUT_DRIVE_NAME = "out"
PRISTINE_OUTPUT_DRIVE_NAME = "out_pristine.ext2"

DEBUG_STEP_FROM = None
DEBUG_STEP_FROM_FILENAME = "step_from_{}_output.json"
DEBUG_RUN_UP_TO = None
DEBUG_RUN_UP_TO_FILENAME = "run_up_to_{}_output.json"

def get_test_drives_config():
    return [
        {
            BACKING: "rootfs.ext2",
            SHARED: False,
            LABEL: "rootfs"
        },
        {
            BACKING: "input.ext2",
            SHARED: False,
            LABEL: "input"
        },
        {
            BACKING: "job.ext2",
            SHARED: False,
            LABEL: "job"
        },
        {
            BACKING: "{}.ext2".format(OUTPUT_DRIVE_NAME),
            #SHARED: True, #Must be False on verification game since the drive
            #contents don't follow the rollbacks and cartesi machine recreation
            #that happen during verification games
            SHARED: False,
            LABEL: "output"
        }
    ]


TEST_DRIVES = get_test_drives_config()

def build_mtdparts_str(drives):

    mtdparts_str = "mtdparts="

    for i,drive in enumerate(drives):
        mtdparts_str += "flash.%d:-(%s)".format(i, drive[LABEL])

    return mtdparts_str

def make_new_session_request():
    files_dir = NATIVE_BASE_PATH
    if (CONTAINER_SERVER):
        files_dir = CONTAINER_BASE_PATH

    drives_msg = []
    ram_msg = cartesi_base_pb2.RAM(length=TEST_RAM[LENGTH], backing=files_dir + TEST_RAM[BACKING])
    drive_start = 1 << 63
    for drive in TEST_DRIVES:
        drive_path = files_dir + drive[BACKING]
        drive_size = os.path.getsize(NATIVE_BASE_PATH + drive[BACKING])
        drive_msg = cartesi_base_pb2.Drive(start=drive_start, length=drive_size,
                                           backing=drive_path, shared=drive[SHARED])
        drives_msg.append(drive_msg)
        #New drive start is the next potency of 2 from drive_size, but must be
        #at least 1 MB
        new_drive_start = drive_start + int(max((2**(math.log(drive_size,2) - math.log(drive_size,2) % 1 + 1)), 1024*1024))
        print("Drive start: {}\nNew drive size: {}\nNew drive start: {}".format(drive_start, drive_size, new_drive_start))
        drive_start = new_drive_start

    bootargs_str = TEST_ROM[BOOTARGS].format(build_mtdparts_str(TEST_DRIVES))
    rom_msg = cartesi_base_pb2.ROM(bootargs=bootargs_str, backing=files_dir + TEST_ROM[BACKING])

    machine_msg = cartesi_base_pb2.MachineRequest(rom=rom_msg, ram=ram_msg, flash=drives_msg)
    return manager_high_pb2.NewSessionRequest(session_id=TEST_SESSION_ID, machine=machine_msg)

def positive_integer(num):
    try:
        int_num = int(num)
        if not(0 <= int_num):
            raise argparse.ArgumentTypeError("Please provide a valid positive value to step from ")
    except:
        raise argparse.ArgumentTypeError("Please provide a valid positive value to step from ")
    return int_num

def get_args():
    parser = argparse.ArgumentParser(description='GRPC client to the high level emulator API (machine manager)')
    parser.add_argument('--address', '-a', dest='address', default=DEFAULT_ADD, help="Machine manager GRPC server address")
    parser.add_argument('--container', '-c', action="store_true", dest="container_server", help="Machine manager GPRC server is running from docker container")
    parser.add_argument('--output_drive_name', '-o', dest="output_drive_name", help="Machine manager GPRC server is running from docker container")
    parser.add_argument('--debug_step_from', '-s', type=positive_integer, dest="debug_step_from", help="When set, this programs steps from the provided cycle number and dumps the GRPC output in json format to file")
    parser.add_argument('--debug_run_up_to', '-r', type=positive_integer, dest="debug_run_up_to", help="When set, this programs runs up to the provided cycle number and dumps the GRPC output in json format to file")
    parser.add_argument('--debug_step_from_dump_filename', '-sf', dest="debug_step_from_filename", help="Custom filename for step dump files")
    parser.add_argument('--debug_run_up_to_dump_filename', '-rf', dest="debug_run_up_to_filename", help="Custom filename for run dump files")
    parser.add_argument('--session_id', '-i', dest="session_id", help="Custom session id")

    args = parser.parse_args()

    global CONTAINER_SERVER
    global DEBUG_STEP_FROM
    global DEBUG_STEP_FROM_FILENAME
    global DEBUG_RUN_UP_TO
    global DEBUG_RUN_UP_TO_FILENAME
    global TEST_SESSION_ID
    global OUTPUT_DRIVE_NAME
    global TEST_DRIVES

    CONTAINER_SERVER = args.container_server

    if args.session_id:
        TEST_SESSION_ID = args.session_id

    if args.output_drive_name:
        OUTPUT_DRIVE_NAME = args.output_drive_name
        TEST_DRIVES = get_test_drives_config()

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

    return args.address

def make_output_fs_copy():
    files_dir = NATIVE_BASE_PATH
    if (CONTAINER_SERVER):
        files_dir = CONTAINER_BASE_PATH

    cp_proc = subprocess.Popen(["cp", NATIVE_BASE_PATH + PRISTINE_OUTPUT_DRIVE_NAME, NATIVE_BASE_PATH + OUTPUT_DRIVE_NAME + '.ext2'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = cp_proc.communicate()

    if (cp_proc.returncode):
        print("Failed to copy inout.ext2")
        sys.exit(1)

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

        #Putting the access log data structure inside a list to conform to the format expected by the programs that consume this log
        access_log_dict['accesses'].append(access_dict)

    json_dump = json.dumps([access_log_dict], indent=4, sort_keys=True)

    with open(DEBUG_STEP_FROM_FILENAME, 'w') as dump_file:
        dump_file.write(json_dump)

def run():
    responses = []
    srv_add = get_args()
    make_output_fs_copy()
    print("Connecting to server in " + srv_add)
    with grpc.insecure_channel(srv_add) as channel:
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
