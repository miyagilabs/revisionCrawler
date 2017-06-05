import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--start', metavar='start', dest='start', type=int, required=True,
                    help='an integer for the starting change id')
parser.add_argument('--end', metavar='end', dest='end', type=int, required=True,
                    help='an integer for the final change id')
parser.add_argument('--db', metavar='db', dest='sqlite_file', type=str, required=True,
                    help='db file name')
parser.add_argument('--service', metavar='service', dest='service_url', type=str, required=True,
                    help='service url such as https://gerrit.wikimedia.org/r')
args = parser.parse_args()


import logging
logger = logging.getLogger('revisionCrawler')
hdlr = logging.FileHandler('/var/tmp/revisionCrawler.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.DEBUG)
print "Logging started. Run the following to see the log:"
print "tail -f /var/tmp/revisionCrawler.log | grep INFO\n\n"
print "tail -f /var/tmp/revisionCrawler.log | grep WARNING\n\n"
print "tail -f /var/tmp/revisionCrawler.log | grep DEBUG\n\n"


import sqlite3
db_connection = sqlite3.connect(args.sqlite_file)
db_cursor = db_connection.cursor()

from crawler import Crawler
crawler = Crawler(args.service_url, logger, db_cursor)

from corrected_change_crawler  import CorrectedChangeCrawler
corrected_change_crawler = CorrectedChangeCrawler(crawler, db_connection, db_cursor, logger)
corrected_change_crawler.crawl(args.start, args.end)

db_connection.close()

