> :warning: The Cartesi team keeps working internally on the next version of this repository, following its regular development roadmap. Whenever there's a new version ready or important fix, these are published to the public source tree as new releases.

# Cartesi Demo

The Cartesi Demo is a showcase for a simple dapp that uses all Cartesi Modules. It consists of a very simple dapp that triggers a Verification Game (VG) between two parties (Alice and Bob). Alice disputes Bob's result for the demo dapp execution and runs the dapp correctly. Bob, on the other hand, simulates a party that is not behaving correctly and executes the dapp in a defective environment in which the clock of the Cartesi Machine saturates at a determined cycle.

This repository contains everything that is needed to generate docker images for all the Cartesi Modules and two high level scripts to build everything from scratch and run the demo.

## Getting Started

### Requirements

- Docker >= 18.09
- Byobu >= 5.127
- Wget
- Unzip

### Clone the repository with submodules

```bash
$ git clone --recursive git@github.com:cartesi/demo.git
```

### Enter the directory and execute the demo preparation script

```bash
$ cd demo
$ ./prepare_demo.sh
```

This script builds multiple docker images so it takes a while to complete

### Run the deploy script that triggers the demo inside byobu

```bash
$ byobu
$./deploy
```

From here the script spawns multiple terminal windows and starts:

- A Cartesi contracts enabled ganache instance
- Two machine managers (one for Alice and another for Bob)
- Two compute nodes (one for Alice and another for Bob)
- The simple demo dapp scripts that trigger the Cartesi Machine of the sample computation for Alice and Bob and the Verification Game dispute

The demo ends when the Verification Game is concluded and arbitrates Alice as the winner.

## Under the hood

​	In this section we further detail what's going on as a whole and under each module during the preparation and execution of the demo.

​	The prepare_demo.sh script automates most of the time consuming preparation tasks needed to execute the demo:

