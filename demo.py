# DEMO

import logging

logger = logging.getLogger('revisionCrawler')
hdlr = logging.FileHandler('/var/tmp/revisionCrawlerDemo.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.DEBUG)
print "Logging started. Run the following to see the log:"
print "tail -f /var/tmp/revisionCrawlerDemo.log | grep INFO"
print "tail -f /var/tmp/revisionCrawlerDemo.log | grep WARNING"
print "tail -f /var/tmp/revisionCrawlerDemo.log | grep DEBUG"


from crawler import Crawler
crawler = Crawler("https://gerrit.wikimedia.org/r", logger, None)

print crawler.is_merged(356586) # True
# print crawler.is_merged(356858) # False

# print crawler.revision_count(356586) # 5
# print crawler.revision_count(356858) # 2


# print crawler.download_base_file(356858, "SpamBlacklistHooks.php")

# print crawler.download_revision_file(356858, 2, "SpamBlacklistHooks.php")

# print crawler.files_in_revision(356858, 1) # [u'SpamBlacklistHooks.php', u'SpamBlacklist.php', u'EmailBlacklist.php']

# numbers = crawler.revision_numbers(356858)
# print "first revision: {}, last revision: {}".format(numbers[0], numbers[-1]) #1, 2

# numbers = crawler.revision_numbers(356586)
# print "first revision: {}, last revision: {}".format(numbers[0], numbers[-1]) #2, 6


# print crawler.has_diff(356858, "SpamBlacklistHooks.php", 2, 1)  # True
# print crawler.has_diff(356858, "EmailBlacklist.php", 2, 1)  # False

# print crawler.has_diff(
#  	356586,
#  	crawler.slash_escaped_file_path("modules/gerrit/templates/gerrit.config.erb"),
#  	6,
#  	2) # True

# print crawler.has_diff(
#  	356586,
#  	crawler.slash_escaped_file_path("modules/gerrit/templates/gerrit.config.erb"),
#  	6,
#  	3) # False


# crawler.print_file_comments_in_revision(356858, 1, "SpamBlacklistHooks.php")
# crawler.print_file_comments_in_revision(
# 	356586,
# 	3,
# 	"modules/gerrit/templates/gerrit.config.erb")


# # https://gerrit.wikimedia.org/r/#/c/356586/6/modules/gerrit/templates/gerrit.config.erb
# print crawler.build_diff_path(356586, 6, "modules/gerrit/templates/gerrit.config.erb")


# print crawler.has_comments_for_file_in_revision(
# 	356586, 3, "modules/gerrit/templates/gerrit.config.erb") # True
# print crawler.has_comments_for_file_in_revision(
# 	356586, 2, "modules/gerrit/templates/gerrit.config.erb") # False
# print crawler.has_comments_for_file_in_revision(
# 	356858, 1, "SpamBlacklistHooks.php") # True
# print crawler.has_comments_for_file_in_revision(
# 	356858, 2, "SpamBlacklistHooks.php") # False

# print crawler.has_comments_for_file(
# 	356586, "modules/gerrit/templates/gerrit.config.erb") # True
# print crawler.has_comments_for_file(356858, "SpamBlacklistHooks.php") # True
# print crawler.has_comments_for_file(356858, "EmailBlacklist.php") # False


# from corrected_change_crawler import CorrectedChangeCrawler
# crawler = CorrectedChangeCrawler(crawler, None, None, logger)
# # https://gerrit.wikimedia.org/r/#/c/356586/6/modules%2Fgerrit%2Ftemplates%2Fgerrit.config.erb
# crawler.find_interesting_file_paths(356586)
# # Empty
# crawler.find_interesting_file_paths(356858)


# from corrected_change_crawler import CorrectedChangeCrawler
# crawler = CorrectedChangeCrawler(crawler, None, None, logger)
# for change_id in range(356585, 356587):
# 	crawler.find_interesting_file_paths(change_id)


# # Examining if a file has any diffs
# change_id = 356508
# numbers = crawler.revision_numbers(change_id)
# first_revision_no = numbers[0]
# last_revision_no = numbers[-1]
# file_paths = crawler.files_in_revision(change_id, first_revision_no)
# file_paths = [crawler.slash_escaped_file_path(f) for f in file_paths]
# print file_paths
# condition = lambda file_path: crawler.has_diff(
# 	change_id, file_path, last_revision_no, first_revision_no)
# interesting_file_paths = filter(condition, file_paths)
# print interesting_file_paths