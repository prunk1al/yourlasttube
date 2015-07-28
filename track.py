import urllib
import time
import logging 
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api.labs import taskqueue
import tools
import album
import artist
import async
import Class


class Track(ndb.Model):
    artistKey=ndb.KeyProperty(required=False)
    ytid=ndb.StringProperty(required=False)



    def getVideo(self):
        logging.error(self)
        name, artist=self.key.id().split(' - ')

        data=memcache.get("%s,%s"%(artist,name))

        if data is None:
            key=ndb.Key('Track',name+ ' - ' + artist)
            data=key.get()

        if data is None:
            song=name.replace(" ","%20").replace("-","+").replace("'","")
            data= None
            #
            
            if data is None:
                v=[]
                if v !=[]:
                    data=v[0].video
                else:
                    
                    url=tools.get_url('youtube','video',[artist,name])
                    logging.error(url)
                    j=tools.getjson(url)
                    
                    data=j["items"][0]["id"]["videoId"]
                    self.ytid=data
                    data=self
                    self.put()

                    memcache.set("%s,%s"%(artist,name),self.ytid)

        try:
            self.ytid=data.ytid
        except:
            self.ytid=""
      
        
        











def get_tracks(mbid,key=None):

    tracks=memcache.get('get_tracks: %s'%mbid)
    if tracks is not None:
        return tracks

    albums=Class.Albums.query(Class.Albums.album_mbid==mbid).get(keys_only=True)
    tracks=Class.Tracks.query(ancestor=albums).fetch()
    if tracks != []:
        return tracks
    
    

    logging.error("track data from url")
    album_mbid=mbid
    url=tools.get_url('musicbrainz','tracks',mbid)
    xml=tools.get_xml(url)

    release=xml.getElementsByTagName("release")

    tracks=[]
    track_n=0
    for r in release:
        
        track_c=r.getElementsByTagName("track-list")[0].attributes.get("count").value
        artist_mbid=r.getElementsByTagName("artist-credit")[0].getElementsByTagName("artist")[0].attributes.get("id").value
        artist_name=r.getElementsByTagName("artist-credit")[0].getElementsByTagName("name")[0].childNodes[0].nodeValue
        if track_c > track_n:
            track_n=int(track_c)
            tracks=[]
            
            for t in r.getElementsByTagName("track"):
                track_mbid=t.getElementsByTagName("recording")[0].attributes.get("id").value
                track_name=t.getElementsByTagName("title")[0].childNodes[0].nodeValue
                track_number=int(t.getElementsByTagName("position")[0].childNodes[0].nodeValue)

                T=Class.Tracks(track_name=track_name,track_video=" ",track_mbid=track_mbid,track_number=track_number,key=ndb.Key(Class.Tracks,track_mbid,parent=ndb.Key(Class.Albums,album_mbid,parent=ndb.Key(Class.Artists,artist_mbid))))
                T.ancestor=ndb.Key(Class.Albums,album_mbid)
                tracks.append(T)
   
   
            
           
    

   
    if key is None:
    
        logging.info("Get videos async")
        try:
            logging.error(tracks)
            tracks=get_videos(tracks)
            #track=get_hottness(tracks)
            ndb.put_multi(tracks)
        except:
            logging.error("Get videos syncronous")
            for i in tracks:
                i.track_video=get_video(artist_name,i.track_name)
               
    else:
        logging.error("Get videos syncronous")
        for i in tracks:
            i.track_video=get_video(artist_name,i.track_name)
            

    memcache.set("get_tracks: %s"%mbid,tracks)
    #taskqueue.add(url='/worker', params={'f':'track.get_tracks_genre(%s)'%tracks})
    
    
    
    return tracks



def get_track_hottness(mbid,artist_name,track_name):


	hottness=0.0

	"""data=memcache.get("hottness %s"%mbid)
    if data is not None:
        return data

    
    
    ar=urllib.quote(artist_name.encode('utf8'))

    song=urllib.quote(track_name.encode('utf8'))

    url=tools.get_url('echonest','genre',[ar,song])
    
    j=tools.get_json(url)
    try:
        hottness=float(j["response"]["songs"][0]["song_hotttnesss"])
    except:
        hottness=0.0   

    memcache.set("hottness %s"%mbid,hottness)"""
    
	return(hottness)

