
# CHANGE => IS MERGED


def request_json(url):
	import urllib2
	response = urllib2.urlopen(url).read()
	if response[:4] == ")]}'":
		response = response[4:]

	import json
	return json.loads(response)



def is_merged(change_id):
	url = "https://gerrit.wikimedia.org/r/changes/{}".format(change_id)
	response = request_json(url)
	return response["status"] == "MERGED"

print is_merged(356586) # True
print is_merged(356858) # False
