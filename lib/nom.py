from evtx import PyEvtxParser
import json
import datetime
from elasticsearch import helpers, Elasticsearch
import sys

# This file is parsing the evtx file and any default modules

# Example Standard Out Plugin
class stdout_nom():
    def __init__(self,config):
        self.name = "standard out JSON example"
    def ingest_file(self,filename):
        print("Starting std (sh)outing on target {}".format(filename))
        for event in nom_file(filename):
            print(json.dumps(event,indent=2))
            print("=" * 12)
        print("Finished Shouting")

# Elasticsearch Plugin
class elastic_nom():
    def __init__(self,config):
        self.name = "elasticseach ingest"
        self.es_host = config['es_host']
        self.es_port = config['es_port']
        self.es_index = config['es_index']
        self.security = config['security']
        self.es_user = config['es_user']
        self.es_pass = config['es_pass']
        self.es_api_key = config['es_api_key']
        self.scheme = config['es_scheme']
        self.index_template = config['index_template']
        self.ecs_map = self.load_ecs(config['ecs_map_file'])
        self.ecs_mode = config['ecs_mode']
        self.prep_es()
    def make_key(self,channel,provider,event_id):
        key = channel + provider + event_id
        return key.lower()
    def load_ecs(self,filename):
        with open(filename,'r') as in_file:
            data = json.load(in_file)
        # I think a flat dictionary is better for this sort of thing
        mapping_dict = {}
        for channel in data:
            for provider in data[channel]:
                for event_id in data[channel][provider]:
                    mapping_dict[self.make_key(channel,provider,event_id)] =  data[channel][provider][event_id]
        return mapping_dict
    def get_es(self):  
        if self.security == "basic":
            es = Elasticsearch(
                [self.es_host],
                http_auth=(self.es_user, self.es_pass),
                scheme=self.scheme,
                port=self.es_port,
            )
            return es
        elif self.security == "api":
            es = Elasticsearch(
                [self.es_host],
                api_key=self.es_api_key,
                scheme=self.scheme,
                port=self.es_port,
            )
            return es
        elif self.security == "none":
            es = Elasticsearch(
                [self.es_host],
                port=self.es_port,
                scheme=self.scheme
            )
            return es
        else:
            print("something has gone with getting an ES client")
            return None
    def prep_es(self):
        # connect to es
        es = self.get_es()
        # set/reset template
        with open(self.index_template,"r") as t_file:
            template = json.load(t_file)
        # If a non default index name add it to the template
        if self.es_index != 'evtx_nom':
            template['index_patterns'].append(self.es_index)
        es.indices.put_template(name="evtx-nom",body=template)
        return es
    def ingest_file(self,filename):
        # Process 1 file ah ah ah
        print("Starting work on target {}".format(filename))
        es = self.get_es()
        start = datetime.datetime.utcnow()
        errors = 0
        done = 0
        for ok, action in helpers.streaming_bulk(
            client=es, actions=self.prepare_actions(filename)
        ):
            if not ok:
                errors += 1
            done += 1
        end = datetime.datetime.utcnow()
        duration = end - start
        print("Finished Processing {} in {} seconds. ingested {} out of {} events".format(filename,duration.seconds,done - errors, done))
        return {'errors' : errors, 'done' : done}
    def prepare_actions(self,filename):
        # This method is a wrapper around the base nom method to add each event as a bulk index action
        for event in nom_file(filename):
            source = {
                '@timestamp' : event['timecreated']['systemtime'],
                'winlog' : event,
                'os' : {"platform" : "windows"},
                'agent' : {"name" : "evtx-nom"}
            }
            # Process the ECS!
            action = {
                '_index': self.es_index,
                '_source': self.process_ecs(source)
            }
            yield action
    def parse_date(self,datestring):
        # Parse Date to Python object ISO 8601/ RFC3339
        output = datetime.datetime.fromisoformat(datestring.replace('Z','+00:00'))
        return output
    def process_ecs(self,source):
        # If we are not bothering just skip all this horrible code
        if not self.ecs_mode:
            return source
        # Take the source document, check if we have an ECS map for it and then if so do the things
        key = self.make_key(
            source['winlog']['channel'],
            source['winlog']['provider']['name'],
            source['winlog']['eventid']
            )
        # check if we have a map
        if key in self.ecs_map:
            # for each ecs field key in the map add it to the source
            for field in self.ecs_map[key]:
                if self.ecs_map[key][field].startswith('%%%%'):
                    value = self.dict_fetch(source,self.ecs_map[key][field].replace('%%%%',''))
                else:
                    value = self.ecs_map[key][field]
                source = self.dict_put(field,value,source)
            return source
        else:
            return source
    def dict_put(self,key,value,source):
        # Merge ECS value back into source document , I think this works but its a bit mental to try and understand. YAY Recursive!
        # This should build the dictionary up bringing existing paths along for the ride then
        if '.' in key:
            # Our key is a dot noted path ie "object.subobject.subsubobject" etc
            key_list = key.split('.')
            # get the leftmost subobject
            item = key_list[0]
            # remove this from the key for the next runs
            key_list.pop(0)
            # check if the subobject already exists in source object
            if item not in source:
                # create an empty subobject and keep going deeper into inception
                source[item] = self.dict_put('.'.join(key_list),value,{})
                # Whatever comes back goes into our object
            else:
                # we need to merge into existing subobject and keep going deeper into inception
                source[item] = self.dict_put('.'.join(key_list),value,source[item])
                # Whatever comes back goes into our object
        else:
            # key is just a field name now  so add value finally
            source[key] = value
        # return what we have up to previous level of inception or the exit if we back at the top 
        return source

    def dict_fetch(self,source,key):
        if '.' in key:
            key_list = key.split('.')
            new_source = source[key_list[0]]
            key_list.pop(0)
            value = self.dict_fetch(new_source,'.'.join(key_list))
        else:
            value = source[key] or "unknown"
        return value


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
        # just a variable strings for es as numbers dont make sense at the moment
        output = str(item)
    return output

# Fetch Whole JSON section
def get_section(item):
    output = {}
    for field in item:
        value = get_value(item[field])
        if value != None:
            output[field.lower()] = value
    return output


# iterator from evtx-rs You can use this standalone if you want (ie for splunk)
def nom_file(filename):
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
        # Raw Document
        event['xml'] = record['data']
        yield event
