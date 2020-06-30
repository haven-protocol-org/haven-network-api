import pymongo
import os


class Mongodb:
  def __init__(self):
      self.myclient = pymongo.MongoClient(os.environ['mongo'])
      self.mydb = self.myclient[os.environ['dbname']]

  def delete_one(self,collection,query):
    try:
      self.mydb[collection].delete_one(query)
    except Exception as e:
      print(type(e))
      print(e.args)
      print(e)
    return True
  
  def delete(self,collection,query):
    try:
      self.mydb[collection].delete_many(query)
    except Exception as e:
      print(type(e))
      print(e.args)
      print(e)
    return True
    
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

  def find_last(self,collection,query={}):
    try:
      response=self.find_one(collection,query,sort=[( '_id', pymongo.DESCENDING )])
    except Exception as e:
      response=e.message
      print(type(e)) 
      print(e.args)
      print(e.message)
    return response

  def find_first(self,collection,query={}):
    try:
      response=self.find_one(collection,query,sort=[( '_id', pymongo.ASCENDING )])
    except Exception as e:
      response=e.message
      print(type(e)) 
      print(e.args)
      print(e.message)
    return response

  def find_one(self,collection,query={},sort={}):
    try:
      response=self.mydb[collection].find_one(query,sort=sort)
    except Exception as e:
      response=e.message
      print(type(e)) 
      print(e.args)
      print(e.message)
    return response
  
  def find(self,collection,query={},sort={}):
    try:
      response=self.mydb[collection].find(query,sort=sort)
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
      print(type(e)) 
      print(e.args)
      print(e.message)
    return response
    