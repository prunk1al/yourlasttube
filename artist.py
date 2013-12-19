import logging 
from google.appengine.api import memcache
from google.appengine.ext import ndb
import tools
import image
import Class
from google.appengine.api.labs import taskqueue
import track
import time

def get_artist_albums(artist_mbid):
    

    albums=[]
    try:
        artist=Class.Artists.query(Class.Artists.artist_mbid==artist_mbid).get()
    except:
        artist=None
    if artist is not None:
        for i in Class.Albums.query(ancestor=artist.key).iter():
            albums.append(i)
        
        if len(albums)>0:
            logging.error("return from database")
            return artist, albums
                   
    albums=[]

    logging.error("START OF Artist_ALBUMS")

    url=tools.get_url("musicbrainz","artist_mbid",artist_mbid)
    xml=tools.get_xml(url)
    try:
        artist_name= xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
    except:
        return None
    logo=image.get_image(artist_mbid,'logo')     
    background=image.get_image(artist_mbid,'bg')
    
    artist=Class.Artists(artist_name=artist_name, artist_mbid=artist_mbid,disambiguation=" ",letter=artist_name[0], key=ndb.Key(Class.Artists,artist_mbid))
    artist.logo=logo
    artist.background=background
    try:
        artist_key=artist.put()  
    except:
        pass

    logging.debug(artist)


    releases=xml.getElementsByTagName("release-group")
    for rg in releases:

        try:
            if rg.getElementsByTagName("primary-type")[0].childNodes[0].nodeValue != "Album":
                continue
            error=rg.getElementsByTagName("secondary-type")[0]
            continue
        except:
            try:
                if rg.attributes.get("type").value == "Album":

                    album_mbid=rg.attributes.get("id").value
                    b=Class.Albums(key=ndb.Key(Class.Albums,album_mbid,parent=ndb.Key(Class.Artists,artist_mbid)))
                    b.ancestor=ndb.Key(Class.Artists,artist_mbid)
                    b.album_mbid=album_mbid
                    b.album_name=rg.getElementsByTagName("title")[0].childNodes[0].nodeValue
                    b.album_date=rg.getElementsByTagName("first-release-date")[0].childNodes[0].nodeValue
                    b.album_image=image.get_image(album_mbid, key="album")
                    logging.debug(b)
                    albums.append(b)
                    
            except:
                continue

    albums.sort(key=lambda tup: tup.album_date)
    try:
        test=ndb.put_multi(albums)
    except:
        pass

    logging.error("END OF Artist_ALBUMS")

    return artist,albums


def getAlbumFromMBrainz(mbid):
    logging.error("START OF getAlbumFromMBrainz")
    albums=[]

    url=tools.get_url("musicbrainz","artist_mbid",mbid)
    xml=tools.get_xml(url)

    try:
        artist_name= xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
    except:
        return None
    

    releases=xml.getElementsByTagName("release-group")
    for rg in releases:

        try:
            if rg.getElementsByTagName("primary-type")[0].childNodes[0].nodeValue != "Album":
                continue
            error=rg.getElementsByTagName("secondary-type")[0]
            continue
        except:
            try:
                if rg.attributes.get("type").value == "Album":
                    album={}
                    album["mbid"]=rg.attributes.get("id").value
                    album["name"]=rg.getElementsByTagName("title")[0].childNodes[0].nodeValue
                    album["date"]=rg.getElementsByTagName("first-release-date")[0].childNodes[0].nodeValue
                    albums.append(album)
                    
            except:
                continue
    logging.error(albums)
    logging.error("END OF Artist_ALBUMS")
    albums.sort(key=lambda tup: tup["date"], reverse=True)

    return albums


def getXhrAlbums(mbid=""):
    

    albums= getAlbumFromMBrainz(mbid)
    logging.error(albums)

    return albums




def get_xhrsimilar(mbid=""):
    similars=[]
    logging.error("GETTING SIMILAR FROM ECHONEST")
    url=tools.get_url('lastfm','similar',mbid)
    j=tools.get_json(url)
    
    if j is None:
        return []
    
    try:
        a=j['similarartists']['artist']
    except:
        return []
    for i in a:
        name=i['name']
        similar={}
        similar["name"]=name
        similar["mbid"]=i['mbid']
        logging.error(similar)
        similars.append(similar)

    return similars

