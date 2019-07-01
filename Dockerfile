FROM ubuntu:18.04

MAINTAINER Carlo Fragni<carlo@cartesi.io>

ENV BASE /opt/cartesi

# Install basic development tools
# ----------------------------------------------------
RUN \
    apt-get update && \
    apt-get install --no-install-recommends -y \
        ca-certificates git build-essential make curl software-properties-common python3

#Install node
SHELL ["/bin/bash", "-c"]
RUN \
    apt-get install -y gnupg-agent && \
    curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get install -y nodejs

# Copying source files
# ----------------------------------------------------
COPY . $BASE

# Installing node dependencies
# ----------------------------------------------------
WORKDIR $BASE

RUN \
    npm install

# Installing python dependencies
# ----------------------------------------------------

RUN \
    pip3 install -r requirements.txt

#Exporting some needed files to interact with the
#deployed contracts and running ganache from saved state
# ----------------------------------------------------
#CMD \
#    cp deployed_dispute_contracts.yaml /root/host && \
#    cp step.add /root/host && \
#    cp mm.add /root/host && \
#    cp /opt/cartesi-node/contracts/build/contracts/ComputeInstantiator.json /root/host && \
#    cp /opt/cartesi-node/contracts/build/contracts/VGInstantiator.json /root/host && \
#    cp /opt/cartesi-node/contracts/build/contracts/MMInstantiator.json /root/host && \
#    cp /opt/cartesi-node/contracts/build/contracts/PartitionInstantiator.json /root/host && \
#    riscv-solidity/node_modules/.bin/ganache-cli --db=$GANACHE_DB_DIR -l 9007199254740991 --allowUnlimitedContractSize -e 200000000 -i=7777 -d --mnemonic="mixed bless goat recipe urban pair tuna diet drive capable normal action"

