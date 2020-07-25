import json
import sys
import os

# This is to parse the WELMS into our JSON map file


def parse_event(event):
    channel = event['LoggedTo']['Name']
    provider = event['Provider']
    message = event['Message']
    eventid = event['Id']['Value']
    #print("====" * 12)
    #print(channel,provider,eventid)
    return {
        "channel" : channel,
        "provider" : provider,
        "eventid" : eventid,
        "message" : message
        }


def process_file(filename,welm_map):
    with open(filename,'r') as in_file:
        data = json.load(in_file)
    for item in data:
        log = parse_event(item)
        if log['channel'] == "":
            continue
        if log['message'] == "":
            continue
        if log['channel'] in welm_map:
            if log['provider'] in welm_map[log['channel']]:
                if log['eventid'] in welm_map[log['channel']][log['provider']]:
                    if log['message'] != welm_map[log['channel']][log['provider']][log['eventid']]:
                        print("something very odd dupe eventid {} on {} {} but with different message strings".format(log['eventid'],log['channel'],log['provider']))
                welm_map[log['channel']][log['provider']][log['eventid']] = log['message']
            else:
                welm_map[log['channel']][log['provider']] = { log['eventid'] : log['message']}
        else:
            welm_map[log['channel']] = { log['provider'] : { log['eventid'] : log['message'] }}
    return welm_map

welm_path = "/home/tomm/welm/"

welm_map = {}
target_list = []
for dir in os.listdir(welm_path):
    event_file = os.path.join(welm_path,dir,'welm/events.json')
    if os.path.isfile(event_file):
        print("Found {}".format(event_file))
        target_list.append(event_file)
maps = []
for target in target_list:
    welm_map = process_file(target,welm_map)
# Combined WELM Map
with open('welm_map.json','w') as out_file:
    json.dump(welm_map,out_file,indent=2)



    