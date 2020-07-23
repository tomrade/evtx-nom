from lib.nom import nom_file
from elasticsearch import helpers, Elasticsearch
import json 
es = Elasticsearch()

with open("es_stuff/index-template.json","r") as t_file:
    template = json.load(t_file)

done = 0
errors = 0
es.indices.put_template(name="evtx-nom",body=template)
for ok, action in helpers.streaming_bulk(
     client=es, actions=nom_file("sample_logs/Security.evtx")
):
    if not ok:
        errors += 1
    done += 1

print("ingested {} out of {} events".format(done - errors, done))