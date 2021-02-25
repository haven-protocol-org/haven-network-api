#!/bin/bash

#export hv_consumer_key='jCTLM0j92xPEgMz5pNYdE8uMo'
#export hv_consumer_secret='g7pwrdrHz3UohkprfX3jomr9Htz06bD1zHR8T7XZ7g4WPmCV0I'
#export hv_access_token_key='558692181-Iy9SKeaJCMceUnfmu3rfiABkfiUy1SJSpj3KgoiB'
#export hv_access_token_secret='juMUdKHVDD4uSDwfyzYkDois1jQiC4iQNZ2rsgOrDXq5T'



export hv_mongo_url='mongodb://localhost:27017/?retryWrites=true&w=majority'
export hv_mongo_db='haven_mainnet'
export hv_daemon_url='https://vault.havenprotocol.org:443'
#export hv_resetrates=true
export hv_debug=true

python3 ../batch.py

