
import logging 
from google.appengine.api import memcache
from google.appengine.ext import ndb
import tools
import album
import artist
import async
from google.appengine.api.labs import taskqueue
import urllib
import time

class Tracks(ndb.Model):
    song=ndb.StringProperty(required=True)
    video=ndb.StringProperty(required=True)
    track_mbid=ndb.StringProperty(required=True)
    album_mbid=ndb.StringProperty(required=True)
    artist_mbid=ndb.StringProperty(required=True)
    number=ndb.IntegerProperty(required=True)
    created=ndb.DateTimeProperty(auto_now_add=True)
    hottness=ndb.FloatProperty(default=0.0)
    
class Artist(ndb.Model):
    artist=ndb.StringProperty(required=True)
    mbid=ndb.StringProperty(required=True)
    created=ndb.DateTimeProperty(auto_now_add=True)
    disambiguation=ndb.StringProperty(required=True)
    letter=ndb.StringProperty(required=True)



def get_tracks_mb(mbid,key=None):
    
    
    query="select * from Tracks where album_mbid='%s'"%mbid
    logging.error(query)

    data=memcache.get(query)
    if data is not None:
        logging.error("mbid from memcache")
        return data
    else:
        logging.error("tracks not in memcache")


    d=list(ndb.gql(query))
    
    if d != []:
        logging.error("mbid from ndb")
        data=d
        memcache.set(query,data)

        return data



    logging.error("track data from url")
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
            
                hottness=get_track_hottness(track_mbid,artist_name,track_name)
                tracks.append((track_mbid, track_name ,artist_mbid,track_number,hottness))

    

    

    al,x=album.get_album_mb(mbid)
    artist=x[0]
    logging.error(artist)
    p=[]
    if len(tracks)>1:
        for t in tracks:
            song=t[1]

            track_mbid=t[0]
            album_mbid=mbid
            artist_mbid=t[2]
            track_number=t[3]
            hottness=t[4]
            T=Tracks(song=song,video=" ",track_mbid=track_mbid,album_mbid=album_mbid,artist_mbid=artist_mbid, number=track_number,hottness=hottness)
        
            p.append(T)
            memcache.set(track_mbid,p)
    
    if key is None:
    
        logging.error("Get videos async")
        try:
            get_videos(p)
        
        except:
            logging.error("Get videos syncronous")
            for i in p:
                i.video=get_video(artist_name,i.song)
                logging.error(i)
    else:
        logging.error("Get videos syncronous")
        for i in p:
            i.video=get_video(artist_name,i.song)
            logging.error(i)

    #memcache.set(query,p)
    #taskqueue.add(url='/worker', params={'f':'track.get_tracks_genre(%s)'%tracks})
    
    
    
    return p






def get_video(artist_name,song):
    song=song.replace(" ","+").replace("-","+").replace("'","")
    
    data=memcache.get("%s,%s"%(artist_name,song))
    
    if data is None:
        v=[]
        if v !=[]:
            data=v[0].video
        else:
            
            url=tools.get_url('youtube','video',[artist_name,song])
            xml=tools.get_xml(url)
            if  xml.getElementsByTagName("yt:videoid")!= []:
                data=xml.getElementsByTagName("yt:videoid")[0].childNodes[0].nodeValue
            else:
                data=" "
        memcache.set("%s,%s"%(artist_name,song),data)
 
    return data

def get_videos(tracks):
    urls=[]
    
    for i in tracks:
        song=i.song.replace(" ","+").replace("-","+").replace("'","")
        ar=artist.get_artist_mb(i.artist_mbid)
        url=tools.get_url('youtube','video',[ar,song])
        urls.append(url)
    

        
    async.get_urls(urls,"videos",tracks)



