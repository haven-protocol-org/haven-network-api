import datetime
import tempfile
import pid

import blockchain
import coingecko

def importExchangePrice(duration):
  Coingecko=coingecko.Coingecko()
  Coingecko.importExchangePrice(duration)


def batch():
  try:
    with pid.PidFile('havenImport') as p:
      print ("Starting process " + str(p))
      bc=blockchain.Blockchain()
      bc.importCurrencies()
      importExchangePrice(365*3)
      importExchangePrice(90)
      importExchangePrice(2)
      bc.scanBlockchain()
  except pid.PidFileError:
    print ("Traitement déjà lancé")
  except Exception as e:
    print (e)

begin_time = datetime.datetime.now()
batch()
time_elapsed = datetime.datetime.now() - begin_time
print("Script ended in " + str(time_elapsed))