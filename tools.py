import urllib2
import urllib
import os
import webapp2
import jinja2
import logging
import json
import time
import cgi
from google.appengine.api import memcache
from google.appengine.ext import db
from xml.dom import minidom



class Tracks(db.Model):
    song=db.StringProperty(required=True)
    video=db.StringProperty(required=True)
    track_mbid=db.StringProperty(required=True)
    album_mbid=db.StringProperty(required=True)
    artist_mbid=db.StringProperty(required=True)
    
    created=db.DateTimeProperty(auto_now_add=True)

class Artist(db.Model):
    artist=db.StringProperty(required=True)
    mbid=db.StringProperty(required=True)
    created=db.DateTimeProperty(auto_now_add=True)
    disambiguation=db.StringProperty(required=True)

class Album(db.Model):
    mbid=db.StringProperty(required=True)
    album=db.StringProperty(required=True)
class Genres(db.Model):
    genre=db.StringProperty(required=True)
    track_mbid=db.ListProperty(unicode,required=True)

def get_dbArtist(artist):

    query="select * from Artist where artist='%s'"%artist
    logging.error("get_dbArtist query")
    logging.error(query)
    data=memcache.get(query)
    
    if data is not None:
        if data!= []:
            if data[0].disambiguation is not None:
                data=None
        if data is not None:
            logging.error("mbid from memcache get_dbArtist")
            return data
    
    data=list(db.GqlQuery(query))
    memcache.set(query,data)
    if data != []:
        logging.error("mbid from db get_dbArtist")
    return data




def  get_similar(artist=""):
    
    data=memcache.get("similar_%s"%artist)
    if data is not None:
        return data

    API_KEY= '51293239750eea5095511e23b3107e31'

    SERVER = 'ws.audioscrobbler.com/2.0'              
    SERVICE = '/?method=artist.getsimilar&'         
    params = "artist="+artist.replace(" ","+")+"&api_key="+API_KEY+"&limit=10"
       
    url ='http://%s%s%s' % (SERVER,SERVICE,params) 
    logging.error(url)

    time.sleep(1) 
    page=urllib2.urlopen(url)
    xml=minidom.parseString(page.read())
    names=xml.getElementsByTagName("url")
    i=0
    similar=[]
    for x in names:
        name=x.childNodes[0].nodeValue[18:]
        similar.append(name.replace("+"," "))
        i=i+1
        if i>=5:
            break
    memcache.set("similar_%s"%artist,data)
    return similar

def get_data(artist,d=False, I=False):
    logging.error("getting data of %s"%artist)
    data=get_dbArtist(artist)
    if data != []:
        logging.error("mbid from db or memcache get_data")
        return data


    SERVER = 'www.musicbrainz.org'              
    SERVICE = '/ws/2/artist/?'         
    params = 'alias:"'+artist+'"OR artist:"'+artist+'"'
    x=urllib.urlencode({"query":params})
    url ='http://%s%s%s' % (SERVER,SERVICE,x.replace("OR+","OR%20"))

    logging.error(url)
    xml=memcache.get("mb %s"%artist)
    if xml is None:
        time.sleep(1)
        page=urllib2.urlopen(url)
        xml=minidom.parseString(page.read())
        memcache.set("mb %s"%artist,xml)

    parsed=xml.getElementsByTagName("artist")
    
    
    mbid=[]
    for a in parsed:
        
        mbidId=a.attributes.get("id").value
        name=a.getElementsByTagName("name")[0].childNodes[0].nodeValue
        disambiguation=""

        try:
            disambiguation=a.getElementsByTagName("disambiguation")[0].childNodes[0].nodeValue
            if d==False:
                logging.error("Not listing %s because has disambiguation"%name)
                continue
        except:
            disambiguation=" "
        logging.error("DESAMBIGUACION")
        logging.error(disambiguation)
        if d==True:
            genres=get_genres(mbidId)
                   
            
       
        ar=Artist(artist=name, mbid=mbidId, disambiguation=disambiguation)
        if I==True:
            logging.error("INSERTING %s IN DATABASE"%name)
            ar.put()
        mbid.append(ar)
        memcache.set("select * from Artist where artist='%s'"%name,[ar])

        

    return mbid

