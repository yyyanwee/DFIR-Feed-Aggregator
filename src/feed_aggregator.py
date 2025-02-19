import json
import os
import re
import sys
import time
import yaml
import feedparser
import dateparser
import stix2
from pycti import OpenCTIConnectorHelper, Report


"""
TODO:
1. Different feed may contain the same information but since they are from different sources, they are considered different.
2. 
"""

class FeedAggregator:
    def __init__(self):
        config_file_path = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
        config = (
            yaml.load(open(config_file_path), Loader=yaml.SafeLoader)
            if os.path.isfile(config_file_path)
            else {}
        )

        #hardcode testing version
        '''
        self.config ={
            "OPENCTI_URL": "http://opencti:8080",
            "OPENCTI_TOKEN": "d4f4d2b0-6b3b-4f6b-8d2d-3f8f6c6d8b4d",
            "feed_urls": [("Bleeping Computer","https://www.bleepingcomputer.com/feed/"), ("The Hackers News","https://feeds.feedburner.com/TheHackersNews")],
            "keyword_filters": ["security"],
        }
        '''

        self.helper = OpenCTIConnectorHelper(config) 
        self.rss_feed_urls = config["feed_urls"]
        self.keyword_filters = config["keyword_filters"]
        
        # to track previously processed entries
        self.processed_entries = set()
        self.rejected_entries = set()

        self.dummy_organization = self.helper.api.identity.create(
            type="Organization",
            name="DUMMY",
            description="Dummy organization which can be used in various unknown contexts.",
        )

    def _get_state(self):
        #Loads previously processed entry identifiers from connector state
        state = self.helper.get_state()
        if state and "processed_entries" in state:
            self.processed_entries = set(state["processed_entries"])

    def _save_state(self):
        #Saves current processed entries to connector state.
        self.helper.set_state({
            "processed_entries": list(self.processed_entries)
        })
    
    #Helper function
    def _create_stix_report(self, entry: dict[str, any], source) -> stix2.Report:
        #Convert RSS entry into a STIX2 Report object.
        report_name = entry.title
        report_date = dateparser.parse(entry.published)
        external_reference = stix2.ExternalReference(source_name=source, url=entry.link)

        report = stix2.Report(
                        id=Report.generate_id(report_name, report_date),
                        name=report_name,
                        published=report_date,
                        description = entry["summary"],
                        external_references=[external_reference],
                        # TODO: Figure this out, cannot be empty
                        object_refs=[self.dummy_organization["standard_id"]] 
                    )
        print(report)
        print("")
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

        # For Bleeping Computer, the author tag contains information that it's sponsored
        # e.g. author = "Sponsored by TruGrid"
        try:
            if "sponsored" in filtered['author'].lower():
                return False
        except KeyError: # entry does not have an 'author' field
            pass

        # Title-based exclusion using regex
        # Attempts to remove unnecessary entries with titles such as "Top xx in 2025" or ad posts
        # List is not exhaustive, but we try our best!
        non_event_title_starters = [
            # How-to and guides
            r'how\s+to',
            r'guide(?:s)?\s+(?:to|for)',
            r'(?:quick\s+)?tutorial',
            
            # Numbered lists and rankings
            r'\d+\s+(?:ways|steps|tips|tools|tricks|things)',
            r'top\s+\d+',
            r'best\s+\d+',
            
            # Educational/informational
            r'understanding',
            r'(?:what|when|why|where)\s+(?:is|are|you|to)',
            r'(?:protecting|securing|safeguarding)',
            r'introduction\s+to',
            
            # Best practices and recommendations
            r'best\s+practices',
            r'essential\s+(?:tips|practices|steps)',
            r'why\s+you\s+should',
            
            # Summaries and roundups
            r'weekly\s+(?:recap|roundup|digest)',
            r'month(?:ly)?\s+in\s+review',
            r'(?:daily|weekly|monthly)\s+(?:security\s+)?(?:update|summary)',
            
            # Promotional content
            r'sponsored(?:\s+post)?:?',
            r'advertis(?:ement|ing):?',
            r'\[sponsored\]',
            
            # Resource collections
            r'resource(?:s)?\s+(?:guide|list)',
            r'checklist(?:s)?\s+for',
        ]

        for pattern in non_event_title_starters:
            regex = re.compile(pattern, re.IGNORECASE)
            if regex.search(filtered["title"]):
                return False

        # Summary-based exclusions
        # Remove entries based on specific keywords present in the summary
        non_event_desc_exclusions = {
            'guide','best practices','tips',
            'strategy','adoption','basics',
            'introduction',"weekly recap", "trends", "sponsored"}
        try:
            summary_set = set(filtered["summary"].split())
            if summary_set.intersection(non_event_desc_exclusions):
                return False
        except KeyError:
            pass
        
        return is_okay
        

    def process_rss_feeds(self):
        # Get the set of already processed entries
        self._get_state()

        for detail in self.rss_feed_urls:
            feed = feedparser.parse(detail[1])
            for entry in feed["entries"]:
                try:
                    if(self.filter_entry(entry)):
                        report = self._create_stix_report(entry, detail[0])
                        # Track processed entry id to prevent duplicates
                        self.processed_entries.add(report.get('id'))

                        # send report to OpenCTI
                        bundle = stix2.Bundle(objects=report).serialize()
                        self.helper.send_stix2_bundle(bundle, entities_types=self.helper.connect_scope)

                        # Save after sending
                        self._save_state()
                    else:
                        self.rejected_entries.add(entry)
                except Exception as e:
                        self.helper.log_error(f"Error processing entry: {e}")
                        print(e)

        # Final save after processing
        self._save_state()


    def run(self):
        print(f"Running Feed Aggregator - Run")
        # NumBefore = len(self.processed_entries)
        self.process_rss_feeds()

        # NumReportsAdded = len(self.processed_entries) - NumBefore
        # print(f"Number of reports added: {NumReportsAdded}")

        # #For ease of debugging/tracking
        # rejected_entries_dict = {"rejected_entries": list(self.rejected_entries)}
        # json.dump(rejected_entries_dict["rejected_entries"], open("processed_entries.txt", "w"))

        # print("Rejected Entries\n")
        # print(f"Number of rejected entries: {len(self.rejected_entries)}")
        # print(f"Running Feed Aggregator - End")

    def process(self):
        self.run()
        time.sleep(120) #Set to 12 hours before going live (43200)
    
if __name__ == "__main__":
    try:
        Feed_Aggregator = FeedAggregator()
        while True:
            Feed_Aggregator.process()
    except Exception as e:
        print(e)
        time.sleep(10)
        sys.exit(0)

