class Crawler:
	SHOW_REQUESTED_URLS_FOR_DEBUGGING = True

	def __init__(self, service_url, logger, db_cursor):
		self.service_url = service_url # e.g., "https://gerrit.wikimedia.org/r"
		self.api_url = "{}/changes/".format(self.service_url)
		self.logger = logger
		self.https_request_count = 0
		self.db_cursor = db_cursor


	def request(self, relative_url):
		import urllib2
		url = "{}{}".format(self.api_url, relative_url)
		if Crawler.SHOW_REQUESTED_URLS_FOR_DEBUGGING:
			self.logger.debug("Visiting %s" % url)
		self.https_request_count += 1
		if self.https_request_count % 5 == 0:
			self.logger.warning("Total HTTPS request made: %d" % self.https_request_count)

		return urllib2.urlopen(url).read()


	# The parameter file_path should NOT be slash escaped
	def build_diff_path(self, change_id, revision_no, file_path):
		#""	https://gerrit.wikimedia.org/r/#/c/356586/6/modules/gerrit/templates/gerrit.config.erb
		pattern = "{}/#/c/{}/{}/{}"
		return pattern.format(self.service_url, change_id, revision_no, file_path)


	def request_json(self, relative_url):
		response = self.request(relative_url)
		if response[:4] == ")]}'":
			response = response[4:]

		import json
		return json.loads(response)


	def is_merged(self, change_id):
		response = self.request_json(change_id)
		return response["status"] == "MERGED"


	def revision_numbers(self, change_id):
		relative_url = "{}/?o=ALL_REVISIONS".format(change_id)
		response = self.request_json(relative_url)
		numbers = [value["_number"] for value in response['revisions'].values()]
		numbers.sort()
		return numbers


	def revision_count(self, change_id):
		return len(self.revision_numbers(change_id))


	# TODO: Use /content instead of /download (https://github.com/miyagilabs/revisionCrawler/issues/1)
	# The parameter file_path should be slash escaped
	def download_base_file(self, change_id, file_path):
		valid_revision_number = self.revision_numbers(change_id)[0]
		# Note: "parent=1" specifies that we request the file in the parent commit.
		relative_url = "{}/revisions/{}/files/{}/download?parent=1".format(
			change_id,
			valid_revision_number,
			file_path)
		# https://gerrit.wikimedia.org/r/changes/356858/revisions/1/files/SpamBlacklistHooks.php/download?parent=1
		return self.request(relative_url)


	# TODO: Use /content instead of /download (https://github.com/miyagilabs/revisionCrawler/issues/1)
	# The parameter file_path should be slash escaped
	def download_revision_file(self, change_id, revision_no, file_path):
		pattern = "{}/revisions/{}/files/{}/download"
		relative_url = pattern.format(change_id, revision_no, file_path)	
		return self.request(relative_url)


	def files_in_revision(self, change_id, revision_no):
		# url = "https://gerrit.wikimedia.org/r/changes/356858/revisions/1/files/"
		relative_url = "{}/revisions/{}/files/".format(change_id, revision_no)
		response = self.request_json(relative_url)

		# files = []
		# for key, value in content_in_json.iteritems():
		# 	if key != "/COMMIT_MSG":
		# 		files.append(key)
		# print files

		condition = lambda file_name: file_name != "/COMMIT_MSG"
		return filter(condition, response.keys())
	

	# The parameter file_path should be slash escaped
	def has_diff(self, change_id, file_path, revision_no, base_revision_no):
		pattern = "{}/revisions/{}/files/{}/diff?base={}"
		relative_url = pattern.format(
			change_id,
			revision_no,
			file_path,
			base_revision_no)
		response = self.request_json(relative_url)
		return len(response["content"]) > 1


	def slash_escaped_file_path(self, path):
		return path.replace("/", "%2F")


	def unescape_slash(self, path):
		return path.replace("%2F", "/")	


	# The parameter file_path should NOT be slash escaped
	def print_file_comments_in_revision(self, change_id, revision_no, file_path):
		relative_url = "{}/revisions/{}/comments".format(change_id, revision_no)
		response = self.request_json(relative_url)

		for comment_map in response[file_path]:
			print comment_map["author"]["name"] + "says: \"\n " + comment_map["message"]
			print "\""


	# The parameter file_path should NOT be slash escaped
	def has_comments_for_file_in_revision(self, change_id, revision_no, file_path):
		relative_url = "{}/revisions/{}/comments".format(change_id, revision_no)
		response = self.request_json(relative_url)
		return len(response) > 0 and file_path in response


	# The parameter file_path should NOT be slash escaped
	def has_comments_for_file(self, change_id, file_path, cached_revision_nos=None):
		numbers = cached_revision_nos if cached_revision_nos else self.revision_numbers(change_id)

		for n in numbers:
			if self.has_comments_for_file_in_revision(change_id, n, file_path):
				return True

		return False


	def insert_status(self, change_id, status, detail):
		self.db_cursor.execute(
			"INSERT INTO changeIdStatus(change_id, status, detail) VALUES ({}, \"{}\", \"{}\")".\
			format(change_id, status, detail))


	def insert_corrected_file_url(self, change_id, url):
		self.db_cursor.execute(
			"INSERT INTO 	correctedFileUrl(change_id, url) VALUES ({change_id}, \"{url}\")".\
			format(change_id=change_id, url=url))