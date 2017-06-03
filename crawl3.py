import urllib2

# THIS IS WHAT IT IS DOING:
# Change => File names in Revision 1 => Files that change from Revision 1 to Revision 2


# BY THE WAY:
# This is how you get the base version of a file (notice the parent=1 parameter at the end)
# https://gerrit.wikimedia.org/r/changes/356858/revisions/1/files/SpamBlacklistHooks.php/download?parent=1

DEBUG = False



# List files in Revision1
url = "https://gerrit.wikimedia.org/r/changes/356858/revisions/1/files/"
content = urllib2.urlopen(url).read()
# The response strangely has 4 characters ")]}'" that breaks JSON parsing.
if content[:4] == ")]}'":
	content = content[4:]

import json
content_in_json = json.loads(content)

# files = []
# for key, value in content_in_json.iteritems():
# 	if key != "/COMMIT_MSG":
# 		files.append(key)
# print files

condition = lambda file_name: file_name != "/COMMIT_MSG"
files = filter(condition, content_in_json.keys())
print files



#For every file in Revision1
#	Check if diff(Revision1 and RevisionN) is not empty

# Is there a diff in a file between two revisions:
def has_diff(file_relative_url, target, source):
	# TODO: convert each slash in file_relative_url to %2F
	url = "https://gerrit.wikimedia.org/r/changes/356858/revisions/"+source+"/files/" + file_relative_url + "/diff?base=" + target
	content = urllib2.urlopen(url).read()
	if content[:4] == ")]}'":
		content = content[4:]

	if DEBUG:
		print content

	import json
	content_in_json = json.loads(content)
	if DEBUG:
		print content_in_json
	has_diff = len(content_in_json["content"]) > 1
	print has_diff
	return has_diff


condition = lambda f : has_diff(f, "1", "2")
corrected_files = filter(condition, files)
print corrected_files
