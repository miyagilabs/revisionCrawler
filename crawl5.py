SERVICE_URL = "https://gerrit.wikimedia.org/r"
API_URL = "{}/changes/".format(SERVICE_URL)
SHOW_REQUESTED_URLS_FOR_DEBUGGING = True
HTTPS_REQUEST_COUNT = 0

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


def request(relative_url, api_url=API_URL):
	import urllib2
	url = "{}{}".format(api_url, relative_url)
	if SHOW_REQUESTED_URLS_FOR_DEBUGGING:
		logger.debug("Visiting %s" % url)
	global HTTPS_REQUEST_COUNT
	HTTPS_REQUEST_COUNT += 1
	if HTTPS_REQUEST_COUNT % 5 == 0:
		logger.warning("Total HTTPS request made: %d" % HTTPS_REQUEST_COUNT)

	return urllib2.urlopen(url).read()


def request_json(relative_url, api_url=API_URL):
	response = request(relative_url, api_url)
	if response[:4] == ")]}'":
		response = response[4:]

	import json
	return json.loads(response)


def is_merged(change_id):
	response = request_json(change_id)
	return response["status"] == "MERGED"


def revision_numbers(change_id):
	relative_url = "{}/?o=ALL_REVISIONS".format(change_id)
	response = request_json(relative_url)
	numbers = [value["_number"] for value in response['revisions'].values()]
	numbers.sort()
	return numbers


def revision_count(change_id):
	return len(revision_numbers(change_id))


# TODO: Use /content instead of /download (https://github.com/miyagilabs/revisionCrawler/issues/1)
# The parameter file_path should be slash escaped
def download_base_file(change_id, file_path):
	valid_revision_number = revision_numbers(change_id)[0]
	# Note: "parent=1" specifies that we request the file in the parent commit.
	relative_url = "{}/revisions/{}/files/{}/download?parent=1".format(
		change_id,
		valid_revision_number,
		file_path)
	# https://gerrit.wikimedia.org/r/changes/356858/revisions/1/files/SpamBlacklistHooks.php/download?parent=1
	return request(relative_url)


# TODO: Use /content instead of /download (https://github.com/miyagilabs/revisionCrawler/issues/1)
# The parameter file_path should be slash escaped
def download_revision_file(change_id, revision_no, file_path):
	pattern = "{}/revisions/{}/files/{}/download"
	relative_url = pattern.format(change_id, revision_no, file_path)	
	return request(relative_url)


def files_in_revision(change_id, revision_no):
	# url = "https://gerrit.wikimedia.org/r/changes/356858/revisions/1/files/"
	relative_url = "{}/revisions/{}/files/".format(change_id, revision_no)
	response = request_json(relative_url)

	# files = []
	# for key, value in content_in_json.iteritems():
	# 	if key != "/COMMIT_MSG":
	# 		files.append(key)
	# print files

	condition = lambda file_name: file_name != "/COMMIT_MSG"
	return filter(condition, response.keys())
	

# The parameter file_path should be slash escaped
def has_diff(change_id, file_path, revision_no, base_revision_no):
	pattern = "{}/revisions/{}/files/{}/diff?base={}"
	relative_url = pattern.format(
		change_id,
		revision_no,
		file_path,
		base_revision_no)
	response = request_json(relative_url)
	return len(response["content"]) > 1


def slash_escaped_file_path(path):
	return path.replace("/", "%2F")

def unescape_slash(path):
	return path.replace("%2F", "/")	


# The parameter file_path should NOT be slash escaped
def print_file_comments_in_revision(change_id, revision_no, file_path):
	relative_url = "{}/revisions/{}/comments".format(change_id, revision_no)
	response = request_json(relative_url)

	for comment_map in response[file_path]:
		print comment_map["author"]["name"] + "says: \"\n " + comment_map["message"]
		print "\""


