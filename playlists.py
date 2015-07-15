import urllib2
import os
import webapp2
import jinja2
import logging
import json
from xml.dom import minidom

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api.labs import taskqueue
from google.appengine.api import files
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from CorrectArtist import CorrectArtist
from artist import Artist
from track import Track
from echonest import GenrePL
from echonest import ArtistPL
from echonest import ArtistR
from google.appengine.api import images
import artist
import album
import track
import image
import tools
import string


import time

class Playlist:
	tracks=[]
	tipo=""
	param=""
	page=0
	session=""





	def create(self):
		time_start=time.time()
	
		self.tracks=[]
		filter="toptracks"

		
		url=""
		logging.error(url)
		if self.tipo=="tag":
			if {"name": self.param} in  echonest_genres["response"]["genres"]: 
				echo=GenrePL(self.param)
				echo.create()
				self.tracks=echo.tracks
				self.session=echo.session
				#self.createEchoTag()

				actual=time.time() - time_start
				logging.error("After create echo playlist= %s"%actual)
				return

			url=tools.get_url("lastfm","genreCreate",self.param)
		elif self.tipo=="artist":
			echo=ArtistPL(self.param)
			echo.create()
			self.tracks=echo.tracks
			self.session=echo.session

			actual=time.time() - time_start
			logging.error("After create echo playlist= %s"%actual)
			return
			#url=tools.get_url("lastfm","artistCreate",self.param)
		elif self.tipo=="artist-radio":
			echo=ArtistR(self.param)
			echo.create()
			self.tracks=echo.tracks
			self.session=echo.session
			
			actual=time.time() - time_start
			logging.error("After create echo playlist= %s"%actual)
			return
			#url=tools.get_url("lastfm","artistCreate",self.param)
		else:
			url=tools.get_url("lastfm","toptracks"," ")
			filter="tracks"
		logging.error(url)
		page=urllib2.urlopen(url)
		p=page.read()
		j=json.loads(p)
		actual=time.time() - time_start
		logging.error("after json: %s"%actual)
		for d in j[filter]["track"]:

			track={}
			track["artist"]={}
			tracKey=ndb.Key('Track',d["name"]+ " - " +d["artist"]["name"] )
			trac=tracKey.get()
			if trac is not None:
				
				track["ytid"]=trac.ytid
				track["img"]="http://img.youtube.com/vi/"+trac.ytid+"/0.jpg"

			
			mbid=d["artist"]["mbid"]
			
			if mbid=="": continue
			logging.error(mbid)
			cmbid=CorrectArtist.by_id(mbid)
			if cmbid is not None:
				track["artist"]["mbid"]=cmbid.mbid
				artist=ndb.Key('Artist',cmbid.mbid).get()
			else:
				track["artist"]["mbid"]=mbid
				artist=ndb.Key('Artist',mbid).get()

			if artist is not None:
				actual=time.time() - time_start
				logging.error("before similars: %s"%actual)


				if artist.name is not None:
					track["artist"]["name"]=artist.name
				else:
					track["artist"]["name"]=d["artist"]["name"]
				if artist.logo is not None:
					track["artist"]["logo"]=images.get_serving_url(artist.logo)
				if artist.info is not None:
					track["artist"]["info"]=artist.info
				if artist.tags is not None:
					track["artist"]["tags"]=artist.tags
				if artist.similars is not None:
					similars=[]
					s=ndb.get_multi(artist.similars)
					for similar in s:
						similars.append({"name":similar.name, "logo":similar.image,"mbid":similar.key.id()})

					track["artist"]["similars"]=similars
				
				actual=time.time() - time_start
				logging.error("after getting similars: %s"%actual)
			else:
				track["artist"]["name"]=d["artist"]["name"] 
				track["artist"]["similars"]=[]
				track["artist"]["logo"]=""
				track["artist"]["info"]=""
				track["artist"]["tags"]=[]
			track["name"]=d["name"]

			self.tracks.append(track)


	def getTracks(self):
		return self.tracks

	def getNextTrack(self):

		if self.tipo=="tag":
			data=playlists.getEchoTagTracks(self.param)
		elif self.tipo=="artist":
			url=tools.get_url("lastfm","artistNext",self.param)
			logging.error(url)
			
			page=urllib2.urlopen(url)
			p=page.read()
			j=json.loads(p)
			filter="toptracks"
			if "a"=="a":
				d=j[filter]["track"]
				track={}
				track["artist"]={}
				tracKey=ndb.Key('Track',d["name"]+ " - " +d["artist"]["name"] )
				trac=tracKey.get()
				if trac is not None:
					
					track["ytid"]=trac.ytid
					track["img"]="http://img.youtube.com/vi/"+trac.ytid+"/0.jpg"

				
				mbid=d["artist"]["mbid"]
				cmbid=CorrectArtist.by_id(mbid)
				if cmbid is not None:
					track["artist"]["mbid"]=cmbid.mbid
					artist=ndb.Key('Artist',cmbid.mbid).get()
				else:
					track["artist"]["mbid"]=mbid
					artist=ndb.Key('Artist',mbid).get()

				if artist is not None:

					if artist.name is not None:
						track["artist"]["name"]=artist.name
					else:
						track["artist"]["name"]=d["artist"]["name"]
					if artist.logo is not None:
						track["artist"]["logo"]=images.get_serving_url(artist.logo)
					if artist.info is not None:
						track["artist"]["info"]=artist.info
					if artist.tags is not None:
						track["artist"]["tags"]=artist.tags
					if artist.similars is not None:
						similars=[]
						for s in artist.similars:
							similar=s.get()
							similars.append({"name":similar.name, "logo":similar.image,"mbid":similar.key.id()})
						track["artist"]["similars"]=similars
				
				else:
					track["artist"]["name"]=d["artist"]["name"] 
					track["artist"]["similars"]=[]
					track["artist"]["logo"]=""
					track["artist"]["info"]=""
					track["artist"]["tags"]=[]
				track["name"]=d["name"]
				self.tracks.append(track)
			
		else:
			data=playlists.getTopTracks()

			logging.error(data)

	def createEchoTag(self):

		url=tools.get_url("echonest","genre",self.param).replace(" ", "%20")

		j=tools.get_json(url)
		for d in j["response"]["songs"]:
			try:
				mbid=d["artist_foreign_ids"][0]["foreign_id"].split(':')[2]
			except:
				continue
				
			track={}
			track["artist"]={}
			tracKey=ndb.Key('Track',d["title"]+ " - " +d["artist_name"] )
			trac=tracKey.get()
			if trac is not None:
				
				track["ytid"]=trac.ytid
				track["img"]="http://img.youtube.com/vi/"+trac.ytid+"/0.jpg"

			
			
			cmbid=CorrectArtist.by_id(mbid)
			if cmbid is not None:
				track["artist"]["mbid"]=cmbid.mbid
				artist=ndb.Key('Artist',cmbid.mbid).get()
			else:
				track["artist"]["mbid"]=mbid
				artist=ndb.Key('Artist',mbid).get()

			if artist is not None:

				if artist.name is not None:
					track["artist"]["name"]=artist.name
				else:
					track["artist"]["name"]=d["artist_name"]
				if artist.logo is not None:
					track["artist"]["logo"]=images.get_serving_url(artist.logo)
				if artist.info is not None:
					track["artist"]["info"]=artist.info
				if artist.tags is not None:
					track["artist"]["tags"]=artist.tags
				if artist.similars is not None:
					similars=[]
					for s in artist.similars:
						similar=s.get()
						similars.append({"name":similar.name, "logo":similar.image,"mbid":similar.key.id()})
					track["artist"]["similars"]=similars
			
			else:
				track["artist"]["name"]=d["artist_name"]
				track["artist"]["similars"]=[]
				track["artist"]["logo"]=""
				track["artist"]["info"]=""
				track["artist"]["tags"]=[]
			track["name"]=d["title"]
			self.tracks.append(track)

































