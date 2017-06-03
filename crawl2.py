import urllib2

# THIS IS WHAT IT IS DOING
# CHANGE => REVISION 1 COMMENTS => 

DEBUG = False

project_url = "https://gerrit.wikimedia.org/r"
change_id = "356858"
comments_url = project_url + "/changes/" + change_id + "/revisions/1/comments"
comments_content = urllib2.urlopen(comments_url).read()


# The response strangely has 4 characters ")]}'" that breaks JSON parsing.
if comments_content[:4] == ")]}'":
	comments_content = comments_content[4:]

if DEBUG:
	print comments_content

import json
comments_content_in_json = json.loads(comments_content)

print len(comments_content_in_json["SpamBlacklistHooks.php"])

for comment_map in comments_content_in_json["SpamBlacklistHooks.php"]:
	print comment_map["author"]["name"] + "says: \"\n " + comment_map["message"]
	print "\""





