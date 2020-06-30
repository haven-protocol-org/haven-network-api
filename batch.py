import datetime
import tempfile
import pid
import os 

import blockchain
import coingecko


def batch():
  bc=blockchain.Blockchain()
  cg=coingecko.Coingecko()
  if 'batch_debug' in os.environ:
    cg.importCurrencies()
    cg.importExchangePrice(365*3)
    cg.importExchangePrice(90)
    cg.importExchangePrice(2)
    bc.scanBlockchain()
  else:
    try:
      with pid.PidFile('havenImport') as p:
        print ("Starting process " + str(p))
        cg.importCurrencies()
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