def get_albums_mb(mbid):

    url="http://musicbrainz.org/ws/2/release-group?artist="+mbid+"&type=album"
    logging.error(url)
    time.sleep(1)
    page=urllib2.urlopen(url)
    xml=minidom.parseString(page.read())
    parsed=xml.getElementsByTagName("release-group")

    albums=[]
    for rg in parsed:
        album=(rg.attributes.get("id").value,rg.getElementsByTagName("title")[0].childNodes[0].nodeValue)

        try:
            a=rg.getElementsByTagName("secondary-type")[0]
            continue
        except:
            pass

        albums.append(album)

    return(albums)


def get_tracks_mb(mbid):
    


    """CAMBIAR PARA QUE MEMCACHE RECOJA LOS CAMBIOS DE CANCION"""



    """buscamos el album con mayor numero de pistas"""
    query="select * from Tracks where album_mbid='%s'"%mbid
    logging.error(query)

    data=memcache.get(query)
    if data is not None:
        logging.error("mbid from memcache")
        return data
    else:
        logging.error("tracks not in memcache")


    d=list(db.GqlQuery(query))
    
    if d != []:
        logging.error("mbid from db")
        data=[]
        for t in d:
            data.append([t.track_mbid,t.song,t.artist_mbid])
        memcache.set(query,data)

        return data



    logging.error("track data from url")
    url="http://www.musicbrainz.org/ws/2/release?release-group="+mbid+"&inc=recordings+artist-credits"
    logging.error(url)
    time.sleep(1)
    page=urllib2.urlopen(url)
    xml=minidom.parseString(page.read())
    release=xml.getElementsByTagName("release")

    track_n=0
    for r in release:
        
        track_c=r.getElementsByTagName("track-list")[0].attributes.get("count").value
        artist_mbid=r.getElementsByTagName("artist-credit")[0].getElementsByTagName("artist")[0].attributes.get("id").value
        if track_c > track_n:
            track_n=int(track_c)
            tracks=[]
            for t in r.getElementsByTagName("track"):
                track_mbid=t.getElementsByTagName("recording")[0].attributes.get("id").value
                track_name=t.getElementsByTagName("title")[0].childNodes[0].nodeValue
                
                

                tracks.append((track_mbid, track_name ,artist_mbid))
    

    """insertamos en la base de datos"""

    album,artist=get_album_mb(mbid)
    logging.error("ARTISTA:%s"%artist)

    for t in tracks:
        song=t[1]
        video=get_video(artist,song)

        if video != []:
            track_genres=get_track_genre(track_mbid)
            for genre in track_genres:
                data=memcache.get(genre)
                if data is None:
                    k="select * from Genres where genre='%s'"% genre
                    logging.error(k)
                    data=db.GqlQuery(k)
                    logging.error(data.get())
                    if data.get() is None:
                        logging.error("CREANDO GENRE")
                        data=Genres(genre=genre)
                        logging.error(track_mbid)
                        data.track_mbid=[track_mbid]
                    
                if track_mbid not in data.track_mbid:
                    data.track_mbid.append(track_mbid)
                    logging.error(data.track_mbid)
                data.put()
                logging.error("FIN INSERCION")
                memcache.set(genre,data)

        track_mbid=t[0]
        album_mbid=mbid
        artist_mbid=t[2]

        p=Tracks(song=song,video=video,track_mbid=track_mbid,album_mbid=album_mbid,artist_mbid=artist_mbid)
        memcache.set(track_mbid,p)
        p.put()
    memcache.set(query,tracks)
    logging.error(tracks)
    return tracks

def get_artist_mb(mbid):
    data=memcache.get("%s artist="%mbid)
    if data is not None:
        return data

    data=list(db.GqlQuery("select artist from Artist where mbid='%s'"%mbid))
    if data != []:
        memcache.set("%s artist="%mbid, data[0].artist)
        return data[0].artist

    url="http://www.musicbrainz.org/ws/2/artist/?query=arid:"+mbid
    logging.error(url)
    time.sleep(1)
    page=urllib2.urlopen(url)
    xml=minidom.parseString(page.read())
    name= xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
    memcache.set("%s artist="%mbid, name)
    return name

