class CorrectedChangeCrawler:
	def __init__(self, crawler, db_connection, db_cursor, logger):
		self.logger = logger
		self.crawler = crawler
		self.db_connection = db_connection
		self.db_cursor = db_cursor

	def find_interesting_file_paths(self, change_id):
		self.logger.info("Examining %s" % change_id)

		if not self.crawler.is_merged(change_id):
			self.logger.info("Skipping %s (not merged)" % change_id)
			return []

		numbers = self.crawler.revision_numbers(change_id)
		if len(numbers) < 2:
			self.logger.info("Skipping %s (not revised)" % change_id)
			return []

		# check if there any comments

		first_revision_no = numbers[0]
		last_revision_no = numbers[-1]
		file_paths = self.crawler.files_in_revision(change_id, first_revision_no)
		file_paths = [self.crawler.slash_escaped_file_path(f) for f in file_paths]

		condition = lambda file_path: self.crawler.has_diff(
			change_id, file_path, last_revision_no, first_revision_no)
		interesting_file_paths = filter(condition, file_paths)

		if not interesting_file_paths:
			self.logger.info("Skipping %s (no interesting file paths - no diff)" % change_id)
			return []

		condition = lambda file_path: self.crawler.has_comments_for_file(
			change_id, self.crawler.unescape_slash(file_path), cached_revision_nos=numbers)
		interesting_file_paths = filter(condition, interesting_file_paths)

		if not interesting_file_paths:
			self.logger.info("Skipping %s (no interesting file paths - no comments)" % change_id)
			return []

		paths = []
		for f in interesting_file_paths:
			path = self.crawler.build_diff_path(change_id, last_revision_no, f)
			print path
			paths.append(path)

		self.logger.info("Successfully done with %s" % change_id)
		return paths


	def crawl(self, start_change_id, end_change_id):
		from time import sleep
		import time
		import urllib2

		start_time = time.time()
		change_id_count = 0
		for change_id in range(start_change_id, end_change_id + 1):
			paths = []
			change_id_count += 1
			try:
				paths = self.find_interesting_file_paths(change_id)
			except urllib2.HTTPError as e:
				self.logger.error("The server failed the request for %s. Error code: %s" % (change_id, e.code))
				self.crawler.insert_status(change_id, "ERROR", e.code)
			except urllib2.URLError as e:
				self.logger.error("We failed to reach a server for %s. Reason: %s" % (change_id, e.reason))
				self.crawler.insert_status(change_id, "ERROR", e.reason)
			else:
				self.crawler.insert_status(change_id, "DONE", len(paths))
				for path in paths:
					self.crawler.insert_corrected_file_url(change_id, path)

			# Latest Stats
			self.logger.warning(
				"HTTPS request average %f" % (self.crawler.https_request_count * 1.0 / change_id_count))
			elapsed_time = time.time() - start_time
			rate = self.crawler.https_request_count * 1.0 / elapsed_time
			self.logger.warning("Rate of HTTPS requests: %f per second" % rate)
			self.logger.warning("Elapsed time is: %f seconds" % elapsed_time)
			per_change_rate = elapsed_time * 1.0 / change_id_count
			self.logger.warning("Time per change id: %f seconds per change id" % per_change_rate)

			sleep(0.4) # Time in seconds.
			self.db_connection.commit()

		# Final Stats
		elapsed_time = time.time() - start_time
		self.logger.warning("Completed")
		self.logger.warning("HTTPS requests made: %d" % self.crawler.https_request_count)
		self.logger.warning("Total count of change ids processed: %d" % change_id_count)
		self.logger.warning("Total elapsed time %f" % elapsed_time)
		rate = elapsed_time * 1.0 / change_id_count
		self.logger.warning("Time per change id: %f seconds per change id" % rate)
		rate = self.crawler.https_request_count * 1.0 / elapsed_time
		self.logger.warning("Rate of HTTPS requests: %f per second" % rate)
