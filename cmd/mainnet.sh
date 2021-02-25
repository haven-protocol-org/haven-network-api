#!/bin/bash

export hv_mongo_url='mongodb://localhost:27017/?retryWrites=true&w=majority'
export hv_mongo_db='haven_mainnet'
export hv_daemon_url='https://vault.havenprotocol.org:443'
#export hv_resetrates=true
export hv_debug=true

python3 ../batch.py

