# evtx-nom
EVTX log file ingestion (no Windows required) using amazing ![evtx-rs](https://github.com/omerbenamram/evtx) lib. Current target is Elasticsearch with the hope of a modular output in the future.

* ECS common schema output (ive stayed close to winlogbeat however I use lowercase field names under winlog as I feel that is in spirit of ECS better than the Camel Case in winlogbeat)


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

So far I only have one outout plugin called "elastic_nom"

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
            "es_scheme" : "http"
        },
        {
            "name" : "stdout_nom",
            "enabled" : false
        }
    ]
}

```