
import tools
import logging
from track import Track
from artist import Artist
from google.appengine.ext import ndb
from CorrectArtist import CorrectArtist
import json
import urllib2

class Dynamic:
	def __init__(self,data="", tipo="" ,tracks=[],session=""):
		self.data=data
		self.tipo=tipo
		self.tracks=tracks
		self.session=session
	def getData(self):
		return self.data

	def parseTracks(self, contents={}):
		
		for d in contents["response"]["songs"]:
			self.parseTrack(d)
	
	def parseTrack(self, d={}):
	
		try:
			mbid=d["artist_foreign_ids"][0]["foreign_id"].split(':')[2]
		except:
			try:
				mbid=d["artist_foreign_ids"]["foreign_id"].split(':')[2]
			except:
				
				return {}

		track={}
		track["artist"]={}
		tracKey=ndb.Key('Track',d["title"]+ " - " +d["artist_name"] )
		trac=tracKey.get()
		if trac is not None:

			track["ytid"]=trac.ytid
			track["img"]="http://img.youtube.com/vi/"+trac.ytid+"/0.jpg"


		logging.error(mbid)

		cmbid=CorrectArtist.by_id(mbid)
		if cmbid is not None:
			track["artist"]["mbid"]=cmbid.mbid
			mbid=cmbid.mbid
			artist=ndb.Key('Artist',cmbid.mbid).get()
		else:
			track["artist"]["mbid"]=mbid
			artist=ndb.Key('Artist',mbid).get()
		if artist is not None:
			track["artist"]=artist.toJson()

		else:
			track["artist"]["mbid"]=mbid
			track["artist"]["name"]=d["artist_name"]
			track["artist"]["similars"]=[]
			track["artist"]["logo"]=""
			track["artist"]["info"]=""
			track["artist"]["tags"]=[]
		track["name"]=d["title"]
		self.tracks.append(track)

	def create(self):
		self.tracks=[]
		url=tools.get_url("echonest","%sCreate"%self.tipo ,self.data)
		j=tools.getjson(url)
		logging.error(url)
		session=j["response"]["session_id"]
		self.session=session

		url=tools.get_url("echonest","getNext10" ,session)
		logging.error(url)
		j=tools.getjson(url)


		self.parseTracks(j)

		
	def getNext(self):
		self.tracks=[]
		playlist={"data":[]}
		url=tools.get_url("echonest","getNext",self.session)
		logging.error(url)
		j=tools.getjson(url)
		logging.error(url)
		logging.error(j)
		self.parseTracks(j)	
			

class GenrePL(Dynamic):
	def __init__(self, genre="", tipo="genre"):
		Dynamic.__init__(self,genre,tipo)


class ArtistPL(Dynamic):
	def __init__(self, artist="", tipo="artist"):
		Dynamic.__init__(self,artist, tipo)

class ArtistR(Dynamic):
	def __init__(self, artist="", tipo="artistRadio"):
		Dynamic.__init__(self,artist, tipo)

