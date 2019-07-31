#!/usr/bin/env bash

ORIGINAL_DIR=`pwd`
BASE_DIR=${0%/*}

#Going to script directory
cd $BASE_DIR

#Download and unzip test-files
mkdir -p test-files && wget https://www.dropbox.com/sh/xrs5glzbzb29jto/AABHue6i6Po6wMCIeRQvxzmxa?dl=1 -O test-files/test-files.zip && unzip -o test-files/test-files.zip -d test-files -x / && rm test-files/test-files.zip

#Buid blockchain-node image
cd blockchain-node && ./build_cartesi_blockchain_node_image.sh && cd ..

#Build emulator and machine-manager image
cd machine-manager && ./build_image_emulator_base.sh && ./build_machine_manager_image.sh && cd ..

#Build compute-image
cd arbitration-dlib && ./build_compute_test_image_dev.sh && cd ..

#Return to original dir
cd $ORIGINAL_DIR
