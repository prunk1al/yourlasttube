import urllib2
from xml.dom import minidom
import os
import webapp2
import jinja2
import logging
import random
import string
from google.appengine.api import memcache
from google.appengine.ext import db

jinja_env = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

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
		
		query="http://ws.audioscrobbler.com/2.0/?method=user.gettoptracks&user="+user+"&api_key="+API_KEY+"&limit=100"
		logging.error("%s"%query)
		page=urllib2.urlopen(query)
		xml=minidom.parseString(page.read())
		urls=xml.getElementsByTagName("url")
		lista=[]
		for x in range(len(urls)):
			if x%2==0:
				artist,song=urls[x].childNodes[0].nodeValue[25:].split('/_/')
				search= [artist,song]
				lista.append(search)
		return lista


class MainPage(Handler):
	def render_front(self,tracks=""):
		self.render("front.html",tracks=tracks)

	def get(self):
		tracks=memcache.get("select * from Music where video != ' '")

                if tracks is None:
                        tracks=list(db.GqlQuery("select * from Music where video != ' ' limit 10"))
                        for i in tracks:
                                i.artist=i.artist.replace("+","-")
                                i.song=i.song.replace("+","-")
                        memcache.set("select * from Music where video != ' '",tracks)
                self.render_front(tracks)
class BandPage(Handler):

	def render_band(self,artist="",tracks=""):
		self.render("band.html",artist=artist,tracks=tracks)

	def get(self,resource):
		artist=str(urllib2.unquote(resource))[1:]
		tracks=memcache.get("select * from Music where artist='%s'" % artist)

		if tracks is None:
			tracks=list(db.GqlQuery("select * from Music where artist='%s'" % artist))
			for i in tracks:
				i.artist=i.artist.replace("+","-")
				i.song=i.song.replace("+","-")
			memcache.set("select * from Music where artist='%s'" % artist,tracks)
		self.render_band(artist,tracks)
		

class TrackPage(Handler):
	def render_track(self,name="",videos=""):
		self.render("track.html",name=name,videos=videos)
	def get(self,resource,append):
		artist=str(urllib2.unquote(resource))[1:]
		song=str(urllib2.unquote(append))[1:]
		tracks=memcache.get("select * from Music where artist='%s'" % artist)
		if tracks is None:
                        tracks=list(db.GqlQuery("select * from Music where artist='%s'" % artist))
                        for i in tracks:
                                i.artist=i.artist.replace("+","-")
                                i.song=i.song.replace("+","-")
                        memcache.set("select * from Music where artist='%s'" % artist,tracks)
		for track in tracks:
			if track.artist==artist and track.song==song:
				videos=track.video
				break
		self.render("track.html",name=artist+"/"+song,videos=videos)

	def post(self,resource,append):
                artist=str(urllib2.unquote(resource))[1:]
                song=str(urllib2.unquote(append))[1:]
		tracks=memcache.get("select * from Music where artist='%s'" % artist)
		for track in tracks:
                        if track.artist==artist and track.song==song:
                                db.delete(track.key())
				break
		video=self.request.get("video")
		m=Music(artist=artist,song=song,video=video)
		m.put()
		
		tracks=list(db.GqlQuery("select * from Music where artist='%s'" % artist))
		for i in tracks:
	 		i.artist=i.artist.replace("+","-")
        	        i.song=i.song.replace("+","-")
                memcache.set("select * from Music where artist='%s'" % artist,tracks)


		logging.error(artist)
		self.redirect('/')


app = webapp2.WSGIApplication([('/', MainPage),(PAGE_RE+PAGE_RE, TrackPage),(PAGE_RE, BandPage)], debug=True)
