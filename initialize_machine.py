from __future__ import print_function

import grpc
import sys
import os
import time
import datetime

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

TEST_ROM = {
    BACKING: "rom.bin"
}

TEST_RAM = {
    LENGTH: 1 << 20,
}

CONTAINER_BASE_PATH = "/root/host/"
NATIVE_BASE_PATH = "{}/test-files/".format(os.path.dirname(os.path.realpath(__file__)))

def make_new_session_request():
    files_dir = NATIVE_BASE_PATH
    if (CONTAINER_SERVER):
        files_dir = CONTAINER_BASE_PATH

    rom_msg = cartesi_base_pb2.ROM(backing=files_dir + TEST_ROM[BACKING])
    ram_msg = cartesi_base_pb2.RAM(length=TEST_RAM[LENGTH])

    machine_msg = cartesi_base_pb2.MachineRequest(rom=rom_msg, ram=ram_msg)
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

def get_args():
    parser = argparse.ArgumentParser(description='GRPC client to the high level emulator API (core manager)')
    parser.add_argument('--address', '-a', type=address, dest='address', default=DEFAULT_ADD, help="Core manager GRPC server address")
    parser.add_argument('--port', '-p', type=port_number, dest='port', default=DEFAULT_PORT, help="Core manager GRPC server port")
    parser.add_argument('--container', '-c', action="store_true", dest="container_server", help="Core manager GPRC server is running from docker container")
    args = parser.parse_args()

    global CONTAINER_SERVER
    CONTAINER_SERVER = args.container_server

    return (args.address, args.port)

def run():
    responses = []
    srv_add, srv_port = get_args()
    conn_str = "{}:{}".format(srv_add, srv_port)
    print("Connecting to server in " + conn_str)
    with grpc.insecure_channel(conn_str) as channel:
        stub_low = manager_low_pb2_grpc.MachineManagerLowStub(channel)
        stub_high = manager_high_pb2_grpc.MachineManagerHighStub(channel)
        stub_high_defective = manager_high_pb2_grpc.MachineManagerHighStub(channel)
        try:
            #NEW SESSION
            print("\n\n\nNEW SESSION TESTS\n\n\n")

            #Test new session
            print("Asking to create a new session")
            print("Server response:\n{}".format(stub_high.NewSession(make_new_session_request())))

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
