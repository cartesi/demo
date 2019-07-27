docker run -it --name ephemeral-defective-machine-manager -p 0.0.0.0:50052:50051 -v `pwd`/test-files:/root/host --rm cartesi/image-machine-manager bash -c "cd machine-emulator && \`make env\` && cd .. && python3 manager_server.py -a 0.0.0.0 -d"