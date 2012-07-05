import urllib2
from xml.dom import minidom

API_KEY= '51293239750eea5095511e23b3107e31'

def get_music(user):
        query="http://ws.audioscrobbler.com/2.0/?method=user.gettoptracks&user="+user+"&api_key="+API_KEY
        page=urllib2.urlopen(query)
        xml=minidom.parseString(page.read())
        urls=xml.getElementsByTagName("url")
        lista=[]
        for x in range(len(urls)):
                if x%2==0:
                        artist,song=urls[x].childNodes[0].nodeValue[25:].split('/_/')
                        search='"'+ artist + '"' +"+"+ '"' +song+ '"'
                        lista.append(search)
        return lista

def get_video(search):
        query="https://gdata.youtube.com/feeds/api/videos?q="+search+"&max-results=1&hd=true&v=2&format=5&category=music"
        print query
        page=urllib2.urlopen(query)
        xml=minidom.parseString(page.read())
        if  xml.getElementsByTagName("yt:videoid")!= []:
                return xml.getElementsByTagName("yt:videoid")[0].childNodes[0].nodeValue
        return " "


user='prunk'
list_of_plays=get_music(user)
playlist=""
youtube_query="http://www.youtube.com/embed/"+get_video(list_of_plays.pop())+"?"
for i in get_music(user):
        playlist=playlist+get_video(i)+","


youtube_query=youtube_query+"playlist="+playlist+"&autoplay=1"

print youtube_query