def get_echonest_playlist(tipo,mbid):
	if tipo=="artist":
		url=tools.get_url("echonest","artist",mbid)
		j=tools.get_json(url)
		return j["response"]["songs"]


def getTopTracks():
	url=tools.get_url("lastfm","toptracks"," ")
	logging.error(url)
	toptracks=tools.get_json(url)

	return toptracks

def getTagTracks(genre):
	url=tools.get_url("lastfm","toptagtracks",genre)
	logging.error(url)
	tracks=tools.get_json(url)

	return tracks

def getArtistTracks(genre):
	url=tools.get_url("lastfm","artisttoptracks",genre)
	logging.error(url)
	tracks=tools.get_json(url)

	return tracks

def getEchoTagTracks(genre):
	playlist={"data":[]}
	url=tools.get_url("echonest","genre",genre).replace(" ","%20")
	logging.error(url)
	j=tools.get_json(url)
	return j['response']['songs']
		


def get_playlist_from_url(playlist_name):

	playlist={"data":[]}

	if 'frontpage' in playlist_name:
		logging.error("front")
		url=tools.get_url("lastfm","toptracks"," ")
		logging.error(url)
		j=tools.get_json(url)

		for i in j['tracks']['track']:
			if(len(playlist["data"])<11):
				mbid=i["mbid"]
				track_name=i['name']
				artist_name=i["artist"]["name"]
				ancestor_key=Class.Artists().query(Class.Artists.artist_name==artist_name).get(keys_only=True)
				if ancestor_key is not None:
					tracks=Class.Tracks().query(Class.Tracks.track_name==track_name,ancestor=ancestor_key).get()
				else:
					tracks=None
				if tracks is None:
					track_video=track.get_video(artist_name,track_name)
				else:
					track_video=tracks.track_video	
		        
				video={"video_artist":artist_name,"video_track":track_name,"playlist_videos":track_video, "mbid":mbid}
			
				playlist["data"].append(video)

				p=Class.Playlists(playlist_name=playlist_name,playlist_json=j,playlist_videos=playlist,key=ndb.Key(Class.Playlists,playlist_name))
				#p.put()
		memcache.set(playlist_name,playlist)
		return playlist

	logging.error("radio")
	if 'radio' in playlist_name:
		if 'artist' in playlist_name:
			params=playlist_name.split()
			mbid=params[1]	
			url=tools.get_url("echonest","playlist",mbid)
		else:
			genre=playlist_name[0:playlist_name.find('radio')]
			url=tools.get_url("echonest","genre",genre).replace(" ","%20")
		
		logging.error(url)
			
		j=tools.get_json(url)
			
		for i in j['response']['songs']:
			track_name=i['title']
			artist_name=i['artist_name']
			ancestor_key=Class.Artists().query(Class.Artists.artist_name==artist_name).get(keys_only=True)
			if ancestor_key is not None:
				tracks=Class.Tracks().query(Class.Tracks.track_name==track_name,ancestor=ancestor_key).get()
			else:
				tracks=None
			if tracks is None:
				track_video=track.get_video(artist_name,track_name)
			else:
				track_video=tracks.track_video	
			        
			video={"video_artist":artist_name,"video_track":track_name,"playlist_videos":track_video}
				
			playlist["data"].append(video)
			
		p=Class.Playlists(playlist_name=playlist_name,playlist_json=j,playlist_videos=playlist,key=ndb.Key(Class.Playlists,playlist_name))
		p.put()
		memcache.set(playlist_name,playlist)
		logging.error(playlist)
		return playlist

