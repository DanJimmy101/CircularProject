import json
from utility import docfile

with open(docfile, 'r', encoding='utf-8') as json_data:
    doclistData = json.load(json_data)