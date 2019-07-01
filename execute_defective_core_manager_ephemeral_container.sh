docker run -it --name ephemeral-defective-core-manager -p 0.0.0.0:50052:50051 -v `pwd`/test-files:/root/host --rm cartesi/image-core-manager bash -c "python3 manager_server.py -a 0.0.0.0 -d"