def get_track(mbid):
    logging.error(mbid)
    """data=memcache.get(mbid)
    if data is not None:
        logging.error(data)
        return data"""

    try:
        query="select * from Tracks where track_mbid='%s'"%mbid
        logging.error(query)
        tracks=list(ndb.gql(query))

        data=tracks[0]
    
        """memcache.set(mbid, data)"""
    except:
        url=tools.get_url("musicbrainz","recording",mbid)
        xml=tools.get_xml(url)
        logging.error(xml.toprettyxml())
        data=Tracks()
        data.song=xml.getElementsByTagName("title")[0].childNodes[0].nodeValue
        data.artist_mbid=xml.getElementsByTagName("artist")[0].attributes.get("id").value
        artist=xml.getElementsByTagName("artist")[0].getElementsByTagName("name")[0].childNodes[0].nodeValue
        data.video=get_video(artist,data.song)
    logging.error(data)
    return data


def get_track_name(mbid):
    query="select song from Tracks where track_mbid='%s'"%mbid
    
    tracks=list(ndb.gql(query))

    data=tracks[0]
    
    return data

def get_track_artist(mbid):
    query="select artist_mbid from Tracks where track_mbid='%s'"%mbid
    
    tracks=list(ndb.gql(query))

    data=tracks[0]
    
    return data


def get_track_hottness(mbid,artist_name,track_name):

    data=memcache.get("hottness %s"%mbid)
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

    memcache.set("hottness %s"%mbid,hottness)
    
    return(hottness)

def update_hottness(mbid):

    for t in Tracks.all().filter("track_mbid =", mbid).fetch(1):
        t.hottness=get_track_hottness(t.track_mbid,t.artist_mbid,t.song)
  
        t.put()
    

    
    

def get_track_genre(mbid):
   

    data=memcache.get("genre %s"%mbid)
    if data is not None:
        return data

    logging.error("Getting Track Genre")

    
    url=tools.get_url('lastfm','genres', mbid)
    

    try:
        
        xml=tools.get_xml(url)
        
        tags=xml.getElementsByTagName("tag")

        genre=[]
        for tag in tags:
            name=tag.childNodes[1].childNodes[0].nodeValue.replace("'"," ").title()
            count=tag.getElementsByTagName("count")[0].childNodes[0].nodeValue
            logging.error(name)
            b=list(ndb.gql("select * from Black where genre='%s'"%name))
            if b==[]:
                if int(count)>=100 or len(genre)>=5:
                    if name not in genre:
                        genre.append(name)

                else:
                    break
        
        memcache.set("genre %s"%mbid,genre)
        return genre
    except:
        logging.error("fallo al descargar TrackTags")
        return None

def get_tracks_genre(tracks):
    
    for t in tracks:
        track_mbid=t[0]
        track_genres=get_track_genre(track_mbid)
        if track_genres is not None:

            for genre in track_genres:
                data=memcache.get(genre)
                if data is None :
                    k="select * from Genres where genre='%s'"% genre

                    data=list(ndb.gql(k))
                        
                    if data ==[]:
                        data=[Genres(genre=genre)]
                            
                        data[0].track_mbid=[track_mbid]

                if track_mbid not in data[0].track_mbid:
                    data[0].track_mbid.append(track_mbid)
                try:
                                  
                    data[0].put()
 
                except:
                    pass


                memcache.set(genre,data)
def check_hottness(mbid,hottness):
    logging.error("check_hottness")

    try:
        

        t=list(ndb.gql("select * from Tracks where track_mbid='%s'"%mbid))
        track_name=t[0].song
        artist_mbid=t[0].artist_mbid
    
        a=list(ndb.gql("select artist from Artist where mbid='%s'"%artist_mbid))
        artist_name=a[0].artist

        new_hottness=get_track_hottness(mbid,artist_name,track_name)

        if float(new_hottness) != float(hottness):
            logging.info("inserting in ndb")
            logging.info("new_hottness for %s is %s"%(track_name,new_hottness))
            t[0].hottness=new_hottness
            t[0].put()
    
    except:
        pass 
