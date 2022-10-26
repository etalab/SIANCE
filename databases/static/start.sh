#!/usr/bin/bash

docker run -d --net elastictest --name db -p 5432:5432 -e POSTGRES_PASSWORD="siance" siance/db -c "listen_addresses=*"

