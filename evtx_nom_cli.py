from lib.nom import nom_file
from elasticsearch import helpers, Elasticsearch
import json 
es = Elasticsearch()

with open("es_stuff/index-template.json","r") as t_file:
    template = json.load(t_file)

es.indices.put_template(name="evtx-nom",body=template)
helpers.bulk(es, nom_file("sample_logs/Security.evtx"))