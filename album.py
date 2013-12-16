import logging 
from google.appengine.api import memcache

import tools
import image
import Class
import async
from google.appengine.ext import ndb
import artist



def get_album_data(album_mbid):
    data=memcache.get("get_album_data: %s"%album_mbid)
    if data is not None:
        return data
    try:
        album=Class.Albums.query(Class.Albums.album_mbid==album_mbid).get()
    except:
        album =None
    if album is not None:
        return album
    else:
       return get_album_mb(album_mbid)



def get_albums_mb(mbid):
    
    url=tools.get_url('musicbrainz','album',mbid)
    xml=tools.get_xml(url)

    parsed=xml.getElementsByTagName("release-group")

    albums=[]
    for rg in parsed:
        mbid=rg.attributes.get("id").value
        

        try:
            a=rg.getElementsByTagName("secondary-type")[0]
            continue
        except:
            try:
                album=[mbid,rg.getElementsByTagName("title")[0].childNodes[0].nodeValue,rg.getElementsByTagName("first-release-date")[0].childNodes[0].nodeValue]
            except:
                continue

        album.append(image.get_image(mbid," ",'album'))
        albums.append(album)
    albums.sort(key=lambda tup: tup[2])
    for album in albums:
        logging.error(album)
    return(albums)

def get_album_mb(album_mbid):
    
    url="http://www.musicbrainz.org/ws/2/release-group/"+album_mbid+"?inc=artists"
    xml=tools.get_xml(url)
    logging.error("get_album_mb")

    album_name=xml.getElementsByTagName("title")[0].childNodes[0].nodeValue
    artist_mbid=xml.getElementsByTagName("artist")[0].attributes.get("id").value
    album_date=xml.getElementsByTagName("first-release-date")[0].childNodes[0].nodeValue
    album_image=None

    artist_data=Class.Artists.query().filter(Class.Artists.artist_mbid==artist_mbid).get()
    
    if artist_data is None:
        artist_data,album_data=artist.get_artist_albums(artist_mbid)
        
    
    album=Class.Albums(album_mbid=album_mbid,album_name=album_name,album_date=album_date,album_image=album_image,key=ndb.Key(Class.Albums,album_mbid,parent=ndb.Key(Class.Artists,artist_data.artist_mbid)))
        

    album_image_url=tools.get_url('fanart','album',album_mbid)
    albums=async.get_urls([album_image_url],"albums_image",[album])
    logging.error(albums)


    
    return album