def check_playlist(playlist_name):

	logging.error("check_playlist")
	
	playlist=get_playlist_from_Home(playlist_name)
	check=get_playlist_from_url(playlist_name)

	if playlist == check:
		return playlist
	else:
		return check



def get_front_playlist():
	song=[]
	playlist_name="frontpage playlist"

	#playlist =get_playlist_from_Home(playlist_name)
	playlist=memcache.get(playlist_name)
	if playlist is not None:
		return playlist


	playlist=get_playlist_from_url(playlist_name)
	logging.error(playlist)
	
	return playlist




		
def get_genre_playlist(genre):
	song=[]
	playlist=ndb.Key(Class.Playlists,genre).get()
	if playlist is not None:
		for t_data in playlist.playlist_tracks:

			artist=get_artist_from_track(t_data.track_mbid)

			song.append((artist,t_data))

		return song
	else:
		return None

def get_lastfmGenre_playlist(genre):
	url=tools.get_url("lastfm","toptagtracks",genre)
	j=tools.get_json(url)
	return j



def get_lastfmTag_playlist(genre):

	artists_mbid=[]
	song=[]
	tracks=[]

	lastfm_playlist=get_lastfmGenre_playlist(genre)
	
	song=get_genre_playlist(genre)
	if song is not None:

		test=check_playlist(lastfm_playlist,song)
		return song

	
	for i in lastfm_playlist["toptracks"]['track']:
		
		track_mbid=i['mbid']
		
		if track_mbid!="":

			track_name=i['name']
			artist_name=i['artist']['name']
			artist_mbid=i['artist']['mbid']
			
			artist_data=Class.Artists(artist_name=artist_name, artist_mbid=artist_mbid)
			
			t_data=Class.Tracks().query(Class.Tracks.track_mbid==track_mbid).get()
			if t_data is None:

				artist_key=Class.Artists().query(Class.Artists.artist_mbid==artist_mbid).get(keys_only=True)
				if artist_key is not None:

					t_data=Class.Tracks().query(Class.Tracks.track_name==track_name, ancestor=artist_key).get()
					if t_data is None:

						t_data=Class.Tracks(track_name=track_name, track_video=track.get_video(artist_name,track_name),track_mbid=track_mbid)

				if artist_mbid!="":

					if artist_mbid not in artists_mbid:
						artists_mbid.append(artist_mbid)
						taskqueue.add(url='/worker',params={'f': '[track.get_tracks(w.album_mbid) for w in  artist.get_artist_albums("%s")[1]]'%artist_mbid})
					pass
	
			song.append((artist_data,t_data))
			tracks.append(t_data)
	playlist=Class.Playlists(playlist_name=genre,playlist_tracks=tracks,key=ndb.Key(Class.Playlists,genre))
	#playlist.put()		

	return song



