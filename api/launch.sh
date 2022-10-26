#!/usr/bin/bash 

# For development
#uvicorn app:app --reload --port 3011

# For production 
nohup uvicorn app:app --port 3011 &
