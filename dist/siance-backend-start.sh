#!/bin/bash

echo "Starting siance-sc on the « serveur de calcul »"

WD="WORKING DIRECTORY PATH"

cd "$WD"

# Ensures that the necessary docker
# containers are running... see the wiki
# of the project for a full description 
# of what should be running on the « serveur de calcul »
docker container restart elasticsearch
docker container restart unruffled_wiles
docker container restart affectionate_boyd

# Launch the backend server
# If needed, the api can be killed using
# killall python3 || true
python3 backend/bin/siance-backend background-watch
