docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ephemeral-defective-machine-manager > ephemeral-defective-machine-manager.add
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ephemeral-machine-manager > ephemeral-machine-manager.add
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ephemeral-cartesi-blockchain-node > ephemeral-cartesi-blockchain-node.add
docker run -it --name ephemeral-make-alice-disp-config -v `pwd`:/root/host --rm cartesi/image-demo-dapp bash -c "python3 dispatcher_config_generator.py -b /root/host/base_dispatcher_config_bob.yaml -o /root/host/dispatcher_config_bob.yaml -dmm -obn -ua 0x8b5432ca3423f3c310eba126c1d15809c61aa0a9 -d"
