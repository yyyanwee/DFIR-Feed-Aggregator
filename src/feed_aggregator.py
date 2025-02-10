import os
import sys
import time
import feedparser
import yaml
import stix2
from pycti import OpenCTIConnectorHelper, get_config_variable


# OpenCTI Connector Initialization
# config = {
#     "opencti_url": os.getenv("OPENCTI_URL"),
#     "opencti_token": os.getenv("OPENCTI_TOKEN"),
#     "rss_feed_urls": os.getenv("FEED_URLS"), #list of RSS feed URLs
#     "rss_feed_keywords": os.getenv("FEED_KEYWORDS"), #list of keywords to filter
# }

#hardcode testing version
config ={
    "opencti_url": "opencti:8080",
    "opencti_token": "d4f4d2b0-6b3b-4f6b-8d2d-3f8f6c6d8b4d",
    "rss_feed_urls": ["https://www.bleepingcomputer.com/feed/", "https://feeds.feedburner.com/TheHackersNews"],
    "rss_feed_keywords": ["security"],
    "feed_keyword_blacklist": ["top"]
}

class FeedAggregator:
    def __init__(self):
        #config_file_path = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
        # config = (
        #     yaml.load(open(config_file_path), Loader=yaml.SafeLoader)
        #     if os.path.isfile(config_file_path)
        #     else {}
        # )
        #self.opencti_connector = OpenCTIConnectorHelper(config)
        self.rss_feed_urls = config["rss_feed_urls"]
        self.rss_feed_keywords = config["rss_feed_keywords"]
        self.feed_keyword_blacklist = config["feed_keyword_blacklist"]

    def filter_feeds(self, feed):
        # returns a list of feed entries which contains the keywords in its "category" field
        try:
            filtered_items = [item for item in feed.entries
            if any(keyword.lower() in (item.category).lower() for keyword in self.rss_feed_keywords)]
        except AttributeError:
            filtered_items = [item for item in feed.entries]

        # remove items with blacklisted keywords
        try:
            filtered_items = [item for item in filtered_items
            if not any(keyword.lower() in (item.title).lower() for keyword in self.feed_keyword_blacklist)]
        except AttributeError as e:
            print(e)
            pass


        return filtered_items
    
    def send_to_opencti(self, entries):
        #converts the list of filered entries into a stix bundle and sends it to OpenCTI as a report

        #create stix objects from list of filtered feed items

        #create stix bundle from objects
        return

    
    def run(self):
        for feed_url in self.rss_feed_urls:
            print(feed_url)
            feed = feedparser.parse(feed_url)
            filtered_entries = self.filter_feeds(feed)
            for entry in filtered_entries:
                print(entry.title)
                print(entry.description)
                print("")
            print("next site")
        
        pass
            


    def process(self):
        self.run()
        time.sleep(3600) #1 hour in seconds
    
if __name__ == "__main__":
    try:
        Feed_Aggregator = FeedAggregator()
        Feed_Aggregator.process()
    except Exception as e:
        print(e)
        time.sleep(10)
        sys.exit(0)

    
