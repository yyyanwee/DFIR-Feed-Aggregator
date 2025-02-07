import os
import sys
import time
import feedparser
import yaml
import stix2
from pycti import OpenCTIConnectorHelper, get_config_variable


# OpenCTI Connector Initialization
config = {
    "opencti_url": os.getenv("OPENCTI_URL"),
    "opencti_token": os.getenv("OPENCTI_TOKEN"),
    "rss_feed_urls": os.getenv("FEED_URLS"), #list of RSS feed URLs
    "rss_feed_keywords": os.getenv("FEED_KEYWORDS"), #list of keywords to filter
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

    def filter_feed(self, feed):
        for keyword in self.rss_feed_keywords:
            if keyword in feed.title:
                return True
        return False
    
    def run(self):
        for feed_url in self.rss_feed_urls:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                if self.filter_feed(entry):
                    self.create_stix2_indicator(entry)


    
if __name__ == "__main__":
    try:
        Feed_Aggregator = FeedAggregator()
        Feed_Aggregator.run()
    except Exception as e:
        print(e)
        time.sleep(10)
        sys.exit(0)

    
