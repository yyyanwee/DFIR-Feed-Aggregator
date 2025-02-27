from datetime import datetime
from zoneinfo import ZoneInfo
import os
from pathlib import Path
import re
import sys
import time
import traceback
import yaml
import feedparser
import dateparser
import stix2
from pycti import OpenCTIConnectorHelper, Report, get_config_variable

"""
Some Limitaations:
1. Different feeds may contain the same information but since they are from different sources, they are considered different in OpenCTI. 
2. 
"""

class FeedAggregator:
    def __init__(self):
        config_file_path = Path(__file__).parents[1].joinpath("config.yml")
        config = (
            yaml.load(open(config_file_path), Loader=yaml.FullLoader)
            if os.path.isfile(config_file_path)
            else {}
        )

        self.helper = OpenCTIConnectorHelper(config) 
        rss_feed_urls = get_config_variable("FEED_URLS", ["feed_aggregator", "FEED_URLS"],config, False, None)
        keyword_filters = get_config_variable("FEED_KEYWORDS", ["feed_aggregator", "FEED_KEYWORDS"],config, False, None)

        self.rss_feed_urls = [tuple(item.split("|")) for item in rss_feed_urls.split(",")]
        self.keyword_filters = keyword_filters.split(",")

        # to track previously processed entries
        self.processed_entries = set()
        self.rejected_entries = set()

        self.dummy_organization = self.helper.api.identity.create(
            type="Organization",
            name="DUMMY",
            description="Dummy organization which can be used in various unknown contexts.",
        )

    def _get_state(self):
        #Loads previously processed data from connector state
        state = self.helper.get_state()
        if state and "processed_entries" in state:
            self.processed_entries = set(state["processed_entries"])
        if state and "rejected_entries" in state:
            self.rejected_entries = set(state["rejected_entries"])

    def _save_state(self):
        #Saves processed and rejected entries to connector state.
        self.helper.set_state({
            "processed_entries": list(self.processed_entries), "rejected_entries": list(self.rejected_entries)
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
                        report_types=["threat-report"],
                        # Using a dummy reference
                        object_refs=[self.dummy_organization["standard_id"]] 
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
                        self.rejected_entries.add(entry.link)
                        self._save_state()
                except Exception as e:
                        self.helper.log_error(f"Error processing entry: {e}")
                        print(e)

        # Final save after processing
        self._save_state()


    def run(self):
        print(f"Running Feed Aggregator - {datetime.now(ZoneInfo("Asia/Singapore")).strftime("%d-%m-%Y %H:%M:%S")}",flush=True)
        NumBefore = len(self.processed_entries)
        self.process_rss_feeds()
        NumReportsAdded = len(self.processed_entries) - NumBefore
        print(f"Number of reports added this run: {NumReportsAdded}",flush=True)
        print(f"Total Number of rejected entries: {len(self.rejected_entries)}",flush=True)
        print(f"Rejected Entries: {self.rejected_entries}", flush=True)
        print(f"Feed Aggregator Run End",flush=True)

    def process(self):
        self.run()
        time.sleep(43200) #Set to 12 hours - can convert into a config
    
if __name__ == "__main__":
    try:
        Feed_Aggregator = FeedAggregator()
        while True:
            Feed_Aggregator.process()
    except Exception as e:
        print(e)
        traceback.print_exc()
        time.sleep(10)
        sys.exit(0)

