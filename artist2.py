

import logging 
from google.appengine.api import memcache
from google.appengine.ext import ndb
import tools
import track
import image


class Artist(ndb.Model):
    artist=ndb.StringProperty(required=True)
    mbid=ndb.StringProperty(required=True)
    created=ndb.DateTimeProperty(auto_now_add=True)
    disambiguation=ndb.StringProperty(required=True)
    letter=ndb.StringProperty(required=True)

class Tracks(ndb.Model):
    name=ndb.StringProperty(required=True)
    video=ndb.StringProperty(required=True)
    mbid=ndb.StringProperty(required=True)
    number=ndb.IntegerProperty(required=True)
    hottness=ndb.FloatProperty(required=False)
    views=ndb.IntegerProperty(default=0)

class Albums(ndb.Model):
    album_mbid=ndb.StringProperty(required=True)
    album_name=ndb.StringProperty(required=True)
    album_date=ndb.StringProperty(required=True)
    album_image=ndb.StringProperty(required=False)


class Artists(ndb.Model):
    artist_name=ndb.StringProperty(required=True)
    artist_mbid=ndb.StringProperty(required=True)
    disambiguation=ndb.StringProperty(required=True)
    letter=ndb.StringProperty(required=False)
    albums=ndb.StructuredProperty(Albums,repeated=True)
    logo=ndb.StringProperty(required=False)
    background=ndb.StringProperty(required=False)

def get_artist_albums(artist_mbid):
    logging.error("START OF Artist_ALBUMS")

    url=tools.get_url("musicbrainz","artist_mbid",artist_mbid)
    xml=tools.get_xml(url)

    artist_name= xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
    logo=image.get_image(artist_mbid," ",'artist')     
    background=image.get_image(artist_mbid,"artist_name",'bg')
    
    artist=Artists(artist_name=artist_name, artist_mbid=artist_mbid,disambiguation=" ",letter=artist_name[0], key=ndb.Key('Artists',artist_mbid))
    artist.logo=logo
    artist.background=background
    artist_key=artist.put()  

    logging.error(artist)

    releases=xml.getElementsByTagName("release-group")

    albums=[]
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

                    b=Albums(key=ndb.Key(Albums,album_mbid,parent=ndb.Key(Artist,artist_mbid)))

                    b.album_mbid=album_mbid
                    b.album_name=rg.getElementsByTagName("title")[0].childNodes[0].nodeValue
                    b.album_date=rg.getElementsByTagName("first-release-date")[0].childNodes[0].nodeValue
                    b.album_image=image.get_image(album_mbid,b.album_name,key="album")
                    
                    albums.append(b)
                    logging.error(b)
            except:
                continue
    
    albums.sort(key=lambda tup: tup.album_date)

    test=ndb.put_multi(albums)

    logging.error("END OF Artist_ALBUMS")

    return artist,albums


def get_ndbArtist(artist):

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
    
    data=list(ndb.gql(query))
    memcache.set(query,data)
    if data != []:
        logging.error("mbid from ndb get_ndbArtist")
    return data
    
def get_artist_name(mbid):
    query="select artist from Artist where mbid='%s'"%mbid
    logging.error(query)
    track=list(ndb.gql(query))

    data=track[0]
    
    return data

def  get_similar(mbid=""):
    
    data=memcache.get("similar_%s"%mbid)
    
    if data is not None:
        return data

    
    logging.error("GETTING SIMILAR FROM ECHONEST")
    url=tools.get_url('echonest','similar',mbid)
    j=tools.get_json(url)
    
    if j is None:
        return []
    
    similar=[]
    try:
        a=j['response']['artists']
    except:
        return []
    for i in j['response']['artists']:
        name=i['name']
        if 'foreign_ids' in i.keys():
            s_mbid=i['foreign_ids'][0]['foreign_id'][19:]
        
            similar.append([name,s_mbid])
        
    logging.error("END OF ECHONEST CODE")
    memcache.set("similar_%s"%mbid,similar)   
    return similar

def get_data(artist,d=False, I=False):
    
    logging.error("getting data of %s"%artist)
    data=get_ndbArtist(artist)
    if data != []:
        logging.error("mbid from ndb or memcache get_data")
        return data
    
    url=tools.get_url('musicbrainz','artist',artist)
    xml=tools.get_xml(url)
    parsed=xml.getElementsByTagName("artist")
    
    disambiguation=" "
    mbid=[]

    if xml.getElementsByTagName("artist-list")[0].attributes.get("count").value == '1' :
        
        mbidId=parsed[0].attributes.get("id").value
        url="http://musicbrainz.org/ws/2/artist/"+mbidId+"?inc=releases"

        
        x=tools.get_xml(url)  
        name=xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
        disambiguation=" "
        ar=Artist(artist=name, mbid=mbidId, disambiguation=disambiguation, letter=name[0])
        
        mbid.append(ar)
        memcache.set("select * from Artist where artist='%s'"%name,[ar])

    else:
        
        for a in parsed:
        
            mbidId=a.attributes.get("id").value
            name=a.getElementsByTagName("name")[0].childNodes[0].nodeValue

            try:
                disambiguation=a.getElementsByTagName("disambiguation")[0].childNodes[0].nodeValue
                if d==False:
                    continue
            except:
                disambiguation=" "
            
            ar=Artist(artist=name, mbid=mbidId, disambiguation=disambiguation, letter=name[0])
            mbid.append(ar)
            memcache.set("select * from Artist where artist='%s'"%name,[ar])
    logging.error(mbid)

    return mbid

def get_artist_mb(mbid):
    data=memcache.get("%s artist="%mbid)
    if data is not None:
        return data
    try:
        data=list(ndb.gql("select artist from Artist where mbid='%s'"%mbid))
        if data != []:
            memcache.set("%s artist="%mbid, data[0].artist)
            return data[0].artist
    except:
        pass

    url="http://www.musicbrainz.org/ws/2/artist/?query=arid:"+mbid
    xml=tools.get_xml(url)

    if xml.getElementsByTagName("artist-list")[0].attributes.get("count").value == '1':
        name= xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
        memcache.set("%s artist="%mbid, name)
        a=Artist(artist=name, mbid=mbid,disambiguation=" ",letter=name[0])
        
        try:
            a.put()

            logging.error("Artist inserted in ndb")
        except:
            pass
        return name