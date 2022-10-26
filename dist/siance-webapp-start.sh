#!/bin/bash

echo "Starting siance-app service on the api/web-server"

WD="WORKING DIRECTORY PATH"

cd "$WD"

# Launch the "siance webapp" from data
# right now it is just a hack to get
# some of the old functions
#cd asn-webapp
#bash ./deploy.sh
#cd "$WD"

# Launch the API
# If needed, the api can be killed using
# killall python3 || true
python3 -m api api/

# Launch the component storybook
# this allows to debug components dynamically 
#cd front && http-server storybook-static -p 8000 -g &
#cd "$WD"

# Serve the website 
#cd front && http-server build -p 80 -g -c-1
