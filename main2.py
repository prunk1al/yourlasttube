import urllib2
from xml.dom import minidom
import os
import webapp2
import jinja2
import logging
import random
import string
import time
import cgi
import json
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
	genre=db.StringProperty(required=True)
	album=db.StringProperty(required=True)
	created=db.DateTimeProperty(auto_now_add=True)

class Artist(db.Model):
	artist=db.StringProperty(required=True)



API_KEY= '51293239750eea5095511e23b3107e31'
def get_video(search):
	
	artist,song=search[0],search[1]
	data=memcache.get(search)
	if data is not None:
		return data
	else:

		query='http://gdata.youtube.com/feeds/api/videos?q="'+artist+'+'+song+'+official+video"+-mashup+-lyrics+-collaboration+-pirates+-cover+-making+-fanmade&max-results=1&v=2&format=5'
		page=urllib2.urlopen(query)
		xml=minidom.parseString(page.read())
		if  xml.getElementsByTagName("yt:videoid")!= []:
			data=xml.getElementsByTagName("yt:videoid")[0].childNodes[0].nodeValue
		else:
			data=" "
		memcache.set(search,data)
		return data

def update_cache(key="all",artist=""):
	if key=="all" or key=="videos": 
		videos=list(db.GqlQuery("select * from Music where video != ' '"))
		for i in videos:
			i.artist=i.artist.replace("+","-")
			i.song=i.song.replace("+","-")
		memcache.set("select * from Music where video != ' '",videos)
	
	if key=="all" or key=="all_artist":
		artist=list(db.GqlQuery("select * from Music"))
		for i in artist:
			i.artist=i.artist.replace("+","-")
			i.song=i.song.replace("+","-")
		memcache.set("select * from Music",artist)

	if key=="all" or key=="artist":
		tracks=list(db.GqlQuery("select * from Music where artist='%s'" % artist))
		for i in tracks:
			i.artist=i.artist.replace("+","-")
			i.song=i.song.replace("+","-")
		memcache.set("select * from Music where artist='%s'" % artist,tracks)


def artist_cache(artist):

	tracks=memcache.get("select * from Music where artist='%s'" % artist)
	
	if tracks is None:
		tracks=list(db.GqlQuery(u"select * from Music where artist='%s'" % artist))
		if tracks == []:
			return []

		for i in tracks:
			i.artist=i.artist.replace("+","-")
			i.song=i.song.replace("+","-")
		memcache.set("select * from Music where artist='%s'" % artist,tracks)
	return tracks

def get_artists():
	artists=memcache.get("artists")
	if artists==None:
		artists={}

	return artists

def replace_space(text):
	s=""
	for c in text:
		if c==" ":
			s=s+"+"
		else:
			s=s+c
	return s


