import urllib2

# THIS IS WHAT IT IS DOING
# CHANGE => REVISION COUNT

DEBUG = True

project_url = "https://android-review.googlesource.com"
change_id = "8657"
all_revisions_url = project_url + "/changes/" + change_id + "/?o=ALL_REVISIONS"
all_revisions_content = urllib2.urlopen(all_revisions_url).read()


# The response strangely has 4 characters ")]}'" that breaks JSON parsing.
if all_revisions_content[:4] == ")]}'":
	all_revisions_content = all_revisions_content[4:]

if DEBUG:
	print all_revisions_content

import json
all_revisions_content_in_json = json.loads(all_revisions_content)


revision_count = len(all_revisions_content_in_json['revisions'])
if DEBUG:
	print revision_count



