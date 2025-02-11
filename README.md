# Feed Aggregator Connector

The job of this connector is to poll multiple RSS Feeds at a regular schedule, parsing the feeds using `feedparser`. The connector accomplishes a few key tasks:
1. Periodically poll multiple RSS feeds
2. Detect and process new entries
3. Convert feed entries into [STIX2 Report format](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_n8bjzg1ysgdq)
4. Push new reports to OpenCTI Platform


The connector currently covers the following RSS Feeds:
| RSS Feed | Feed URL |
| ----------- | ----------- |
| The Hacker News | https://feeds.feedburner.com/TheHackersNews |
| Bleeping Computer | https://www.bleepingcomputer.com/feed/|
|  | |


## Installation
The Feed Aggregator connector is a standalone Python process that must have access
to the OpenCTI platform and the RabbitMQ. RabbitMQ credentials and connection parameters
are provided by the API directly, as configured in the platform settings.

Place the contents in the `docker-compose.yml` file provided into the global `docker-compose.yml` file used for OpenCTI.

### Configuration variables

Below are the parameters you'll need to set for OpenCTI:

| Parameter `OpenCTI` | config.yml | Docker environment variable | Mandatory | Description                                          |
|---------------------|------------|-----------------------------|-----------|------------------------------------------------------|
| URL                 | url        | `OPENCTI_URL`               | Yes       | The URL of the OpenCTI platform.                     |
| Token               | token      | `OPENCTI_TOKEN`             | Yes       | The default admin token set in the OpenCTI platform. |
 
Below are the parameters you'll need to set to run the connector properly:

| Parameter `Connector` | config.yml          | Docker environment variable   | Default      | Mandatory | Description                                                                                      |
|-----------------------|---------------------|-------------------------------|--------------|-----------|--------------------------------------------------------------------------------------------------|
| ID                    | `id`                | `CONNECTOR_ID`                | /            | Yes       | A unique `UUIDv4` identifier for this connector instance.                                        |
| Name                  | `name`              | `CONNECTOR_NAME`              | `FeedAggregator` | Yes       | Full name of the connector : `Feed_Aggregator`.                                                       |

## How it works

FeedParser processes RSS Feeds and extract entries. 
The entry is filtered according to certain rules to remove unwanted information. 

The following rules are applied to the feeds:
| Rule |    Description | Feeds Applied |
| ----------- | ----------- | ----------- |
| Category Filter | Selects articles of certain categories | Bleeping Computer |
| Ad Removal | Removes unnecessary ad posts or summary posts | All |
|  | |


The filtered entry is then converted into Stix2 Report Format and sent to OpenCTI Platform. 

#### Example Report Format
```
{
  "type": "report",
  "spec_version": "2.1",
  "id": "report--84e4d88f-44ea-4bcd-bbf3-b2c1c320bcb3",
  "created": "2015-12-21T19:59:11.000Z",
  "modified": "2015-12-21T19:59:11.000Z",
  "created_by_ref": "identity--a463ffb3-1bd9-4d94-b02d-74e4f1658283",
  "name": "The Black Vine Cyberespionage Group",
  "description": "A simple report with an indicator and campaign",
  "published": "2016-01-20T17:00:00.000Z",
  "report_types": ["campaign"],
  "object_refs": [
    "indicator--26ffb872-1dd9-446e-b6f5-d58527e5b5d2",
    "campaign--83422c77-904c-4dc1-aff5-5c38f3a2c55c",
    "relationship--f82356ae-fe6c-437c-9c24-6b64314ae68a"
  ]
}
## type, spec_version, created, modified, name, published, object_refs are required ###
```
## Reference Materials

<b>PyCTI:</b>  
https://opencti-client-for-python.readthedocs.io/en/stable/

<b>FeedParser:</b>  
https://feedparser.readthedocs.io/en/latest/

<b>OpenCTI:</b>  
https://docs.opencti.io/latest/deployment/connectors/#introduction
https://docs.opencti.io/latest/development/connectors/

<b>Stix2:</b>  
https://oasis-open.github.io/cti-documentation/stix/intro.html
    



