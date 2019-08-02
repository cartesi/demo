docker run -it --name ephemeral-initialize-machine -v `pwd`/test-files:/opt/cartesi/test-files --rm cartesi/image-demo-dapp bash -c "python3 initialize_machine.py -c -a $1:50051"