- Downloads binaries of the ROM, kernel and flash drives (root file system and additional input/output drives) used by the demo dapp (the kernel, ROM and root file system can be made from scratch using the [machine-emulator-sdk repository](https://github.com/cartesi/machine-emulator-sdk] ) and the additional flash drives using your preferred file system generation/manipulation tools, like e2tools for ext2).
- Builds the [blockchain-node docker image](https://github.com/cartesi/blockchain-node) which contains a Ganache ethereum blockchain node for development/testing purposes. During the build of this image, the necessary smart contracts for the Cartesi environment are deployed in the Ganache personal ethereum blockchain: the on-chain Cartesi Machine smart contacts ([machine-solidity-step](https://github.com/cartesi/machine-solidity-step)) and the arbitration smart contracts ([arbitration-dlib](https://github.com/cartesi/arbitration-dlib)), including those that implement the on-chain part of the Verification Game.
- Builds the image that contains the [machine-manager server](https://github.com/cartesi/machine-manager) and the [machine-emulator](https://github.com/cartesi/machine-emulator). The machine-manager server has a high level GRPC API to create and interact with machine-emulator sessions while the machine-emulator is a Cartesi Machine specification compliant implementation.
- Builds the compute image (also located in the [arbitration-dlib repository](https://github.com/cartesi/arbitration-dlib)) that contains a service responsible for watching the blockchain for events that a party should react to and triggering the reactions (like engaging in a Verification Game and reacting to the other party actions during a Verification Game).

​	The deploy script starts all the Cartesi modules for two parties (Alice and Bob), the Ganache node that performs the blockchain tasks and does some additional setup so the whole demo can execute.  Here is a more detailed description of what is performed in the deploy script:

-  First multiple terminal sessions are started in split-screen using byobu. While executing the demo inside byobu, you may press shift+arrow keys to change the window in focus. While pressing shift+an arrow key, byobu prints the window number on top of every window.
- Then, in the top-left session (numbered as session 0 by byobu) Alice's machine-manager container is started with a shared volume that is later used to provide the flash drives and backing files needed for the instantiation of Alice's Cartesi Machines .
- A similar setup is performed for Bob (in byobu session number 1, top-center position), but Bob's machine-manager is initialized in a mode that triggers saturating the cycle of Cartesi Machines managed by that instance once it reaches a certain value. This intentional defect is in place so Bob effectively represents a party that is misbehaving and is necessary to illustrate the Verification Game performed in this demo.
-  In the bottom-left session (byobu session number 4), a blockchain-node container is started, getting Ganache up and running with all the Cartesi smart contacts that were deployed when building it's docker image. Additionally, at this point multiple files are exported from this container, containing the addresses of the deployed smart contracts used by other modules, as well as their ABIs. These files can be found under the exported-node-files directory, inside the blockchain-node directory once the container is up and running.
- Next, the script builds the docker image used to execute the simple dapp used in this demo. This image is tagged as cartesi/image-demo-dapp and uses some of the exported addresses and ABIs from the previous step.
- Afterwards, on the top-right window session (byobu session number 5), a container from the image built in the previous step (cartesi/image-demo-dapp ) is started and executes a simple python script that creates a session in Ana's machine-manager, initializing the Cartesi machine with the configuration to execute the sample computation task of this demo. The sample computation is composed of a few steps: creating a tiny SQLite database, inserting some data and performing a couple of queries. The Cartesi machine is initiated with 64MB of RAM, the Linux kernel, ROM, root file system and three additional flash drives that were obtained in the first step of the prepare_demo.sh script. The additional flash drives are job.ext2, out.ext2 and input.ext2. The job.ext2 drive has a shell script that executes the SQLite binary installed in the root file system drive, providing as input the sql commands in a file inside the input.ext2 drive and placing the resulting database and the results of the performed queries in the out.ext file sytem.
- An equivalent initialization is performed for a session in Bob's machine-manager, on the bottom-right window session (byobu session 6).
- Following, in the top-right session (byobu session 5), a simple python script is executed inside a  cartesi/image-demo-dapp container to generate the configuration file for Ana's compute module. The generated configuration file contains the address of Ana's machine-manager server, the address of the ethereum blockchain node (in this demo, the Cartesi contracts enabled Ganache instance) the addresses of all deployed contracts and the reference to their ABIs, as well as some other configurations.
- An equivalent configuration for Bob's compute module is generated right after.
- The next step is the execution of a short javascript script in the byobu session 2 window inside a cartesi/image-demo-dapp container that triggers a Verification Game between Alice and Bob. The script places Bob as the claimer and Alice as the challenger party that is disputing Bob's computation result.
- Finally, Alice and Bob compute services are started each inside a different container, respectively on byobu sessions 2 and 3, and they engage in the Verification Game that was triggered in the javascript script of the previous step. 



​	The Verification Game starts. Both parties agree on the Merkle tree root hash of the initial state of their Cartesi machines, as both were initialized with the same configuration, but they don't agree on the final hash.

​	The dispute starts with the partition phase, in which Alice and Bob engage in an n-ary search (where n=10 in this demo) to identify the cycle in which their execution of the sample computation diverge. 
Once they identify the exact cycle where they agree on the Merkle tree root hash of the Cartesi machine state but diverge on the state after the execution of that cycle's instruction (that is, they don't agree on the Merkle tree root hash of the Cartesi machine state for cycle + 1), it's time for Alice to submit to the memory manager contract in the blockchain her off-chain state accesses that happen in the transaction of the Cartesi machine state from the last cycle both parties agree to the cycle they do not.

​	Once the state accesses are submitted, the instruction that transitions the state of the Cartesi machine from the cycle both parties agree to the one they don't is then executed by the on-chain machine step implementation. If at any point the state accesses from the blockchain step implementation diverge from the state accesses submitted by Alice, Alice loses the dispute, if the execution ends with no divergences, Alice wins (in this demo, there are no divergences as Alice is the correct party and Bob is the one misbehaving).

## Contributing

Thank you for your interest in Cartesi! Head over to our [Contributing Guidelines](https://github.com/cartesi/demo/blob/master/CONTRIBUTING.md) for instructions on how to sign our Contributors Agreement and get started with Cartesi!

Please note we have a [Code of Conduct](https://github.com/cartesi/demo/blob/master/CODE_OF_CONDUCT.md), please follow it in all your interactions with the project.

## Authors

* *Augusto Teixeira*
* *Carlo Fragni*

## License

The demo repository and all contributions are licensed under [APACHE 2.0](https://www.apache.org/licenses/LICENSE-2.0). Please review our [LICENSE](https://github.com/cartesi/demo/blob/master/LICENSE) file.

## Acknowledgments

- Original work