def  get_similar(mbid=""):
    
    data=memcache.get("similar_%s"%mbid)
    
    if data is not None:
        return data

    similars=[]
    logging.error("GETTING SIMILAR FROM ECHONEST")
    url=tools.get_url('echonest','similar',mbid)
    j=tools.get_json(url)
    
    if j is None:
        return []
    
    try:
        a=j['response']['artists']
    except:
        return []
    for i in j['response']['artists']:
        name=i['name']
        if 'foreign_ids' in i.keys():
            similar=Class.Artists()
            similar.artist_name=name
            similar.artist_mbid=i['foreign_ids'][0]['foreign_id'][19:]
            similar.logo=image.get_image(similar.artist_mbid,"logo")
        
            similars.append(similar)
        
        logging.debug(similars)
    logging.error("END OF ECHONEST CODE")
    memcache.set("similar_%s"%mbid,similars)   
    return similars


def get_artist_logo(mbid):
    url=tools.get_url('fanart','artist',mbid)
    j=tools.get_json(url)
    if j is None:
        return None
    for i in j:
        try:
            logo=j[i]['musiclogo'][0]['url']+'/preview'
        except:
            return None
    return logo


def get_artist_mb(mbid):
    data=memcache.get("%s artist="%mbid)
    if data is not None:
        return data
    try:
        data=Class.Artists.query(artist_mbid==artist_mbid).get()

        if data != []:
            memcache.set("%s artist="%mbid, data)
            return data
    except:
        pass

    url="http://www.musicbrainz.org/ws/2/artist/?query=arid:"+mbid
    xml=tools.get_xml(url)

    if xml.getElementsByTagName("artist-list")[0].attributes.get("count").value == '1':
        artist_name= xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
        artist_mbid=mbid        
        logo=image.get_image(artist_mbid,'logo')     
        background=image.get_image(artist_mbid,'bg')

        artist=Class.Artists(artist_name=artist_name, artist_mbid=artist_mbid,disambiguation=" ",letter=artist_name[0], key=ndb.Key(Class.Artists,artist_mbid))
        artist.logo=logo
        artist.background=background


        try:
            artist_key=artist.put()
        except:
            artist_key=None 
            
        return artist

def search_artist(artist_name):

    
    logging.error("getting data of %s"%artist_name)
    data=Class.Artists.query(Class.Artists.artist_name==artist_name).get()
    if data is not None:
        logging.error("mbid from ndb or memcache get_data")
        return [data]
    
    url=tools.get_url('musicbrainz','artist',artist_name)
    logging.error(url)
    xml=tools.get_xml(url)
    parsed=xml.getElementsByTagName("artist")
    
    disambiguation=" "
    artists=[]

    if xml.getElementsByTagName("artist-list")[0].attributes.get("count").value == '1' :
        
        artist_mbid=parsed[0].attributes.get("id").value
        artist_data,album_data=get_artist_albums(artist_mbid)
        artists.append(artist_data)
    else:
        
        for a in parsed:
            artist={}

            artist["mbid"]=a.attributes.get("id").value
            artist["name"]=a.getElementsByTagName("name")[0].childNodes[0].nodeValue
            try:
                artist["country"]=a.getElementsByTagName("area")[0].getElementsByTagName("name")[0].childNodes[0].nodeValue
            except:
                artist["country"]=""

            try:
                disambiguation=a.getElementsByTagName("disambiguation")[0].childNodes[0].nodeValue
            except:
                disambiguation=" "
            
            #artist_data=Class.Artists(artist_name=name, artist_mbid=mbidId, disambiguation=disambiguation, letter=name[0])
            

            artists.append(artist)
            
    

    return artists
def crawl_artist(artist_name):
    t=search_artist(artist_name)
                        
    for m in t:
        logging.error(m)
        if artist_name==m.artist_name:
            
                
            taskqueue.add(url='/worker',params={'f': '[track.get_tracks(w.album_mbid) for w in  artist.get_artist_albums("%s")[1]]'%m.artist_mbid})



from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def getArtistInfo(mbid):
    logging.error("getArtistInfo")
    url=tools.get_url("lastfm","artistInfo",mbid)
    logging.error(url)
    j=tools.get_json(url)
    data=j["artist"]["bio"]["content"]
    return strip_tags(data)

def getArtistTags(mbid):
    logging.error("getArtistTags")
    url=tools.get_url("lastfm","artistTags",mbid)
    logging.error(url)
    j=tools.get_json(url)
    data=[]
    for tag in j["toptags"]["tag"]:
        if int(tag["count"])>=30:
            data.append(tag["name"])
    return data
    