def get_album_mb(mbid):
    url="http://www.musicbrainz.org/ws/2/release-group/"+mbid+"?inc=artists"
    logging.error(url)
    time.sleep(1)
    page=urllib2.urlopen(url)
    xml=minidom.parseString(page.read())
    return xml.getElementsByTagName("title")[0].childNodes[0].nodeValue,xml.getElementsByTagName("name")[0].childNodes[0].nodeValue 



def get_video(artist,song):
    song=song.replace(" ","+").replace("-","+").replace("'","")
    
    data=memcache.get("%s,%s"%(artist,song))
    
    if data is None:
        v=[]
        if v !=[]:
            data=v[0].video
        else:
            
            query="http://gdata.youtube.com/feeds/api/videos?q="+artist+"+"+song+"+official+video&max-results=1&v=2&format=5&key=AI39si42ldETBAU7tY22n0DCKTn1jBDj3Hx4_RwMjQvzW27yyQ_q4QjekBC7rfEd80rMArD6wZxmngyEK0IDb9rUrN28uW6Ybw"
            query=query.replace(" ","+")
            logging.error(query)
            time.sleep(1)
            page=urllib2.urlopen(query)
            xml=minidom.parseString(page.read())
            if  xml.getElementsByTagName("yt:videoid")!= []:
                data=xml.getElementsByTagName("yt:videoid")[0].childNodes[0].nodeValue
            else:
                data=" "
        memcache.set("%s,%s"%(artist,song),data)
 
    return data

def get_genres(mbid):
    data=memcache.get("genres %s" % mbid)
    if data is not None:
        return data

    API_KEY= '51293239750eea5095511e23b3107e31'
    url="http://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&mbid="+mbid+"&api_key="+API_KEY+"&limit=5"
    logging.error(url)
    try:
        page=urllib2.urlopen(url)
        xml=minidom.parseString(page.read())
        tags=xml.getElementsByTagName("tag")

        count=0
        genres=[]
        for t in tags:
            genres.append(t.getElementsByTagName("name")[0].childNodes[0].nodeValue)
            count=count+1
            if count>=5:
                break
            
            logging.error(genres)

        memcache.set("genres %s"%mbid, genres)
        return genres

    except:
        logging.error("error en last.fm")
        return []


def get_track(mbid):
    data=memcache.get(mbid)
    if data is not None:
        return data
    query="select * from Tracks where track_mbid='%s'"%mbid
    logging.error(query)
    track=list(db.GqlQuery(query))

    data=track[0]
    
    memcache.set(mbid, data)
    return data

def get_image(mbid,key=""):
    data=memcache.get("image %s %s"%(mbid,key))
    if data is not None:
        return data

    logging.error("GETTING IMAGES")
    API_KEY= '51293239750eea5095511e23b3107e31'
    url="http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&mbid="+mbid+"&api_key="+API_KEY
    logging.error(url)

    try:
        page=urllib2.urlopen(url)
        xml=minidom.parseString(page.read())

        artists=xml.getElementsByTagName("artist")

        for artist in artists:

           
            id=artist.getElementsByTagName("mbid")[0].childNodes[0].nodeValue
            if id==mbid:
              
                image=artist.childNodes[11].childNodes[0].nodeValue
                
                break
              
        memcache.set("image %s %s"%(mbid,key),image)
        return image

    except:
        logging.error("error en last.fm")
        return " "

def get_track_genre(mbid):

    data=memcache.get("genre %s"%mbid)
    if data is not None:
        return data

    logging.error("Getting Track Genre")

    API_KEY= '51293239750eea5095511e23b3107e31'
    url="http://ws.audioscrobbler.com/2.0/?method=track.gettoptags&mbid="+mbid+"&api_key="+API_KEY
    logging.error(url)

    try:
        page=urllib2.urlopen(url)
        
        xml=minidom.parseString(page.read())
        
        tags=xml.getElementsByTagName("tag")

        genre=[]
        for tag in tags:
            name=tag.childNodes[1].childNodes[0].nodeValue
            count=tag.getElementsByTagName("count")[0].childNodes[0].nodeValue
            logging.error(name)
            logging.error(count)
            
            if int(count)>=100:
                genre.append(name)

            else:
                break
        
        memcache.set("genre %s"%mbid,genre)
        return genre
    except:
        logging.error("fallo al descargar TrackTags")