def crawl(band=""):

	
	tocrawl=[]
	tocrawl.append(band)
	crawled=[]

	
	i=0
	for artist in tocrawl:
		logging.error(artist)
		artist=artist.replace("'","")
		if artist_cache(cgi.escape(artist)) != []:
			crawled.append(artist)
		if artist not in crawled:


				
			
			artists={}
			artists["artist"]=artist
			artists["albums"]={}
			artists["genre"]=""

			artist_list=memcache.get("artist_list")
			if artist_list is None:
				artist_list=[]
			artist_list.append(artist)
			memcache.set("artist_list",artist_list)

			logging.error("%s crawling artist %s"%(i,artist))


			query="http://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&artist="+artist+"&api_key="+API_KEY
			page=urllib2.urlopen(query)
			xml=minidom.parseString(page.read())
			g=xml.getElementsByTagName("name")
			genre=g[0].childNodes[0].nodeValue
			artists["genre"]=genre

			logging.error("getting albums")
			query="http://ws.audioscrobbler.com/2.0/?method=artist.gettopalbums&artist="+artist+"&api_key="+API_KEY
			page=urllib2.urlopen(query)
			xml=minidom.parseString(page.read())
			albums=xml.getElementsByTagName("album")
			
			if len(albums)>=5:
				i=2

			for album in albums:
				name=album.childNodes[1].childNodes[0].nodeValue
				artists["albums"][name]=[]

		


			for album in artists["albums"].iterkeys():
				

				artist=cgi.escape(artist,quote=True)
				
				query="http://ws.audioscrobbler.com/2.0/?method=album.getinfo&artist="+artist+"&album="+replace_space(cgi.escape(album,quote=True))+"&api_key="+API_KEY+"&limit=5"
				
				logging.error(query)
				try:
					page=urllib2.urlopen(query)
				except:
					break
				xml=minidom.parseString(page.read())
				tracks=xml.getElementsByTagName("track")

				for track in tracks:
					song=cgi.escape(track.childNodes[1].childNodes[0].nodeValue)
					logging.error(song)
					try:
						video=str(get_video((artist,replace_space(cgi.escape(song,quote=True)))))
						artists["albums"][album].append((song,video))
						m=Music(artist=artist, song=song, video=video,genre=genre, album=album)
						m.put()
						memcache.set(artist,artists)
					except:
						pass


			
		query="http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist="+artist+"&api_key="+API_KEY

		crawled.append(tocrawl.pop())
		
		page=urllib2.urlopen(query)
		xml=minidom.parseString(page.read())
		names=xml.getElementsByTagName("url")
		for x in names:
			name=x.childNodes[0].nodeValue[18:]

			if name not in tocrawl and name not in crawled:
				tocrawl.append(name)



		if i>=2:
			break
		i=i+1




def search_artist(artist):
	if list(db.GqlQuery("select * from Artist"))==[]:
		logging.error("not in Artist")
		crawl_artist(artist)

def crawl_artist(artist):
	tocrawl=memcache.get("tocrawl_artist")
	crawled=memcache.get("crawled_artist")
	logging.error("crawling artist")

	if tocrawl is None:
		tocrawl=[]
		tocrawl.append(artist)
	if crawled is None:
		crawled=[]

	if tocrawl is not None:
		if artist in tocrawl:
			x=tocrawl.index(artist)
			next_crawl=tocrawl.pop(x)

		if artist in crawled:
			next_crawl=tocrawl.pop()
		
		else:
			next_crawl=artist

		query="http://api.deezer.com/2.0/search/artist?q="+next_crawl+"&output=xml&nb_items=1"
		logging.error(query)
		page=urllib2.urlopen(query)
		xml=minidom.parseString(page.read())
		names=xml.getElementsByTagName("url")

		crawled.append(next_crawl)
		for x in names:
			name=x.childNodes[0].nodeValue[18:]

			if name not in tocrawl and name not in crawled:
				tocrawl.append(name)
		
		a=Artist(artist=next_crawl)
		a.put()

		b=memcache.set("tocrawl_artist",tocrawl)
		c=memcache.set("crawled_artist",crawled)
	





class MainPage(Handler):
	def render_front(self,tracks=""):
		self.render("front.html",tracks=tracks)

	def get(self):
		tracks=memcache.get("select * from Music where video != ' '")
		if tracks is None:
			tracks=list(db.GqlQuery("select * from Music where video != ' '"))
			for i in tracks:
				i.artist=i.artist.replace("+","-")
				i.song=i.song.replace("+","-")
			memcache.set("select * from Music where video != ' '",tracks)
		random.shuffle(tracks)
		for i in tracks:
				logging.error("track=%s"% i.song)
		self.render_front(tracks[0:2])

	def post(self):
		artist=self.request.get('artist')
		artist=artist.replace(" ","-")
		
		search_artist(artist)

		self.redirect("/"+artist)