def get_video_db(artist_name,song):

    artist=Class.Artists().query(Class.Artists.artist_name==artist_name).get(keys_only=True)

    if artist is not None:
        video=Class.Tracks().query(Class.Tracks.track_name==song,ancestor=artist).get()
 
        if video  is not None:
            logging.error(video)
            return video.track_video

    return None

def get_video(artist_name,song):
    song=song.replace(" ","%20").replace("-","+").replace("'","")
    
    data= None
    data=memcache.get("%s,%s"%(artist_name,song))
    
    if data is None:
        v=[]
        if v !=[]:
            data=v[0].video
        else:
            
            url=tools.get_url('youtube','video',[artist_name,song])
            logging.error(url)
            j=tools.get_json(url)
            
            data=j["feed"]["entry"][0]['media$group']['yt$videoid']['$t']
            
        memcache.set("%s,%s"%(artist_name,song),data)
 
    return data

def get_videos(tracks):
    
    urls=[]

    for i in tracks:
   	
        song=urllib.quote(i.track_name.encode('utf8'))
        ar=urllib.quote(i.key.parent().get().key.parent().get().artist_name.encode('utf8'))
        video_url=tools.get_url('youtube','video',[ar,song])
        urls.append(video_url)

    return async.get_urls(urls,"videos",tracks)
def get_hottness(tracks):
    urls=[]
    for i in tracks:

        song=urllib.quote(i.track_name.encode('utf8'))
        ar=urllib.quote(i.key.parent().get().key.parent().get().artist_name.encode('utf8'))
        hottness_url=tools.get_url('echonest','genre',[ar,song])
        urls.append(hottness_url)
    return async.get_urls(urls,"videos",tracks)

"""
def getAlbumTracks(mbid):

    tracks=memcache.get('get_tracks: %s'%mbid)
    if tracks is not None:
        return tracks

    logging.error("track data from url")
    album_mbid=mbid
    url=tools.get_url('musicbrainz','tracks',mbid)
    logging.error(url)
    xml=tools.get_xml(url)

    release=xml.getElementsByTagName("release")

    tracks=[]
    track_n=0
    for r in release:
        
        medium=int(r.getElementsByTagName("medium")[0].getElementsByTagName("position")[0].childNodes[0].nodeValue)
        track_c=r.getElementsByTagName("track-list")[0].attributes.get("count").value
        if track_c > track_n:
            track_n=int(track_c)
            tracks=[]
            artist=r.getElementsByTagName("artist-credit")[0].getElementsByTagName("artist")[0].attributes.get("id").value
            artistName=r.getElementsByTagName("artist-credit")[0].getElementsByTagName("artist")[0].childNodes[0].childNodes[0].nodeValue
            for t in r.getElementsByTagName("track"):
                T={}
                T["artist"]={}
                T["artist"]["mbid"]=artist
                T["artist"]["name"]=artistName
                T["mbid"]=t.getElementsByTagName("recording")[0].attributes.get("id").value
                T["name"]=t.getElementsByTagName("title")[0].childNodes[0].nodeValue
                T["number"]=int(t.getElementsByTagName("position")[0].childNodes[0].nodeValue)+(medium*100)
                tracks.append(T)
    logging.error(tracks)
    return tracks
"""
def getAlbumTracks(mbid):
    url=tools.get_url('musicbrainz','tracksj',mbid)
    logging.error(url)
    j=tools.get_json(url)
    tracks=[]
   
    max=0
    temp=0
    for i in range(len(j["releases"])):

        if len(j["releases"][i]["media"]) > temp:
            temp=len(j["releases"][i]["media"])
            max=i

    logging.error(max)
    for r in range(len(j["releases"][max]["media"])):
        for track in j["releases"][max]["media"][r]["tracks"]:
            logging.error(track)
            T={}
            T["artist"]={}
            T["artist"]["mbid"]=track["artist-credit"][0]["artist"]["id"]
            T["artist"]["name"]=track["artist-credit"][0]["artist"]["name"]
            T["mbid"]=track["id"]
            T["name"]=track["title"]
            T["number"]=int(track["number"])+((r+1)*100)
            tracks.append(T)

    return tracks

def getTrackVideo(mbid):
    url=tools.get_url('musicbrainz','recording', mbid)
    j=tools.get_json(url)
    artist_name=j['artist-credit'][0]["artist"]["name"]
    song=j["title"]
    return get_video(artist_name,song)

def checkImage(data):
    return True