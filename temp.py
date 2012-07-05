import urllib2
from xml.dom import minidom

def get_musiclist(user):

	query="http://ws.audioscrobbler.com/2.0/?method=user.gettoptracks&user="+user+"&api_key=51293239750eea5095511e23b3107e31"
	p=urllib2.urlopen(query)
	xml=minidom.parseString(p.read())
	
	t=xml.getElementsByTagName("url")
	lista=[]
	for x in range(len(t)):
		if x%2==0:
			track=xml.getElementsByTagName("url")[x].childNodes[0].nodeValue[25:]
			name,artist=track.split('/_/')
			lista.append(name+"+"+artist)

	return lista


lista=[]

for i in get_musiclist("prunk"):
	query="https://gdata.youtube.com/feeds/api/videos?q="+i+"&hd=true&v=2&max-results=1&orderby=rating"
	p=urllib2.urlopen(query)
	xml=minidom.parseString(p.read())
	if xml.getElementsByTagName("yt:videoid")!=[]:
		lista.append(xml.getElementsByTagName("yt:videoid")[0].childNodes[0].nodeValue)
	
search=""
for i in lista:
	search=search+i+","

print search
