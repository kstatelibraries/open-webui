#!/bin/bash

USER="innovationlab"
REMOTE_HOST="10.130.110.20"



# Spawn the first SSH connection (port 12000 local to 11434 remote)
ssh -L 12000:localhost:11434 $USER@$REMOTE_HOST -N &

# Spawn the second SSH connection (port 12001 local to 7860 remote)
ssh -L 12001:localhost:7860 $USER@$REMOTE_HOST -N &

wait