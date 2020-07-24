from lib.nom import prep_es, ingest_file
import json
import argparse
import os

# TODO args etc etc

# Grab All the files
target_list = []
for root,d_names,f_names in os.walk('sample_logs'):
    for f in f_names:
        if f.endswith('.evtx'):
            target_list.append(os.path.join(root, f))
print(target_list)
# Set Template
prep_es()
# Ingest Files
for target in target_list:
    ingest_file(target)