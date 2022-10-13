from tinydb import TinyDB, Query
import json

jsonDB = 'tagsDB.json'

db = TinyDB(jsonDB)
DBquery = Query()

def add_stuff(table_name,data_to_insert):
    table = db.table(table_name)
    if len(table.search(DBquery.tag == data_to_insert)) <= 0:
        table.insert({'tag': data_to_insert})

def search_db(table_name):
    table = db.table(table_name)
    db_data = table.all()
    data_to_out = []
    for data in db_data:
        data_to_out.append(data['tag'])
    return set(data_to_out)

def tiny_db_add_data(data_to_db):
    if (',' in data_to_db):
        data = data_to_db.split(",")
        for tag in data:
            tagLength = len(tag)
            if tagLength >= 3:
                add_stuff(tag[:3],tag)
            elif tagLength == 2:
                add_stuff(tag,tag)
            else:
                print("Not a tag")
    else:
        tagLength = len(data_to_db)
        if tagLength >= 3:
            add_stuff(data_to_db[:3],data_to_db)
        elif tagLength == 2:
            add_stuff(data_to_db,data_to_db)
        else:
            print("Not a tag")

def tiny_db_search_data(search_keyword):
    searchTagLength = len(search_keyword)
    if searchTagLength >= 3:
        return search_db(search_keyword[:3])
    elif searchTagLength == 2:
        return search_db(search_keyword)
    else:
        print("Not a search keyword")