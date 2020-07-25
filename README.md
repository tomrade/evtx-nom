# evtx-nom
EVTX log file ingestion (no Windows required) using amazing ![evtx-rs](https://github.com/omerbenamram/evtx) lib. Current target is Elasticsearch with the hope of a modular output in the future.

* Elasticsearch output uses ECS common schema output (ive stayed close to winlogbeat however I use lowercase field names under winlog as I feel that is in the spirit of ECS better than the Camel Case used in winlogbeat)
* ECS mappings are done via a config file you can add your own maps to
* Event log message string reconstruction from the WELM project , where possible the event_data/user_data variables are put back into the string

## Usage

``` bash
tomm@dev-ubuntu:~/evtx-nom/evtx-nom$ python3 evtx_nom_cli.py 
Getting Ready to Nom
found 1 source files
========================
Trying 'elastic_nom' Plugin
Ingesting files
Starting work on target sample_logs/Security.evtx
Finished Processing sample_logs/Security.evtx in 8 seconds. ingested 31828 out of 31828 events
========================
```

## Config File

So far I only have one (real) output plugin called "elastic_nom", and a demo json stdout one

You add your input paths to the directory input and then choose one or more outputs.

``` json
{
    "inputs" : {
        "directory" : {
            "enabled" : true,
            "paths" : [
                "sample_logs"
            ]
        }
    },
    "outputs" : [
        {
            "name" : "elastic_nom",
            "enabled" : true,
            "es_host" : "localhost",
            "es_port" : "9200",
            "es_index" : "evtx_nom",
            "security" : "none",
            "es_user" : "USERNAME",
            "es_pass" : "PASSWORD",
            "es_api_key" : "APIKEY",
            "es_scheme" : "http",
            "index_template" : "es_stuff/index-template.json",
            "ecs_map_file" : "es_stuff/ecs_map.json",
            "ecs_mode" : true
        },
        {
            "name" : "stdout_nom",
            "enabled" : false
        }
    ]
}

```

## WELM Mapping

Ive included a welm dataset here under the welm folder, is currently hardcoded into the script but will add some config later. It is made from the "events.json" file from the WELM project. 

Like my ECS mapping file, it is a JSON file (15mb beware) structured based on channel + provider + event_id. The lookup is done with a composite key like with my ECS mapper on a flat dictionary to hopefully improve speed. Ive trred to include much of the logic in the JSON to reduce the steps I need to do in python at ingest time.

``` json
      "4418": {
        "raw": "%1.%2: EFS service failed to provision RMS for EDP. Error code: %3.",
        "params": [
          "filenumber",
          "linenumber",
          "errorcode"
        ],
        "format_string": "{1}.{2}: EFS service failed to provision RMS for EDP. Error code: {3}.",
        "swap_mode": true
      }
```

You can see when I created the dataset I precreated a python "format" string to use and include a "swap_mode" flag so evtx-mode will attempt to do the format when this is true rather than using a "in" lookup or regex on ingest. Python format starts its numbering at 0 rather 1 unlike the event logs however the way I deal with is to bump parameter list in evtx-nom when executing ie

``` python
["filenumber","linenumber","errorcode"]
```
becomes

``` python
["bump","filenumber","linenumber","errorcode"]
```


## Plugins

### Elasticsearch "elastic_nom"

#### Config

``` json
        {
            "name" : "elastic_nom",
            "enabled" : true,
            "es_host" : "localhost",
            "es_port" : "9200",
            "es_index" : "evtx_nom",
            "security" : "none",
            "es_user" : "USERNAME",
            "es_pass" : "PASSWORD",
            "es_api_key" : "APIKEY",
            "es_scheme" : "http",
            "index_template" : "es_stuff/index-template.json",
            "ecs_map_file" : "es_stuff/ecs_map.json",
            "ecs_mode" : true
        }
```

| field | value type | notes |
| --- | --- | --- |
| name | elastic_nom | it must be elastic_nom |
| enabled | bool | true or false, if true it will be used |
| es_host | string | ip or host of elasticsearch |
| es_port | string | port of elasticsearch (default is 9200) |
| es_index | string | index to write events to |
| security | string | can be "none" , "basic" or "api" |
| es_user | string | elasticsearch security username (for basic auth |
| es_pass | string | elasticsearch security password ( for basic auth)|
| es_api_key | string | base64 encoded api key (for api auth) |
| es_scheme| string | http or https (for security you will be using https) |
| index_template | string | path to index template, ive included one under es_stuff/index-template.json, You do not need to edit this for a custom index name as it will be done by the plugin |
| ecs_map_file | string | path to ecs map |
| ecs_mode | string | if set to false no ecs mapping is done, the logs are still ecs structured ie under winlog.* just no processing ) |

#### ECS Mapping

The ECS map file is another JSON file. It is structured based on the channel, provider and finally the eventID

``` json
{
    "Security" : {
        "Microsoft-Windows-Security-Auditing" : {
            "4624" :{
                "event.action" : "user-logon",
                "event.kind" : "event",
                "user.name" : "%%%%winlog.event_data.targetusername",
                "user.id" : "%%%%winlog.event_data.targetusersid"
            }
        }
    }
}

```

Nested fields can be done with dots ie ```event.action``` means

``` json
{
"event" : {
    "action" : "value"

}
}
```

If a value starts with 4 percentages ie "%%%%" evtx-nom will look up the value based on the provided path for example the value ```%%%%winlog.event_data.targetusersid``` Looks for the value from the field 
```winlog.event_data.targetusersid``` (again using dots for nested fields). Please note that the path will be the lowercase ECS path as this lookup is done post parsing, you can find these paths in kibana/es post ingest.

When evtx-nom starts up it flattens these maps into a flat dictionary via a key value consisting of "channel + provider + eventid" ie

``` python
mapping_dict = {
    "securityMicrosoft-Windows-Security-Auditing4624" :  {"event.action" : "user-logon"}
}
```

This is so I can find as match based on "for X in mapping_dict" rather than a nested search tree, im not if this is better/faster or not , but I feel a dictionary check in RAM would be better/faster than a DB even with memcache

