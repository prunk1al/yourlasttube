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

import Class
import artist
import album
import track
import image
import tools
import string


def get_album_from_track(track_mbid):
	logging.error("get album from %s"%track_mbid)
	qry=Class.Tracks().query(Class.Tracks.track_mbid==track_mbid).get(keys_only=True)
	if qry is not None:
		album=qry.parent().get()
		logging.error(album)
def get_artist_from_track(track_mbid):
	logging.error("get artist from %s"%track_mbid)
	qry=Class.Tracks().query(Class.Tracks.track_mbid==track_mbid).get(keys_only=True)
	if qry is not None:
		artist=qry.parent().parent().get()

		return artist
	else:
		return Class.Artists()

def get_artist_name_from_track(track_mbid):
	artist=get_artist_from_track(track_mbid)
	logging.error(artist)
	if artist is not None:
		logging.error(artist.artist_name)
		return artist.artist_name
	else:
		return " "



def get_playlist_from_Home(playlist_name):
	playlist=memcache.get(playlist_name)
	if playlist is not None:
		logging.error("playlist from memcache")
		return playlist

	playlist_class=ndb.Key(Class.Playlists,playlist_name).get()
	logging.error(playlist_class)
	if playlist_class is not None:
		
		logging.error("playlist from db")
		memcache.set(playlist_name,playlist_class.playlist_videos)
		return playlist_class.playlist_videos

	return None


"""
def get_echonest_playlist(tipo,mbid):
	song=[]
	playlist_name="%s %s playlist"%(tipo,mbid)

	playlist =get_playlist_from_Home(playlist_name)

	if playlist is not None:
		return playlist

	logging.error(playlist_name)
	playlist={"data":[]}

	ancestor_key=ndb.Key(Class.Artists,mbid)
	artist_data=ancestor_key.get()
	if artist_data is None:
		artist_data=artist.get_artist_albums(mbid)[0]
	artist_name=artist_data.artist_name

	
	url=tools.get_url("lastfm","artisttoptags",artist_data.artist_mbid)


	j=tools.get_json(url)

	for i in j['toptracks']['track']:
		track_name=i['name']

		tracks=Class.Tracks().query(Class.Tracks.track_name==track_name,ancestor=ancestor_key).get()

		if tracks is None:
			track_video=track.get_video(artist_name,track_name)
		else:
			track_video=tracks.track_video	
        
		video={"video_artist":artist_name,"video_track":track_name,"playlist_videos":track_video}
	
		playlist["data"].append(video)

	p=Class.Playlists(playlist_name=playlist_name,playlist_json=j,playlist_videos=playlist,key=ndb.Key(Class.Playlists,playlist_name))
	p.put()
	memcache.set(playlist_name,playlist)
	return playlist
"""
def get_echonest_playlist(tipo,mbid):
	if tipo=="artist":
		url=tools.get_url("echonest","artist",mbid)
		j=tools.get_json(url)
		return j["response"]["songs"]



def get_echonest_tag_genre(genre):
	playlist_name=" %s radio playlist"%(genre)

	playlist =get_playlist_from_Home(playlist_name)

	if playlist is not None:
		return playlist

	else:
		playlist={"data":[]}
		url=tools.get_url("echonest","genre",genre).replace(" ","%20")
		logging.error(url)
		j=tools.get_json(url)
		logging.error(j)
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
		return playlist

def get_echonest_radio(tipo, mbid):
	song=[]
	playlist_name="%s %s radio playlist"%(tipo,mbid)

	playlist =get_playlist_from_Home(playlist_name)

	if playlist is not None:
		return playlist


	logging.error(playlist_name)
	playlist={"data":[]}


	url=tools.get_url("echonest","playlist",mbid)


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
	return playlist



def get_echonest_tag_radio(genre):
	song=[]
	playlist_name="%s radio playlist"%genre

	playlist =get_playlist_from_Home(playlist_name)
	logging.error(playlist_name)
	return(check_playlist(playlist_name))

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



	