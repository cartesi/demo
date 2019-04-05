# core-demo

## Install core-manager through Docker

Install

    sudo apt-get install docker.io

Add your user to docker group

    sudo addgroup augusto docker

Clone cartesi repos

    git clone --recurse-submodules git@github.com:cartesi/core-manager.git
    git clone git@github.com:cartesi/image-ci.git

Build the image

    docker build -t image-ci .

Run the image

    docker run -v ~/core-manager:/root/host --name emulator image-ci

From now on, run it with

    docker start emulator
    docker exec -it emulator bash

Enter the right folder inside the container

    cd /root/host/coer/src/emulator
    make clean
    make grpc

## Install rust nightly


There are instructions on the internet, building or `curl | sh`

    curl -f -L https://static.rust-lang.org/rustup.sh -O
    sh rustup.sh --default-toolchain=nightly

Add cargo to your path in `.bashrc`

    export PATH=$PATH:/home/augusto/.cargo/bin

## Install infrastructure

Follow the instructions in the README.md file.

## Clone contract's repo

Just

    git clone --recurse-submodules git@github.com:cartesi/contracts.git




