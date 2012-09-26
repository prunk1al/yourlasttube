import logging 
from google.appengine.api import memcache
from google.appengine.ext import db

def get_albums_mb(mbid):

    url=get_url('musicbrainz','album',mbid)
    xml=get_xml(url)

    parsed=xml.getElementsByTagName("release-group")

    albums=[]
    for rg in parsed:
        mbid=rg.attributes.get("id").value
        album=[mbid,rg.getElementsByTagName("title")[0].childNodes[0].nodeValue]

        try:
            a=rg.getElementsByTagName("secondary-type")[0]
            continue
        except:
            pass

        album.append(get_image(mbid," ",'album'))
        albums.append(album)

    return(albums)

def get_album_mb(mbid):
    url="http://www.musicbrainz.org/ws/2/release-group/"+mbid+"?inc=artists"
    logging.error(url)
    xml=get_xml(url)
    logging.error("get_album_mb")
    album=xml.getElementsByTagName("title")[0].childNodes[0].nodeValue
    artist=xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
    mbid=xml.getElementsByTagName("artist")[0].attributes.get("id").value
    return album,(artist,mbid)
