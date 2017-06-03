SERVICE_URL = "https://gerrit.wikimedia.org/r"
API_URL = "{}/changes/".format(SERVICE_URL)


def request(relative_url, api_url=API_URL):
	import urllib2
	url = "{}{}".format(api_url, relative_url)
	# print url
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


# TODO: https://github.com/miyagilabs/revisionCrawler/issues/1
def download_base_file(change_id, file_name):
	valid_revision_number = revision_numbers(change_id)[0]
	# Note: "parent=1" specifies that we request the file in the parent commit.
	relative_url = "{}/revisions/{}/files/{}/download?parent=1".format(
		change_id,
		valid_revision_number,
		file_name)
	# https://gerrit.wikimedia.org/r/changes/356858/revisions/1/files/SpamBlacklistHooks.php/download?parent=1
	return request(relative_url)


# TODO: https://github.com/miyagilabs/revisionCrawler/issues/1
def download_revision_file(change_id, revision_no, file_name):
	pattern = "{}/revisions/{}/files/{}/download"
	relative_url = pattern.format(change_id, revision_no, file_name)	
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


def print_file_comments_in_revision(change_id, revision_no, file_path):
	relative_url = "{}/revisions/{}/comments".format(change_id, revision_no)
	response = request_json(relative_url)

	for comment_map in response[file_path]:
		print comment_map["author"]["name"] + "says: \"\n " + comment_map["message"]
		print "\""


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
# print has_diff(356858, "EmailBlacklist.php.php", 2, 1)  # False

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