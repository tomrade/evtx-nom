from lib import nom
import json
import argparse
import os
import sys

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

# Open Plugins
for output in config['outputs']:
    if output['enabled']:
        #es output
        try:
            nom_plugin = getattr(nom, output['name'])
            actioner = nom_plugin(output)
        except AttributeError:
            print("Cannot find module '{}' have you messed up the spelling???".format(output['name']))
            sys.exit()
        # Ingest Files
        for target in target_list:
            actioner.ingest_file(target)
