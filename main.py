import urllib2
from xml.dom import minidom
import os
import webapp2
import jinja2
import logging
import random
from google.appengine.api import memcache
from google.appengine.ext import db

jinja_env = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

PAGE_RE = r'(/(?:[a-zA-Z0-9_-\+]+/?)*)'

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a,**kw)

    def render_str(self,template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)
    
    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))


class Music(db.Model):
	artist=db.StringProperty(required=True)
	song=db.StringProperty(required=True)
	video=db.StringProperty(required=True)


API_KEY= '51293239750eea5095511e23b3107e31'

def get_music(user):
		

	
		query="http://ws.audioscrobbler.com/2.0/?method=user.gettoptracks&user="+user+"&api_key="+API_KEY+"&limit=5"
		logging.error("%s"%query)
		page=urllib2.urlopen(query)
		xml=minidom.parseString(page.read())
		urls=xml.getElementsByTagName("url")
		lista=[]
		for x in range(len(urls)):
			if x%2==0:
				artist,song=urls[x].childNodes[0].nodeValue[25:].split('/_/')
				search= artist +'/'+ song
				lista.append(search)
		random.shuffle(lista)
		return lista

def get_video(search):
	logging.error("search=%s"%search)
	artist,song=search.split('/')
	data=memcache.get(search)
	if data is not None:
		return data
	else:

		query='http://gdata.youtube.com/feeds/api/videos?q="'+artist+'+'+song+'+official+video"+-mashup+-lyrics+-collaboration+-pirates+-cover+-making+-fanmade&max-results=1&v=2&format=5'
		logging.error("%s"%query)
		page=urllib2.urlopen(query)
		xml=minidom.parseString(page.read())
		if  xml.getElementsByTagName("yt:videoid")!= []:
			data=xml.getElementsByTagName("yt:videoid")[0].childNodes[0].nodeValue
		else:
			data=" "
		memcache.set(search,data)
		logging.error("search=%s"%search)
		logging.error("data=%s"%data)
		m=Music(artist=artist,song=song,video=data)
		m.put()
		return data


def get_artists(user):

			
		query="http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user="+user+"&api_key="+API_KEY+"&limit=50"
		logging.error("%s"%query)
		page=urllib2.urlopen(query)
		xml=minidom.parseString(page.read())
		urls=xml.getElementsByTagName("url")
		artists=[]
		for x in range(len(urls)):
			artists.append(urls[x].childNodes[0].nodeValue[25:])
		return artists

def get_tracks(artist,n):
	
	lista=memcache.get(artist)
	
	if lista is not None and len(lista)>=n:
		return lista

	else:
			
		query="http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist="+artist+"&api_key="+API_KEY+"&limit=%s"%n
		logging.error("%s"%query)
		page=urllib2.urlopen(query)
		xml=minidom.parseString(page.read())
		
		tracks=xml.getElementsByTagName("track")
		lista=[]
		for x in range(len(tracks)):
			artista,song=tracks[x].childNodes[11].childNodes[0].nodeValue[25:].split('/_/')
			search= artist +'/'+ song
			lista.append(search)
		logging.error("lista=%s"%len(lista))
		memcache.set(artist,lista)
		return get_tracks(artist,n)




class MainPage(Handler):
	 def render_form(self):
	 	self.render("form.html")
	 def render_videos(self,url=""):
	 	self.render("video.html",url=url)

	 def get(self):
	 	self.render_form()

	 def post(self):
	 	user=self.request.get('user')
	 	list_of_plays=get_music(user)
	 	playlist=""
	 	youtube_query="http://www.youtube.com/embed/"+get_video(list_of_plays.pop())+"?"
	 	for i in list_of_plays:
	 		amv=i
	 		video_id=get_video(amv)
	 		logging.error("video_id=%s"%video_id)
	 		if len(video_id)>2:
	 			playlist=playlist+video_id+","
	 	youtube_query=youtube_query+"playlist="+playlist+"&autoplay=1"
	 	self.render_videos(youtube_query)


class GroupPage(Handler):
	def render_group(self):
		self.render("group.html")

	def get(self,resource):
		data={'group':str(urllib2.unquote(resource))}
		self.render_group()



class MainPage2(Handler):
	 def render_form(self):
	 	self.render("form.html")
	 def render_videos(self,url=""):
	 	self.render("video.html",url=url)

	 def get(self):
	 	self.render_form()

	 def post(self):
	 	user=self.request.get('user')
	 	artists=get_artists(user)
	 	tracks=[]
	 	for artist in artists:
	 		for i in get_tracks(artist,10):
	 			tracks.append(i)
	 	
	 	random.shuffle(tracks)

	 	

	 	playlist=""
	 	youtube_query="http://www.youtube.com/embed/"+get_video(tracks.pop())+"?"
	 	x=0
	 	for i in tracks:
	 		if x>=150:
	 			break
	 		amv=i
	 		video_id=get_video(amv)
	 		logging.error("video_id=%s"%video_id)
	 		if len(video_id)>2:
	 			playlist=playlist+video_id+","
	 			x=x+1
	 			logging.error("x=%s"%x)
	 	youtube_query=youtube_query+"playlist="+playlist+"&autoplay=1"

	 	logging.error("%s"%youtube_query)

	 	self.render_videos(youtube_query)



app = webapp2.WSGIApplication([('/', MainPage),('/group' + PAGE_RE, GroupPage),('/2', MainPage2)], debug=True)





