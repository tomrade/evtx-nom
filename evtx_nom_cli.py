from lib import nom
import json
import argparse
import os

# TODO args etc etc

# Open Config File
with open('config.json','r') as conf_file:
    config = json.load(conf_file)

# Grab All the files
target_list = []
for path in config['inputs']['directory']['paths']:
    for root,d_names,f_names in os.walk(path):
        for f in f_names:
            if f.endswith('.evtx'):
                target_list.append(os.path.join(root, f))
print(target_list)

# Open Plugins
for output in config['outputs']:
    if output['enabled']:
        #es output
        nom_plugin = getattr(nom, output['name'])
        actioner = nom_plugin(output)
        # Ingest Files
        for target in target_list:
            actioner.ingest_file(target)
