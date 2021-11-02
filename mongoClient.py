import pymongo

myclient = pymongo.MongoClient("mongodb://%s:%s@192.168.99.123:30001/" % ('root', 'root'))
mydb = myclient["mydatabase"]
mycol = mydb['test']

cursor = mycol.find({})
for document in cursor:
      print(document)