echonest_genres={"response": {"status": {"version": "4.2", "code": 0, "message": "Success"}, "start": 0, "genres": [{"name": "a cappella"}, {"name": "abstract hip hop"}, {"name": "acid house"}, {"name": "acid jazz"}, {"name": "acid techno"},
 {"name": "acousmatic"}, {"name": "acoustic blues"}, {"name": "acoustic pop"}, {"name": "adult album alternative"}, {"name": "adult standards"}, {"name": "african percussion"}, {"name": "african rock"}, {"name": "afrikaans"}, 
 {"name": "afrobeat"}, {"name": "afrobeats"}, {"name": "aggrotech"}, {"name": "albanian pop"}, {"name": "album rock"}, {"name": "alternative country"}, {"name": "alternative dance"}, {"name": "alternative emo"}, 
 {"name": "alternative hip hop"}, {"name": "alternative metal"}, {"name": "alternative pop"}, {"name": "alternative rock"}, {"name": "ambient"}, {"name": "ambient idm"}, {"name": "andean"}, {"name": "anime"}, 
 {"name": "anti-folk"}, {"name": "arab folk"}, {"name": "arab pop"}, {"name": "argentine rock"}, {"name": "art rock"}, {"name": "atmospheric black metal"}, {"name": "atmospheric post rock"}, {"name": "austindie"}, 
 {"name": "australian alternative rock"}, {"name": "australian hip hop"}, {"name": "australian pop"}, {"name": "austropop"}, {"name": "avant-garde"}, {"name": "avant-garde jazz"}, {"name": "avantgarde metal"}, 
 {"name": "axe"}, {"name": "azonto"}, {"name": "bachata"}, {"name": "baile funk"}, {"name": "balearic"}, {"name": "balkan brass"}, {"name": "banda"}, {"name": "bangla"}, {"name": "barbershop"}, {"name": "baroque"}, {"name": "basque rock"},
 {"name": "bass music"}, {"name": "beach music"}, {"name": "beatdown"}, {"name": "bebop"}, {"name": "belgian rock"}, {"name": "belly dance"}, {"name": "benga"}, {"name": "bhangra"}, {"name": "big band"}, {"name": "big beat"}, 
 {"name": "black death"}, {"name": "black metal"}, {"name": "bluegrass"}, {"name": "blues"}, {"name": "blues-rock"}, {"name": "bolero"}, {"name": "boogaloo"}, {"name": "boogie-woogie"}, {"name": "bossa nova"}, {"name": "bounce"},
 {"name": "bouncy house"}, {"name": "brass band"}, {"name": "brazilian gospel"}, {"name": "brazilian hip hop"}, {"name": "brazilian indie"}, {"name": "brazilian pop music"}, {"name": "brazilian punk"}, {"name": "breakbeat"}, 
 {"name": "breakcore"}, {"name": "breaks"}, {"name": "brega"}, {"name": "brill building pop"}, {"name": "british blues"}, {"name": "british folk"}, {"name": "british invasion"}, {"name": "britpop"}, {"name": "broken beat"}, 
 {"name": "brostep"}, {"name": "brutal death metal"}, {"name": "brutal deathcore"}, {"name": "bubblegum dance"}, {"name": "bubblegum pop"}, {"name": "bulgarian rock"}, {"name": "c-pop"}, {"name": "c86"}, {"name": "cabaret"}, 
 {"name": "calypso"}, {"name": "canadian indie"}, {"name": "canadian pop"}, {"name": "cantautor"}, {"name": "canterbury scene"}, {"name": "cantopop"}, {"name": "capoeira"}, {"name": "ccm"}, {"name": "cello"}, {"name": "celtic"}, 
 {"name": "celtic christmas"}, {"name": "celtic rock"}, {"name": "chalga"}, {"name": "chamber pop"}, {"name": "chanson"}, {"name": "chaotic hardcore"}, {"name": "charred death"}, {"name": "chicago blues"}, {"name": "chicago house"},
 {"name": "chicago soul"}, {"name": "chicano rap"}, {"name": "children's music"}, {"name": "chilean rock"}, {"name": "chill lounge"}, {"name": "chill-out"}, {"name": "chillwave"}, {"name": "chinese indie rock"}, 
 {"name": "chinese traditional"}, {"name": "chiptune"}, {"name": "choral"}, {"name": "choro"}, {"name": "chr"}, {"name": "christian alternative rock"}, {"name": "christian christmas"}, {"name": "christian dance"}, 
 {"name": "christian hardcore"}, {"name": "christian hip hop"}, {"name": "christian metal"}, {"name": "christian music"}, {"name": "christian punk"}, {"name": "christian rock"}, {"name": "christmas"}, {"name": "christmas product"},
 {"name": "classic chinese pop"}, {"name": "classic funk rock"}, {"name": "classic garage rock"}, {"name": "classic rock"}, {"name": "classic russian rock"}, {"name": "classical"}, {"name": "classical christmas"},
 {"name": "classical guitar"}, {"name": "classical period"}, {"name": "classical piano"}, {"name": "comedy"}, {"name": "comic"}, {"name": "contemporary classical"}, {"name": "contemporary country"}, {"name": "contemporary jazz"},
 {"name": "contemporary post-bop"}, {"name": "cool jazz"}, {"name": "country"}, {"name": "country blues"}, {"name": "country christmas"}, {"name": "country gospel"}, {"name": "country rock"}, {"name": "coupe decale"}, 
 {"name": "coverchill"}, {"name": "cowpunk"}, {"name": "croatian pop"}, {"name": "crossover thrash"}, {"name": "crunk"}, {"name": "crust punk"}, {"name": "cuban rumba"}, {"name": "cumbia"}, {"name": "cumbia villera"}, 
 {"name": "current"}, {"name": "czech folk"}, {"name": "dance pop"}, {"name": "dance rock"}, {"name": "dance-punk"}, {"name": "dancehall"}, {"name": "dangdut"}, {"name": "danish pop"}, {"name": "dark ambient"}, 
 {"name": "dark black metal"}, {"name": "dark cabaret"}, {"name": "dark wave"}, {"name": "darkstep"}, {"name": "death core"}, {"name": "death metal"}, {"name": "deathgrind"}, {"name": "deep disco house"}, {"name": "deep funk"}, 
 {"name": "deep house"}, {"name": "deep soul house"}, {"name": "deep trap"}, {"name": "deeper house"}, {"name": "delta blues"}, {"name": "demoscene"}, {"name": "desert blues"}, {"name": "desi"}, {"name": "detroit techno"}, 
 {"name": "digital hardcore"}, {"name": "dirty south rap"}, {"name": "disco"}, {"name": "disco house"}, {"name": "discovery"}, {"name": "djent"}, {"name": "doo-wop"}, {"name": "doom metal"}, {"name": "doomcore"}, {"name": "downtempo"}, 
 {"name": "downtempo fusion"}, {"name": "dream pop"}, {"name": "dreamo"}, {"name": "drill and bass"}, {"name": "drone"}, {"name": "drum and bass"}, {"name": "drumfunk"}, {"name": "dub"}, {"name": "dub techno"}, {"name": "dubstep"}, 
 {"name": "duranguense"}, {"name": "dutch hip hop"}, {"name": "dutch house"}, {"name": "dutch pop"}, {"name": "dutch rock"}, {"name": "early music"}, {"name": "east coast hip hop"}, {"name": "easy listening"}, {"name": "ebm"}, 
 {"name": "ecuadoria"}, {"name": "electric blues"}, {"name": "electro"}, {"name": "electro house"}, {"name": "electro swing"}, {"name": "electro trash"}, {"name": "electro-industrial"}, {"name": "electroacoustic improvisation"}, 
 {"name": "electroclash"}, {"name": "electronic"}, {"name": "emo"}, {"name": "enka"}, {"name": "entehno"}, {"name": "environmental"}, {"name": "estonian pop"}, {"name": "ethereal wave"}, {"name": "ethiopian pop"}, {"name": "eurobeat"}, 
 {"name": "eurodance"}, {"name": "europop"}, {"name": "eurovision"}, {"name": "exotica"}, {"name": "experimental"}, {"name": "experimental psych"}, {"name": "experimental rock"}, {"name": "fado"}, {"name": "fallen angel"}, 
 {"name": "faroese pop"}, {"name": "filmi"}, {"name": "filter house"}, {"name": "filthstep"}, {"name": "fingerstyle"}, {"name": "finnish hardcore"}, {"name": "finnish hip hop"}, {"name": "finnish pop"}, {"name": "flamenco"}, 
 {"name": "folk"}, {"name": "folk christmas"}, {"name": "folk metal"}, {"name": "folk punk"}, {"name": "folk rock"}, {"name": "folk-pop"}, {"name": "footwork"}, {"name": "forro"}, {"name": "fourth world"}, {"name": "freak folk"}, 
 {"name": "freakbeat"}, {"name": "free improvisation"}, {"name": "free jazz"}, {"name": "freestyle"}, {"name": "french hip hop"}, {"name": "french indie pop"}, {"name": "french pop"}, {"name": "french rock"}, {"name": "funeral doom"}, 
 {"name": "funk"}, {"name": "funk metal"}, {"name": "funk rock"}, {"name": "future garage"}, {"name": "futurepop"}, {"name": "g funk"}, {"name": "gabba"}, {"name": "gamelan"}, {"name": "gangster rap"}, {"name": "garage pop"}, 
 {"name": "garage rock"}, {"name": "german hip hop"}, {"name": "german indie"}, {"name": "german oi"}, {"name": "german pop"}, {"name": "german punk"}, {"name": "ghettotech"}, {"name": "glam metal"}, {"name": "glam rock"}, {"name": "glitch"}, 
 {"name": "glitch hop"}, {"name": "goregrind"}, {"name": "gospel"}, {"name": "gothic alternative"}, {"name": "gothic americana"}, {"name": "gothic doom"}, {"name": "gothic metal"}, {"name": "gothic rock"}, {"name": "gothic symphonic metal"}, 
 {"name": "grave wave"}, {"name": "grime"}, {"name": "grindcore"}, {"name": "groove metal"}, {"name": "grunge"}, {"name": "grupera"}, {"name": "guidance"}, {"name": "gujarati"}, {"name": "gypsy jazz"}, {"name": "hands up"}, 
 {"name": "happy hardcore"}, {"name": "hard alternative"}, {"name": "hard bop"}, {"name": "hard glam"}, {"name": "hard house"}, {"name": "hard rock"}, {"name": "hard trance"}, {"name": "hardcore"}, {"name": "hardcore breaks"}, 
 {"name": "hardcore hip hop"}, {"name": "hardcore punk"}, {"name": "hardcore techno"}, {"name": "hardstyle"}, {"name": "harmonica blues"}, {"name": "harp"}, {"name": "hawaiian"}, {"name": "heavy christmas"}, {"name": "hi nrg"}, 
 {"name": "highlife"}, {"name": "hindustani classical"}, {"name": "hip hop"}, {"name": "hip house"}, {"name": "hiplife"}, {"name": "horror punk"}, {"name": "hot"}, {"name": "hot adult contemporary"}, {"name": "house"}, 
 {"name": "hungarian pop"}, {"name": "hurban"}, {"name": "hyphy"}, {"name": "icelandic pop"}, {"name": "illbient"}, {"name": "indian classical"}, {"name": "indian pop"}, {"name": "indian rock"}, {"name": "indie christmas"}, 
 {"name": "indie folk"}, {"name": "indie pop"}, {"name": "indie rock"}, {"name": "indie shoegaze"}, {"name": "indietronica"}, {"name": "indonesian pop"}, {"name": "industrial"}, {"name": "industrial metal"}, 
 {"name": "industrial rock"}, {"name": "intelligent dance music"}, {"name": "irish folk"}, {"name": "irish rock"}, {"name": "israeli rock"}, {"name": "italian disco"}, {"name": "italian hip hop"}, {"name": "italian indie pop"}, 
 {"name": "italian pop"}, {"name": "j-alt"}, {"name": "j-ambient"}, {"name": "j-core"}, {"name": "j-dance"}, {"name": "j-idol"}, {"name": "j-indie"}, {"name": "j-metal"}, {"name": "j-pop"}, {"name": "j-punk"}, {"name": "j-rap"}, 
 {"name": "j-rock"}, {"name": "j-theme"}, {"name": "jam band"}, {"name": "jangle pop"}, {"name": "japanese psychedelic"}, {"name": "japanese r&b"}, {"name": "japanese standards"}, {"name": "japanese traditional"}, {"name": "japanoise"}, 
 {"name": "jazz"}, {"name": "jazz blues"}, {"name": "jazz christmas"}, {"name": "jazz funk"}, {"name": "jazz fusion"}, {"name": "jazz metal"}, {"name": "jazz orchestra"}, {"name": "jerk"}, {"name": "judaica"}, {"name": "jug band"}, 
 {"name": "juggalo"}, {"name": "jump blues"}, {"name": "jump up"}, {"name": "jungle"}, {"name": "k-hop"}, {"name": "k-indie"}, {"name": "k-pop"}, {"name": "k-rock"}, {"name": "kannada"}, {"name": "kirtan"}, {"name": "kiwi rock"}, 
 {"name": "kizomba"}, {"name": "klezmer"}, {"name": "kompa"}, {"name": "kraut rock"}, {"name": "kuduro"}, {"name": "kwaito"}, {"name": "la indie"}, {"name": "laiko"}, {"name": "latin"}, {"name": "latin alternative"}, 
 {"name": "latin christian"}, {"name": "latin christmas"}, {"name": "latin hip hop"}, {"name": "latin jazz"}, {"name": "latin metal"}, {"name": "latin pop"}, {"name": "latvian pop"}, {"name": "lds"}, {"name": "liedermacher"}, 
 {"name": "lilith"}, {"name": "liquid funk"}, {"name": "lithumania"}, {"name": "lo star"}, {"name": "lo-fi"}, {"name": "louisiana blues"}, {"name": "lounge"}, {"name": "lovers rock"}, {"name": "luk thung"}, {"name": "madchester"}, 
 {"name": "maghreb"}, {"name": "makossa"}, {"name": "malagasy folk"}, {"name": "malayalam"}, {"name": "malaysian pop"}, {"name": "mambo"}, {"name": "mande pop"}, {"name": "mandopop"}, {"name": "manele"}, {"name": "marching band"}, 
 {"name": "mariachi"}, {"name": "martial industrial"}, {"name": "mashup"}, {"name": "math pop"}, {"name": "math rock"}, {"name": "mathcore"}, {"name": "mbalax"}, {"name": "medieval"}, {"name": "medieval rock"}, {"name": "meditation"}, 
 {"name": "mellow gold"}, {"name": "melodic death metal"}, {"name": "melodic hard rock"}, {"name": "melodic hardcore"}, {"name": "melodic metalcore"}, {"name": "melodic progressive metal"}, {"name": "memphis blues"}, {"name": "memphis soul"}, 
 {"name": "merengue"}, {"name": "merengue urbano"}, {"name": "merseybeat"}, {"name": "metal"}, {"name": "metalcore"}, {"name": "mexican indie"}, {"name": "mexican son"}, {"name": "microhouse"}, {"name": "minimal"}, {"name": "minimal dub"}, 
 {"name": "minimal techno"}, {"name": "minimal wave"}, {"name": "modern blues"}, {"name": "modern classical"}, {"name": "modern country rock"}, {"name": "monastic"}, {"name": "moombahton"}, {"name": "more classical piano"}, 
 {"name": "more indie pop"}, {"name": "more melodic death metal"}, {"name": "more tech house"}, {"name": "more thrash metal"}, {"name": "motown"}, {"name": "mpb"}, {"name": "musique concrete"}, {"name": "nashville sound"}, 
 {"name": "native american"}, {"name": "neo classical metal"}, {"name": "neo soul"}, {"name": "neo-industrial rock"}, {"name": "neo-pagan"}, {"name": "neo-progressive"}, {"name": "neo-psychedelic"}, {"name": "neo-singer-songwriter"}, 
 {"name": "neo-synthpop"}, {"name": "neo-trad metal"}, {"name": "neoclassical"}, {"name": "neofolk"}, {"name": "nepali"}, {"name": "neue deutsche harte"}, {"name": "neue deutsche welle"}, {"name": "neurofunk"}, {"name": "neurostep"}, 
 {"name": "new age"}, {"name": "new beat"}, {"name": "new jack swing"}, {"name": "new orleans blues"}, {"name": "new orleans jazz"}, {"name": "new rave"}, {"name": "new romantic"}, {"name": "new tribe"}, {"name": "new wave"}, 
 {"name": "new weird america"}, {"name": "ninja"}, {"name": "nintendocore"}, {"name": "nl folk"}, {"name": "no wave"}, {"name": "noise pop"}, {"name": "noise rock"}, {"name": "nordic folk"}, {"name": "norteno"}, {"name": "northern soul"}, 
 {"name": "norwegian jazz"}, {"name": "norwegian pop"}, {"name": "nu age"}, {"name": "nu disco"}, {"name": "nu gaze"}, {"name": "nu jazz"}, {"name": "nu metal"}, {"name": "nu skool breaks"}, {"name": "nu-cumbia"}, {"name": "nueva cancion"},
 {"name": "nwobhm"}, {"name": "oi"}, {"name": "old school hip hop"}, {"name": "old-time"}, {"name": "opera"}, {"name": "operatic pop"}, {"name": "opm"}, {"name": "oratory"}, {"name": "orchestral"}, {"name": "orgcore"}, 
 {"name": "outlaw country"}, {"name": "outsider"}, {"name": "pagan black metal"}, {"name": "pagode"}, {"name": "pakistani pop"}, {"name": "persian pop"}, {"name": "peruvian rock"}, {"name": "piano blues"}, {"name": "piano rock"}, 
 {"name": "piedmont blues"}, {"name": "pipe band"}, {"name": "poetry"}, {"name": "polish hip hop"}, {"name": "polish pop"}, {"name": "polish reggae"}, {"name": "polka"}, {"name": "polynesian pop"}, {"name": "pop"}, 
 {"name": "pop christmas"}, {"name": "pop emo"}, {"name": "pop punk"}, {"name": "pop rap"}, {"name": "pop rock"}, {"name": "portuguese rock"}, {"name": "post rock"}, {"name": "post-disco"}, {"name": "post-grunge"}, {"name": "post-hardcore"}, 
 {"name": "post-metal"}, {"name": "post-post-hardcore"}, {"name": "post-punk"}, {"name": "power blues-rock"}, {"name": "power electronics"}, {"name": "power metal"}, {"name": "power noise"}, {"name": "power pop"}, {"name": "power violence"}, 
 {"name": "power-pop punk"}, {"name": "progressive bluegrass"}, {"name": "progressive electro house"}, {"name": "progressive house"}, {"name": "progressive metal"}, {"name": "progressive psytrance"}, {"name": "progressive rock"}, 
 {"name": "progressive trance"}, {"name": "protopunk"}, {"name": "psych gaze"}, {"name": "psychedelic rock"}, {"name": "psychedelic trance"}, {"name": "psychill"}, {"name": "psychobilly"}, {"name": "pub rock"}, {"name": "punjabi"}, 
 {"name": "punk"}, {"name": "punk blues"}, {"name": "punk christmas"}, {"name": "qawwali"}, {"name": "quebecois"}, {"name": "quiet storm"}, {"name": "r&b"}, {"name": "r-neg-b"}, {"name": "ragtime"}, {"name": "rai"}, {"name": "ranchera"}, 
 {"name": "rap"}, {"name": "rap metal"}, {"name": "rap rock"}, {"name": "raw black metal"}, {"name": "reggae"}, {"name": "reggae fusion"}, {"name": "reggae rock"}, {"name": "reggaeton"}, {"name": "regional mexican"}, {"name": "renaissance"}, 
 {"name": "retro metal"}, {"name": "riddim"}, {"name": "riot grrrl"}, {"name": "rock"}, {"name": "rock 'n roll"}, {"name": "rock catala"}, {"name": "rock en espanol"}, {"name": "rock steady"}, {"name": "rockabilly"}, {"name": "romanian pop"}, 
 {"name": "romantic"}, {"name": "roots reggae"}, {"name": "roots rock"}, {"name": "rumba"}, {"name": "russian hip hop"}, {"name": "russian pop"}, {"name": "russian punk"}, {"name": "russian rock"}, {"name": "salsa"}, {"name": "samba"}, 
 {"name": "schlager"}, {"name": "schranz"}, {"name": "scottish rock"}, {"name": "screamo"}, {"name": "screamo punk"}, {"name": "sega"}, {"name": "serialism"}, {"name": "sertanejo"}, {"name": "sertanejo tradicional"}, 
 {"name": "sertanejo universitario"}, {"name": "sexy"}, {"name": "shibuya-kei"}, {"name": "shimmer pop"}, {"name": "shimmer psych"}, {"name": "shiver pop"}, {"name": "shoegaze"}, {"name": "show tunes"}, {"name": "singer-songwriter"}, 
 {"name": "ska"}, {"name": "ska punk"}, {"name": "skate punk"}, {"name": "skiffle"}, {"name": "skweee"}, {"name": "slam death metal"}, {"name": "slovak pop"}, {"name": "slovenian rock"}, {"name": "slow core"}, {"name": "sludge metal"}, 
 {"name": "smooth jazz"}, {"name": "soca"}, {"name": "soft rock"}, {"name": "soukous"}, {"name": "soul"}, {"name": "soul blues"}, {"name": "soul christmas"}, {"name": "soul jazz"}, {"name": "soundtrack"}, {"name": "south african jazz"}, 
 {"name": "southern gospel"}, {"name": "southern hip hop"}, {"name": "southern rock"}, {"name": "southern soul"}, {"name": "space rock"}, {"name": "spanish hip hop"}, {"name": "spanish indie pop"}, {"name": "spanish pop"}, 
 {"name": "spanish punk"}, {"name": "speed garage"}, {"name": "speed metal"}, {"name": "speedcore"}, {"name": "spoken word"}, {"name": "steampunk"}, {"name": "stomp and holler"}, {"name": "stomp pop"}, {"name": "stoner metal"}, 
 {"name": "stoner rock"}, {"name": "straight edge"}, {"name": "stride"}, {"name": "string quartet"}, {"name": "suomi rock"}, {"name": "surf music"}, {"name": "swamp blues"}, {"name": "swedish hip hop"}, {"name": "swedish indie pop"}, 
 {"name": "swedish pop"}, {"name": "swedish punk"}, {"name": "swing"}, {"name": "swiss rock"}, {"name": "sxsw"}, {"name": "symphonic black metal"}, {"name": "symphonic metal"}, {"name": "symphonic rock"}, {"name": "synthpop"}, 
 {"name": "taiwanese pop"}, {"name": "talent show"}, {"name": "tamil"}, {"name": "tango"}, {"name": "tech house"}, {"name": "technical death metal"}, {"name": "techno"}, {"name": "teen pop"}, {"name": "tejano"}, {"name": "tekno"}, 
 {"name": "telugu"}, {"name": "texas blues"}, {"name": "texas country"}, {"name": "thai pop"}, {"name": "thrash core"}, {"name": "thrash metal"}, {"name": "throat singing"}, {"name": "tico"}, {"name": "tin pan alley"}, 
 {"name": "traditional blues"}, {"name": "traditional country"}, {"name": "traditional folk"}, {"name": "trance"}, {"name": "trance hop"}, {"name": "trap music"}, {"name": "trapstep"}, {"name": "tribal house"}, {"name": "tribute"}, 
 {"name": "trip hop"}, {"name": "tropical"}, {"name": "trova"}, {"name": "turbo folk"}, {"name": "turkish folk"}, {"name": "turkish pop"}, {"name": "turntablism"}, {"name": "twee pop"}, {"name": "twin cities indie"}, {"name": "uk garage"}, 
 {"name": "uk post-punk"}, {"name": "ukrainian rock"}, {"name": "underground hip hop"}, {"name": "underground power pop"}, {"name": "underground rap"}, {"name": "uplifting trance"}, {"name": "urban contemporary"}, {"name": "vallenato"}, 
 {"name": "vaporwave"}, {"name": "vegan straight edge"}, {"name": "velha guarda"}, {"name": "venezuelan rock"}, {"name": "video game music"}, {"name": "vienna indie"}, {"name": "vietnamese pop"}, {"name": "viking metal"}, {"name": "violin"}, 
 {"name": "viral pop"}, {"name": "visual kei"}, {"name": "vocal house"}, {"name": "vocal jazz"}, {"name": "vocaloid"}, {"name": "volksmusik"}, {"name": "warm drone"}, {"name": "welsh rock"}, {"name": "west coast rap"}, 
 {"name": "western swing"}, {"name": "wind ensemble"}, {"name": "witch house"}, {"name": "wonky"}, {"name": "workout"}, {"name": "world"}, {"name": "world christmas"}, {"name": "world fusion"}, {"name": "worship"}, {"name": "ye ye"}, 
 {"name": "yugoslav rock"}, {"name": "zeuhl"}, {"name": "zim"}, {"name": "zouglou"}, {"name": "zouk"}, {"name": "zydeco"}], "total": 805}}

	