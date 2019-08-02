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

## Contributing

Pull requests are welcome. When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the owners of this repository before making a change.

Please note we have a code of conduct, please follow it in all your interactions with the project.

## Authors

* *Augusto Teixeira*
* *Carlo Fragni*

## License

- TODO

## Acknowledgments

- Original work
