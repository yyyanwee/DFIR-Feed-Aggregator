import datetime
import os
import re
import sys
import time
import feedparser
import dateparser
import stix2
from pycti import OpenCTIConnectorHelper, get_config_variable, Report

class FeedAggregator:
    def __init__(self):
        #config_file_path = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
        # config = (
        #     yaml.load(open(config_file_path), Loader=yaml.SafeLoader)
        #     if os.path.isfile(config_file_path)
        #     else {}
        # )

        #hardcode testing version
        self.config ={
            "OPENCTI_URL": "http://opencti:8080",
            "OPENCTI_TOKEN": "d4f4d2b0-6b3b-4f6b-8d2d-3f8f6c6d8b4d",
            "rss_feed_urls": ["https://www.bleepingcomputer.com/feed/","https://feeds.feedburner.com/TheHackersNews"], 
            "keyword_filters": ["security"],
            "feed_keyword_blacklist": ["top"] #not exhaustive
        }

        #self.helper = OpenCTIConnectorHelper(self.config) 
        self.rss_feed_urls = self.config["rss_feed_urls"]
        self.keyword_filters = self.config["keyword_filters"]
        self.feed_keyword_blacklist = self.config["feed_keyword_blacklist"]
        
        # to track already processed entries
        self.processed_entries = set()

        # self.dummy_organization = self.helper.api.identity.create(
        #     type="Organization",
        #     name="DUMMY",
        #     description="Dummy organization which can be used in various unknown contexts.",
        # )

    def _load_state(self):
        #Loads previously processed entry identifiers from connector state
        state = self.helper.get_state()
        if state and "processed_entries" in state:
            self.processed_entries = set(state["processed_entries"])

    def _save_state(self):
        #Saves current processed entries to connector state.
        self.helper.set_state({
            "processed_entries": list(self.processed_entries)
        })
    
    def _is_new_entry(self,entry) -> bool:
        # Checks if RSS entry is new and should be processed
        return

    #Helper function
    def _create_stix_report(self, entry: dict[str, any]) -> stix2.Report:
        #Convert RSS entry into a STIX2 Report object.
        report_name = entry.title
        report_date = dateparser.parse(entry.published)
        external_reference = stix2.ExternalReference(source_name="Aggregator", url=entry.link) # TODO: Find a way to name external reference according to source name

        report = stix2.Report(
                        id=Report.generate_id(report_name, report_date),
                        name=report_name,
                        published=report_date,
                        description = entry.summary,
                        external_references=[external_reference],
                        object_refs=["indicator--26ffb872-1dd9-446e-b6f5-d58527e5b5d2"] # TODO: Figure this out, cannot be empty
                        #object_refs=[self.dummy_organization["standard_id"]] 
                    )
        return report


    def filter_entry(self, entry):
        is_okay = True

        # Category Filter
        # Returns the entry if it contains the keywords in its "category" field
        # Applies to the following feeds: Bleeping Computer
        try:
            if any(keyword.lower() in (entry['tags'][0]['term']).lower() for keyword in self.keyword_filters):
                filtered = entry
            else: # entry does not contain the tags we are looking for
                return False 
        except KeyError: # entry does not have a 'tags' field
            filtered = entry

        # Title-based exclusion using regex
        # Attempts to remove unnecessary entries with titles such as "Top xx in 2025" or ad posts
        # List is not exhaustive, but we try our best!
        exclusions = [
            r'Top \d+ .*', 
            r'Best \d+ .*',  # Best xxx"
            r'.*Sponsored.*',  # Sponsored by ...
            r'Advertisement.*'  # Advertisements Posts
        ]
        for pattern in exclusions:
            regex = re.compile(pattern, re.IGNORECASE)
            if regex.match(filtered.title):
                return False

        return is_okay
        

    def process_rss_feeds(self):
        #self._load_state()

        for url in self.rss_feed_urls:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if True: #self._is_entry_new(entry): TODO: Implement this
                    try:
                        if(self.filter_entry(entry)):
                            report = self._create_stix_report(entry)

                            # Track processed entry
                            self.processed_entries.add(report.get('id'))
                        
                    except Exception as e:
                        #self.helper.log_error(f"Error processing entry: {e}")
                        print(e)

        # Save after processing
        #self._save_state()
    

    def run(self):
        print(f"Running Feed Aggregator - Run")
        NumBefore = len(self.processed_entries)
        self.process_rss_feeds()
        #print(self.processed_entries)
        NumReportsAdded = len(self.processed_entries) - NumBefore
        print(f"Number of reports added: {NumReportsAdded}")
        print(f"Running Feed Aggregator - End")

    def process(self):
        self.run()
        time.sleep(15) #1 min in seconds
    
if __name__ == "__main__":
    try:
        Feed_Aggregator = FeedAggregator()
        while True:
            Feed_Aggregator.process()
    except Exception as e:
        print(e)
        time.sleep(10)
        sys.exit(0)

