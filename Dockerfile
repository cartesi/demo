FROM ubuntu:18.04

MAINTAINER Carlo Fragni<carlo@cartesi.io>

ENV BASE /opt/cartesi
ENV BLOCKCHAIN_INFO_DIR blockchain-node/exported-node-files
ENV GRPC_DIR machine-manager/machine-emulator/lib/grpc-interfaces

# Install basic development tools
# ----------------------------------------------------
RUN \
    apt-get update && \
    apt-get install --no-install-recommends -y \
        ca-certificates git build-essential make curl \
        software-properties-common python3 python3-pip \
        python3-setuptools python3-wheel

#Install node
SHELL ["/bin/bash", "-c"]
RUN \
    apt-get install -y gnupg-agent && \
    curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get install -y nodejs

# Copying python and node dependencies files
# ----------------------------------------------------
COPY requirements.txt package.json $BASE/

# Installing node dependencies
# ----------------------------------------------------
WORKDIR $BASE

RUN \
    npm install

# Installing python dependencies
# ----------------------------------------------------

RUN \
    pip3 install -r requirements.txt

# Copying source files
# ----------------------------------------------------
COPY dispatcher_config_generator.py initialize_machine.py mock_instances.js $BASE/
COPY $BLOCKCHAIN_INFO_DIR/step.add $BLOCKCHAIN_INFO_DIR/deployed_dispute_contracts.yaml $BLOCKCHAIN_INFO_DIR/ComputeInstantiator.json $BASE/$BLOCKCHAIN_INFO_DIR/
COPY $GRPC_DIR $BASE/$GRPC_DIR
COPY test-files $BASE/test-files

WORKDIR $BASE/$GRPC_DIR

# Generating grpc python files
# ----------------------------------------------------
RUN ./generate_python_grpc_code.sh

WORKDIR $BASE