# The parameter file_path should NOT be slash escaped
def has_comments_for_file_in_revision(change_id, revision_no, file_path):
	relative_url = "{}/revisions/{}/comments".format(change_id, revision_no)
	response = request_json(relative_url)
	return len(response) > 0 and file_path in response


# The parameter file_path should NOT be slash escaped
def has_comments_for_file(change_id, file_path, cached_revision_nos=None):
	numbers = cached_revision_nos if cached_revision_nos else revision_numbers(change_id)

	for n in numbers:
		if has_comments_for_file_in_revision(change_id, n, file_path):
			return True

	return False


# The parameter file_path should NOT be slash escaped
def build_diff_path(change_id, revision_no, file_path):
	#""	https://gerrit.wikimedia.org/r/#/c/356586/6/modules/gerrit/templates/gerrit.config.erb
	pattern = "{}/#/c/{}/{}/{}"
	return pattern.format(SERVICE_URL, change_id, revision_no, file_path)


def find_interesting_file_paths(change_id):
	logger.info("Examining %s" % change_id)

	if not is_merged(change_id):
		logger.info("Skipping %s (not merged)" % change_id)
		return []

	numbers = revision_numbers(change_id)
	if len(numbers) < 2:
		logger.info("Skipping %s (not revised)" % change_id)
		return []

	# check if there any comments

	first_revision_no = numbers[0]
	last_revision_no = numbers[-1]
	file_paths = files_in_revision(change_id, first_revision_no)
	file_paths = [slash_escaped_file_path(f) for f in file_paths]

	condition = lambda file_path: has_diff(
		change_id, file_path, last_revision_no, first_revision_no)
	interesting_file_paths = filter(condition, file_paths)

	if not interesting_file_paths:
		logger.info("Skipping %s (no interesting file paths - no diff)" % change_id)
		return []

	condition = lambda file_path: has_comments_for_file(
		change_id, unescape_slash(file_path), cached_revision_nos=numbers)
	interesting_file_paths = filter(condition, interesting_file_paths)

	if not interesting_file_paths:
		logger.info("Skipping %s (no interesting file paths - no comments)" % change_id)
		return []

	paths = []
	for f in interesting_file_paths:
		path = build_diff_path(change_id, last_revision_no, f)
		print path
		paths.append(path)

	logger.info("Successfully done with %s" % change_id)
	return paths



def insert_status(db_cursor, change_id, status, detail):
	#import sqlite3
	db_cursor.execute("INSERT INTO changeIdStatus(change_id, status, detail) VALUES ({}, \"{}\", \"{}\")".\
		format(change_id, status, detail))

def insert_corrected_file_url(db_cursor, change_id, url):
	#import sqlite3
	db_cursor.execute("INSERT INTO 	correctedFileUrl(change_id, url) VALUES ({change_id}, \"{url}\")".\
		format(change_id=change_id, url=url))


# DEMO

# print is_merged(356586) # True
# print is_merged(356858) # False

# print revision_count(356586) # 5
# print revision_count(356858) # 2


# print download_base_file(356858, "SpamBlacklistHooks.php")

# print download_revision_file(356858, 2, "SpamBlacklistHooks.php")

# print files_in_revision(356858, 1)

# numbers = revision_numbers(356858)
# print "first revision: {}, last revision: {}".format(numbers[0], numbers[-1]) #1, 2

# numbers = revision_numbers(356586)
# print "first revision: {}, last revision: {}".format(numbers[0], numbers[-1]) #2, 6


# print has_diff(356858, "SpamBlacklistHooks.php", 2, 1)  # True
# print has_diff(356858, "EmailBlacklist.php", 2, 1)  # False

# print has_diff(
#  	356586,
#  	slash_escaped_file_path("modules/gerrit/templates/gerrit.config.erb"),
#  	6,
#  	2) # True

# print has_diff(
#  	356586,
#  	slash_escaped_file_path("modules/gerrit/templates/gerrit.config.erb"),
#  	6,
#  	3) # False


# print_file_comments_in_revision(356858, 1, "SpamBlacklistHooks.php")
# print_file_comments_in_revision(
# 	356586,
# 	3,
# 	"modules/gerrit/templates/gerrit.config.erb")


