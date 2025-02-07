import os
import time
import feedparser
import yaml
from pycti import OpenCTIConnectorHelper, get_config_variable, Stix



# OpenCTI Connector Initialization
config = {
    "opencti_url": os.getenv("OPENCTI_URL"),
    "opencti_token": os.getenv("OPENCTI_TOKEN"),
    "rss_feed_urls": "https://example.com/rss",
    "rss_feed_keywords": []

}

class FeedAggregator:
    def __init__(self):
        config_file_path = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
        config = (
            yaml.load(open(config_file_path), Loader=yaml.SafeLoader)
            if os.path.isfile(config_file_path)
            else {}
        )
        self.opencti_connector = OpenCTIConnectorHelper(config)
        self.rss_feed_urls = config["rss_feed_urls"]
        self.rss_feed_keywords = config["rss_feed_keywords"]

    def


    
if __name__ == "__main__":
    try:
        Feed_Aggregator = FeedAggregator()
        cyberMonitorConnector.run()
    except Exception as e:
        print(e)
        time.sleep(10)
        sys.exit(0)

    
