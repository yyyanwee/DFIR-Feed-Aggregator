import datetime
import os
import sys
import time
import uuid
import feedparser
import yaml
import stix2
from pycti import OpenCTIConnectorHelper, get_config_variable


# OpenCTI Connector Initialization
# config = {
#     "opencti_url": os.getenv("OPENCTI_URL"),
#     "opencti_token": os.getenv("OPENCTI_TOKEN"),
#     "rss_feed_urls": os.getenv("FEED_URLS"), #list of RSS feed URLs
#     "keyword_filters": os.getenv("FEED_KEYWORDS"), #list of keywords to filter
#
# }

#hardcode testing version
config ={
    "opencti_url": "opencti:8080",
    "opencti_token": "d4f4d2b0-6b3b-4f6b-8d2d-3f8f6c6d8b4d",
    "rss_feed_urls": ["https://www.bleepingcomputer.com/feed/", "https://feeds.feedburner.com/TheHackersNews"],
    "keyword_filters": ["security"],
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
        #self.helper = OpenCTIConnectorHelper(self.config) 
        self.rss_feed_urls = config["rss_feed_urls"]
        self.keyword_filters = config["keyword_filters"]
        self.feed_keyword_blacklist = config["feed_keyword_blacklist"]

        self.processed_entries = set()

    def _load_state(self):
        #Loads previously processed entry identifiers from connector state
        state = self.helper.get_state()
        if state and 'processed_entries' in state:
            self.processed_entries = set(state['processed_entries'])

    def _save_state(self):
        #Saves current processed entries to connector state.
        self.helper.set_state({
            'processed_entries': list(self.processed_entries)
        })

    def filter_feeds(self, feed):
        # returns a list of feed entries which contains the keywords in its "category" field
        # currently affects the following feeds: Bleeping Computer
        try:
            filtered_items = [item for item in feed.entries
            if any(keyword.lower() in (item.category).lower() for keyword in self.keyword_filters)]
        except AttributeError:
            filtered_items = [item for item in feed.entries]

        # remove items with blacklisted keywords - remove ad posts or summary posts
        try:
            filtered_items = [item for item in filtered_items
            if not any(keyword.lower() in (item.title).lower() for keyword in self.feed_keyword_blacklist)]
        except AttributeError as e:
            print(e)
            pass

        return filtered_items
    
    def _create_stix_report(self, entry: Dict[str, Any]) -> stix2.Report:
        """
        Convert RSS entry into a STIX2 Report object.
        """
        return stix2.Report(
            id=f"report--{str(uuid.uuid4())}",
            created_by_ref=f"identity--{self.config['connector_id']}",
            name=entry.get('title', 'Untitled RSS Entry'),
            description=entry.get('summary', ''),
            published=entry.get('published', datetime.now().isoformat()),
            object_refs=[],  # You can add more refs if needed
            labels=['rss-feed', entry.get('source', 'unknown')]
        )
    
    def process_rss_feeds(self):
        self._load_state()

        for feed_url in self.config['rss_feeds']:
            feed = feedparser.parse(feed_url)
                
            for entry in feed.entries:
                if self._is_entry_new(entry):
                    try:
                        report = self._create_stix_report(entry)
                            
                        # Create report in OpenCTI
                        self.helper.stix2_create_report(report)
                            
                        # Track processed entry
                        self.processed_entries.add(entry.get('id', ''))
                        
                    except Exception as e:
                        self.helper.log_error(f"Error processing entry: {e}")

        # Save after processing
        self._save_state()
    
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

