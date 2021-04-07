#!/bin/bash

export hv_mongo_url='mongodb://localhost:27017/?retryWrites=true&w=majority'
export hv_mongo_db='haven_testnet'
export hv_daemon_url='http://localhost:27750'
#export hv_resetrates=true
export hv_debug=true

python3 ../batch.py

