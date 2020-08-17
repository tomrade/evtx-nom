from lib import nom
import json
import argparse
import os
import sys

# TODO args etc etc


parser = argparse.ArgumentParser(description='Ingest EVTX files into Elasticsearch and more')
parser.add_argument("-c","--config", help="Config File Defaults to config.json", default="config.json")
args = parser.parse_args()


print("Getting Ready to Nom")
# Open Config File
with open(args.config,'r') as conf_file:
    config = json.load(conf_file)

# Grab All the files
target_list = []
for path in config['inputs']['directory']['paths']:
    for root,d_names,f_names in os.walk(path):
        for f in f_names:
            if f.endswith('.evtx'):
                target_list.append(os.path.join(root, f))

print("found {} source files".format(len(target_list)))
print("=" * 24)
# Open Plugins
for output_plugin in config['outputs']:
    output = config['outputs'][output_plugin]
    if output['enabled']:
        #es output
        try:
            print("Trying '{}' Plugin".format(output['name']))
            nom_plugin = getattr(nom, output['name'])
            actioner = nom_plugin(output,config['parsing'])
        except AttributeError:
            print("Cannot find module '{}' have you messed up the spelling???".format(output['name']))
            sys.exit()
        # Ingest Files
        print("Ingesting files")
        for target in target_list:
            actioner.ingest_file(target)
        print("=" * 24)
