import urllib2
import json
import logging
import urllib
from xml.dom import minidom
from google.appengine.api import memcache
from google.appengine.api import files
from google.appengine.ext import blobstore


def get_url(server,service,param):

    LASTFM_API= '51293239750eea5095511e23b3107e31'
    YOUTUBE_API='AI39si42ldETBAU7tY22n0DCKTn1jBDj3Hx4_RwMjQvzW27yyQ_q4QjekBC7rfEd80rMArD6wZxmngyEK0IDb9rUrN28uW6Ybw'
    FARNART_API='32a11570b86e33ddd12310fb76d194ee'
    ECHONEST_API='EPOY20CBSSGYKV88Y'
    
    if server=='lastfm':
        API_KEY=LASTFM_API
        SERVER = 'ws.audioscrobbler.com/2.0'
        mbid=param
        if service=='similar':
            SERVICE = '/?method=artist.getsimilar&'
            params = "mbid="+mbid+"&api_key="+API_KEY+"&limit=10&format=json"
        if service=='genres':
            SERVICE='/?method=track.gettoptags&'
            params="mbid="+mbid+"&api_key="+API_KEY
        if service=='info':
            SERVICE='/?method=artist.getinfo&'
            params="mbid="+mbid+"&api_key="+API_KEY
        if service=='album':
            SERVICE='/?method=album.getinfo&'
            params="mbid="+mbid+"&api_key="+API_KEY+"&format=json"


    if server=='youtube':

        artist,song=param[0],param[1]
        API_KEY=YOUTUBE_API
        SERVER='gdata.youtube.com'
        SERVICE='/feeds/api/videos?q='
        params=artist+"+"+song+"+official+video&max-results=1&v=2&format=5&key="+API_KEY
        params=params.replace(" ","+")

    if server=='musicbrainz':
        SERVER = 'www.musicbrainz.org' 
        mbid=param

        if service=='artist':
            SERVICE = '/ws/2/artist/?'         
            x = 'alias:"'+mbid+'"OR artist:"'+mbid+'"'
            params=urllib.urlencode({"query":x}).replace("OR+","OR%20")

        if service=='album':
            SERVICE='/ws/2/release-group?'
            params="artist="+mbid+"&type=album"

        if service=='tracks':
            SERVICE='/ws/2/release?'
            params='release-group='+mbid+'&inc=recordings+artist-credits'

    if server=='fanart':
        
        SERVER='fanart.tv'
        API_KEY=FARNART_API
        mbid=param

        if service=='artist':
            SERVICE='/webservice/artist/'
            params=API_KEY+'/'+mbid+'/json/all/1/1/'

        if service=='album':
            SERVICE='/webservice/album/'
            params=API_KEY+'/'+mbid+'/xml/all/1/1/'

    if server=='echonest':
        SERVER='developer.echonest.com'
        API_KEY=ECHONEST_API
        mbid=param
        if service=="similar":
            SERVICE='/api/v4/artist/similar?'
            params='api_key='+API_KEY+'&id=musicbrainz:artist:'+mbid+"&format=json&results=5&start=0&bucket=id:musicbrainz"
        if service=="id":
            SERVICE='/api/v4/artist/search?'
            params='api_key='+API_KEY+'&id='+mbid+"&format=xml&bucket=musicbrainz"
    

    url ='http://%s%s%s' % (SERVER,SERVICE,params) 
    
    """logging.error(url)"""
    
    return url

def get_xml(url):

    xml=memcache.get(url)
    if xml is not None:
        return xml

    #time.sleep(1) 
    page=urllib2.urlopen(url)
    logging.error(url)
    xml=minidom.parseString(page.read())
    memcache.set(url,xml)

    return xml

def get_json(url):
    p=memcache.get(url)
    if p is  None:
        #time.sleep(1)
        page=urllib2.urlopen(url)
        logging.error(url)
        p=page.read()
        memcache.set(url,p)
    j=json.loads(p)
    return j

def write_blob(content, filename):
    # Open the file and write to it
    with files.open(filename, 'a') as f:
        f.write(content)

    # Finalize the file. Do this before attempting to read it.
    files.finalize(filename)

    # Get the file's blob key
    blob_key = files.blobstore.get_blob_key(filename)