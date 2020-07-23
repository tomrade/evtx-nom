from evtx import PyEvtxParser
import json
import datetime

# This file is parsing the evtx file


# Parse Date to Python object ISO 8601/ RFC3339
def parse_date(datestring):
    output = datetime.datetime.fromisoformat(datestring.replace('Z','+00:00'))
    return output


# Get values form EVTX-RS json which may be attributes from XML land 
def get_value(item):
    if not item:
        return None
    if isinstance(item,dict):
        output = {}
        # XML Peeps
        if '#attributes' in item:
            for attr in item['#attributes']:
                output[attr.lower()] = item['#attributes'][attr]
        # Regular Object
        else:
            for thing in item:
                output[thing.lower()] = item[thing]
        if not item:
            output = None
        return output
    else:
        # just a variable
        output = str(item)
    return output

# Fetch Whole JSON section
def get_section(item):
    output = {}
    for field in item:
        value = get_value(item[field])
        print(field,value)
        if value != None:
            output[field.lower()] = value
    return output


# iterator from evtx-rs for bulk ES indexer
def nom_file(filename):
    actions = []
    parser = PyEvtxParser(filename)
    # Open Records
    for record in parser.records_json():

        #event = {'recordid' : record['event_record_id']}
        data = json.loads(record['data'])
        # Event Log event
        event = {'recordid': str(record['event_record_id'])}
        event.update(get_section(data['Event']['System']))
        if data['Event'].get('EventData'):
            event['event_data'] = get_section(data['Event']['EventData'])
        source = {
            '@timestamp' : parse_date(event['timecreated']['systemtime']),
            'winlog' : event,
            'os' : {"platform" : "windows"}
        }
        #print(json.dumps(source,indent=4))
        action = {
            '_index': 'evtx_nom',
            '_source': source
        }
        yield action
