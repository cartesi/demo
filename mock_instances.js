#!/usr/bin/node

/*
Copyright 2019 Cartesi Pte. Ltd.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
*/

const os = require('os');
const Web3 = require('web3');
const fs = require('fs');
const yaml = require('js-yaml');
const program = require('commander');

const BLOCKCHAIN_INFO_DIR = "blockchain-node/exported-node-files";
const STEP_CONTRACT_ADD_FILENAME = BLOCKCHAIN_INFO_DIR + "/step.add";
const CONTRACTS_YAML_FILENAME = BLOCKCHAIN_INFO_DIR + "/deployed_dispute_contracts.yaml";
const COMPUTE_INSTANTIATOR_ABI_FILENAME = BLOCKCHAIN_INFO_DIR + "/ComputeInstantiator.json"
const initial_hash = "0xc7e2b1fbc7e499cca84d5bf8eb89a7e8c683e1605a7ebda9c3362fa491d556c8";
const TOTAL_NUMBER = 1;
const MAIN_ACCOUNT = "0x2ad38f50f38abc5cbcf175e1962293eecc7936de";
const SECOND_ACCOUNT = "0x8b5432ca3423f3c310eba126c1d15809c61aa0a9";

program
    .option('-e, --ethereum-node-url <url>', 'URL of ethereum node', 'http://127.0.0.1:8545')

program.parse(process.argv);

console.log("Connecting to " + program.ethereumNodeUrl);

var web3 = new Web3(program.ethereumNodeUrl, null,
                    {transactionConfirmationBlocks: 1});

const contracts_yaml = yaml.safeLoad(fs.readFileSync(CONTRACTS_YAML_FILENAME, 'utf-8'));

const sendRPC = function(web3, param){
  let web3Instance = web3
  return new Promise(function(resolve, reject) {
    web3Instance.currentProvider.send(param, function(err, data){
      if(err !== null) return reject(err);
      resolve(data);
    });
  });
}

var truffle_dump = fs.readFileSync(COMPUTE_INSTANTIATOR_ABI_FILENAME).toString('utf8');

abi = JSON.parse(truffle_dump).abi;

var machine_address =
    fs.readFileSync(STEP_CONTRACT_ADD_FILENAME)
    .toString('utf8');

var compute_address = null;
var compute_user = null;

for (const concern of contracts_yaml.concerns){
    if (concern.abi.includes("ComputeInstantiator.json")){
        compute_address = concern.contract_address;
        compute_user = concern.user_address;
    }
}

if (compute_address == null){
    throw "Couldn't get ComputeInstantiator contract address!";
}

var myContract = new web3.eth.Contract(
  abi,
  compute_address
);

let claimer, challenger, duration;

async function main() {
  let current_index = parseInt(
    await myContract.methods.currentIndex().call()
  );
  for (var i = current_index; i < current_index + TOTAL_NUMBER; i++) {
    console.log("Creating instance: " + i);
    if (i & 1) {
      claimer = MAIN_ACCOUNT;
      challenger = SECOND_ACCOUNT;
    } else {
      claimer = SECOND_ACCOUNT;
      challenger = MAIN_ACCOUNT;
    }
    if (i & 2) {
      final_time = 100000000;
    } else {
      final_time = 100000000;
    }
    if (i & 4) {
      round_duration = 50;
    } else {
      round_duration = 100000;
    }
    console.log("Instance " + i + " has:");
    console.log("  challenger: " + challenger);
    console.log("  claimer: " + claimer);
    console.log("  round_duration: " + round_duration);
    console.log("  machine_address: " + machine_address);
    console.log("  initial_hash: " + initial_hash);
    console.log("  final_time: " + final_time);

    await myContract.methods.instantiate(
      challenger,
      claimer,
      round_duration,
      machine_address,
      initial_hash,
      final_time,
    ).send({from: compute_user,
            gas: "3000000"});
    //  .then((receipt) => { console.log(receipt); });
  }
  let new_index = await myContract.methods.currentIndex().call()
  //response = await sendRPC(web3, { jsonrpc: "2.0",
  //                                 method: "evm_increaseTime",
  //                                 params: [100], id: Date.now() });
}

main();