class BandPage(Handler):

	def render_band(self,artist="",albums=""):
		self.render("band.html",artist=artist,albums=albums)

	def get(self,resource):
		artist=str(urllib2.unquote(resource))[1:]
		artist=artist.replace("-","+")

		artists=memcache.get(artist)
		albums=[]
		albums2=[]
		for album in artists["albums"].iterkeys():
			albums.append(album)
			albums2.append(album.replace(" ","-"))

		artist=artist.replace("+","-")
		self.render_band(artist,albums)
		

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
				genre=track.genre
				logging.error(track.key)
				db.delete(track.key())
				break
		video=self.request.get("video")
		m=Music(artist=artist,song=song,video=video,genre=genre)
		m.put()
		
		update_cache("artist",artist)

		logging.error(artist)
		self.redirect('/')

class AlbumPage(Handler):
	def render_album(self,artist="",album="",tracks=""):
		self.render("album.html",artist=artist,album=album,tracks=tracks)

	def get(self,resource,append):
		artist=str(urllib2.unquote(resource))[1:]
		album=str(urllib2.unquote(append))[1:]


		artist=artist.replace("-","+")
		album=album.replace("-"," ")
		artists=memcache.get(artist)

		logging.error(cgi.escape(album))

		tracks=[]
		for track in artists["albums"][album]:
			tracks.append(track)

		self.render_album(artist=artist,album=album,tracks=tracks)
		






class Crawl(Handler):
	def get(self):
		crawl()



class RandomPage(Handler):
	def render_random(self,lista=""):
		first=lista.pop()
		playlist=""
		for i in lista:
			playlist=playlist+i+","
		logging.error(first)
		logging.error(playlist)
		url="http://www.youtube.com/embed/"+first+"?playlist="+playlist
		self.render("random.html", url=url)

		self.redirect(str(url))
	def get(self):
		videos=memcache.get("select * from Music where video != ' '")
		if videos is None:
			update_cache("videos")
			videos=memcache.get("select * from Music where video != ' '")

		tracks=[]
		for i in videos:
			tracks.append(i.video)
		random.shuffle(tracks)
		self.render_random(tracks[0:150])

class ArtistsPage(Handler):
	def render_artist(self,artist=""):
		self.render("artist.html",artist=artist)

	def get(self):

				
		artist=memcache.get("artist_list")
		self.render_artist(sorted(artist))

	def post(self):
		artist=self.request.get('artist')
		artist=artist.replace(" ","-")
		
		search(artist)
		self.redirect("/"+artist)


class GenresPage(Handler):
	def render_genre(self,artist=""):
		self.render("artist.html",artist=artist)

	def get(self):
		artist_list=memcache.get("artist_list")

		genre=[]
		for i in artist_list:
			artist=memcache.get(i)
			if artist["genre"] not in genre:
				genre.append(artist["genre"])
		self.render_genre(sorted(genre))


class Clean(Handler):
	def get(self):
		artist=list(db.GqlQuery("select * from Music"))
		for i in artist:
			logging.error("a")
			db.delete(i.key())

class GenrePage(Handler):
	def get(self):
		a=0

class Fill(Handler):
	def get(self):
		artist_list=[]
		artists={}
		
		if artists is {}:
			songs=list(db.GqlQuery("select * from Music"))

			for song in songs:

				artist=song.artist
				album=song.album

				logging.error("song %s"%artist)

				if artist not in artist_list:
					artist_list.append(artist)
					memcache.set("artist_list",artist_list)

				logging.error("song %s"%song.artist)
				if song.artist not in artists.keys():
					
					artists["artist"]=artist
					artists["albums"]={}
					artists["genre"]=""

				if song.album not in artists["album"].keys():
					artists["albums"][album]=[]
				if song.genre not in artist["genre"].keys():
					artist["genre"]=song.genre

				artists["albums"][album].append((song.song,song.video))
				logging.error(artists)
				memcache.set(artist,artists)



app = webapp2.WSGIApplication([('/', MainPage),('/fillmemcache',Fill),('/Clean', Clean),('/crawl', Crawl),('/genres',GenresPage),("/genres"+PAGE_RE,GenrePage),('/artists',ArtistsPage),('/random',RandomPage),(PAGE_RE+PAGE_RE+PAGE_RE, TrackPage),(PAGE_RE+PAGE_RE, AlbumPage),(PAGE_RE, BandPage)], debug=True)