# print build_diff_path(356586, 6, "modules/gerrit/templates/gerrit.config.erb")

# print has_comments_for_file_in_revision(
# 	356586, 3, "modules/gerrit/templates/gerrit.config.erb") # True
# print has_comments_for_file_in_revision(
# 	356586, 2, "modules/gerrit/templates/gerrit.config.erb") # False
# print has_comments_for_file_in_revision(
# 	356858, 1, "SpamBlacklistHooks.php") # True
# print has_comments_for_file_in_revision(
# 	356858, 2, "SpamBlacklistHooks.php") # False

# print has_comments_for_file(
# 	356586, "modules/gerrit/templates/gerrit.config.erb") # True
# print has_comments_for_file(356858, "SpamBlacklistHooks.php") # True
# print has_comments_for_file(356858, "EmailBlacklist.php") # False

# find_interesting_file_paths(356586)
# find_interesting_file_paths(356858)


# for change_id in range(356585, 356587):
# 	find_interesting_file_paths(change_id)


## Examining if a file has any diffs
# change_id = 356508
# numbers = revision_numbers(change_id)
# first_revision_no = numbers[0]
# last_revision_no = numbers[-1]
# file_paths = files_in_revision(change_id, first_revision_no)
# file_paths = [slash_escaped_file_path(f) for f in file_paths]
# condition = lambda file_path: has_diff(
# 	change_id, file_path, last_revision_no, first_revision_no)
# interesting_file_paths = filter(condition, file_paths)
# print interesting_file_paths



import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--start', metavar='start', dest='start', type=int, required=True,
                    help='an integer for the starting change id')
parser.add_argument('--end', metavar='end', dest='end', type=int, required=True,
                    help='an integer for the final change id')
parser.add_argument('--db', metavar='db', dest='sqlite_file', type=str, required=True,
                    help='db file name')
args = parser.parse_args()



from time import sleep
import time
import urllib2


import sqlite3
db_connection = sqlite3.connect(args.sqlite_file)
db_cursor = db_connection.cursor()

start_time = time.time()
change_id_count = 0
for change_id in range(args.start, args.end + 1):
	paths = []
	change_id_count += 1
	try:
		paths = find_interesting_file_paths(change_id)
	except urllib2.HTTPError as e:
		logger.error("The server failed the request for %s. Error code: %s" % (change_id, e.code))
		insert_status(db_cursor, change_id, "ERROR", e.code)
	except urllib2.URLError as e:
		logger.error("We failed to reach a server for %s. Reason: %s" % (change_id, e.reason))
		insert_status(db_cursor, change_id, "ERROR", e.reason)
	else: 
		insert_status(db_cursor, change_id, "DONE", len(paths))
		for path in paths:
			insert_corrected_file_url(db_cursor, change_id, path)

	logger.warning(
		"HTTPS request average %f" % (HTTPS_REQUEST_COUNT * 1.0 / change_id_count))
	elapsed_time = time.time() - start_time
	rate = HTTPS_REQUEST_COUNT * 1.0 / elapsed_time
	logger.warning("Rate of HTTPS requests: %f per second" % rate)
	logger.warning("Elapsed time is: %f seconds" % elapsed_time)
	sleep(0.4) # Time in seconds.
	db_connection.commit()

# Stats
elapsed_time = time.time() - start_time
logger.warning("Completed")
logger.warning("HTTPS requests made: %d" % HTTPS_REQUEST_COUNT)
logger.warning("Total count of change ids processed: %d" % change_id_count)
logger.warning("Total elapsed time %f" % elapsed_time)
rate = elapsed_time * 1.0 / change_id_count
logger.warning("Time per change id: %f seconds per change id" % rate)
rate = HTTPS_REQUEST_COUNT * 1.0 / elapsed_time
logger.warning("Rate of HTTPS requests: %f per second" % rate)

db_connection.close()

