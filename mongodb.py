import pymongo
import os

class mongodb:
  DESCENDING=pymongo.DESCENDING
  def __init__(self):
      self.myclient = pymongo.MongoClient(os.environ['mongo'])
      self.mydb = self.myclient["haven"]

  def insert_one(self,collection,data):
    try:
      self.mydb[collection].insert_one(data)
    except pymongo.errors.DuplicateKeyError as e:
      return False
    except Exception as e:
      print(type(e))
      print(e.args)
      print(e)
    return True

  def find_one(self,collection,query="",sort=""):
    try:
      if query=="":
        query={}
      response=self.mydb[collection].find_one(query,sort=sort)
    except Exception as e:
      response=e.message
      print(type(e)) 
      print(e.args)
      print(e.message)
    return response
    
  def update_one(self,collection,myquery, newvalues):
    try:
      response=self.mydb[collection].update_one(myquery, newvalues)
    except Exception as e:
      response=e.message
      print(type(e)) 
      print(e.args)
      print(e.message)
    return response
    