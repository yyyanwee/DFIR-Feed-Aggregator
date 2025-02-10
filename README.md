# Feed Aggregator Connector

The job of this connector is to poll multiple RSS Feeds at a regular schedule, parsing the feeds using `feedparser. The connector accomplishes a few key tasks:
1. Periodically poll multiple RSS feeds
2. Detect and process only new entries
3. Maintain a mechanism to track already processed entries
4. Convert feed entries into [STIX2 Report format](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html#_n8bjzg1ysgdq)
5. Push new reports to OpenCTI Platform


The connector currently covers the following RSS Feeds:
| RSS Feed | Feed URL |
| ----------- | ----------- |
| The Hacker News | https://feeds.feedburner.com/TheHackersNews |
| Bleeping Computer | https://www.bleepingcomputer.com/feed/|
|  | |
|  | |

The following rules are applied to the feeds:
| Rule |    Description |
| ----------- | ----------- |
| Category Filter |  |
| Ad Removal | |
|  | |
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
