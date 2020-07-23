from lib.nom import prep_es, ingest_file
import json 

# TODO args etc etc
# Set Template
prep_es()
ingest_file('sample_logs/Security.evtx')