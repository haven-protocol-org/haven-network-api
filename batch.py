#!/usr/bin/python3

import datetime
import tempfile
import pid
import os 

import blockchain
import coingecko


def batch():
  resetRates=os.getenv('hv_resetrates',False)
  #Check variables
  MANDATORY_ENV_VARS = ["hv_mongo_url", "hv_mongo_db","hv_daemon_url"]
  for var in MANDATORY_ENV_VARS:
    if var not in os.environ:
        raise EnvironmentError("Failed because {} is not set.".format(var))

  bc=blockchain.Blockchain()
  cg=coingecko.Coingecko()
  if 'hv_debug' in os.environ:
    cg.importCurrencies()
    if resetRates:
      cg.importExchangePrice(365*3)
      cg.importExchangePrice(90)
    cg.importExchangePrice(2)
    bc.scanBlockchain()
  else:
    try:
      with pid.PidFile('havenBatch' + os.environ['hv_mongo_db']) as p:
        print ("Starting process on " + os.environ['hv_mongo_db'])
        cg.importCurrencies()
        if resetRates:
          cg.importExchangePrice(365*3)
          cg.importExchangePrice(90)
        cg.importExchangePrice(2)
        bc.scanBlockchain()
    except pid.PidFileError:
      print ("Process already running")
    except Exception as e:
      print (e)

begin_time = datetime.datetime.now()
batch()
time_elapsed = datetime.datetime.now() - begin_time
print("Script ended in " + str(time_elapsed))