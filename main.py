from blockchain import blockchain
from coingecko import coingecko
from datetime import datetime, timedelta

import pymongo
import json
import os



def importExchangePrice():
  Coingecko=coingecko()
  Coingecko.importExchangePrice()


def main(event, context):
  Blockchain=blockchain()
  Blockchain.importCurrencies()
  Blockchain.scanBlockchain()



#importExchangePrice()
main("","")
