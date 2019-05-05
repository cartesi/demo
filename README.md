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

Make this specific version the default

    rustup default nightly-2018-12-23

To be able to use other versions, one needs to either remove `futures-await` or wait for this PR

    https://github.com/alexcrichton/futures-await/pull/112

## Install infrastructure

Follow the instructions in the README.md file.

## Contracts

Just

    cd
    git clone --recurse-submodules git@github.com:cartesi/contracts.git

Install npm, but don't let it uninstall `libssl-dev`.
If this does not work

    sudo apt-get install npm

Try

    curl -L https://www.npmjs.com/install.sh | sh

Intall dependencies

    cd contracts
    npm install

Compile them

    ./node_modules/.bin/truffle compile

## Watcher

Install virtualenv

    sudo apt-get install virtualenv

In the infrastructure folder, create a virtual environment, activate it and install dependencies

    virtualenv vir
    . ./vir/bin/activate
    pip install -r requirements.txt

## RISC-V solidity

Download it::

   git clone git@github.com/cartesi/riscv-solidity.git

Follow the instructions in the `README.md` file.

## Install demo dependencies

Node stuff

    npm install

Pythons3 stuff

    sudo apt install python3-venv
    python3 -m venv vir
    pip install -r requirements.txt

Deactivate with `deactivate` and reactivate again with `workon vir`.

    git submodule update --init --recursive
