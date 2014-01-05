import urllib2
import json
import logging
import urllib
from xml.dom import minidom
from google.appengine.api import memcache
from google.appengine.api import files
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
#import track
import time



def get_url(server,service,param):

   
    
    if server=='lastfm':
        API_KEY=LASTFM_API
        SERVER = 'ws.audioscrobbler.com/2.0'
        mbid=param
        if service=='similar':
            SERVICE = '/?method=artist.getsimilar&'
            params = "mbid="+mbid+"&api_key="+API_KEY+"&limit=4&format=json"
        elif service=='genres':
            SERVICE='/?method=track.gettoptags&'
            params="mbid="+mbid+"&api_key="+API_KEY
        elif service=='artistInfo':
            SERVICE='/?method=artist.getinfo&'
            params="mbid="+mbid+"&api_key="+API_KEY+"&format=json"
        elif service=='album':
            SERVICE='/?method=album.getinfo&'
            params="mbid="+mbid+"&api_key="+API_KEY+"&format=json"
        elif service=='hyppedtracks':
            SERVICE='?method=chart.gethypedtracks&'
            params="api_key="+API_KEY+"&format=json&limit=50"
        elif service=='lovedtracks':
            SERVICE='?method=chart.getlovedtracks&'
            params="api_key="+API_KEY+"&format=json&limit=50"
        elif service=='toptracks':
            SERVICE='?method=chart.gettoptracks&'
            params="api_key="+API_KEY+"&format=json&limit=20"
        elif service=='toptags':
            SERVICE='?method=chart.gettoptags&'
            params="api_key="+API_KEY+"&format=json&limit=50"
        elif service=='toptagtracks':
            SERVICE='?method=tag.gettoptracks&'
            params="tag="+param+"&api_key="+API_KEY+"&format=json&limit=20"
            params=params.replace(" ","+")
        elif service=="artisttoptracks":
            SERVICE='/?method=artist.gettoptracks&'
            params='mbid='+param+'&api_key='+API_KEY+'&format=json&limit=20"'
        elif service=="artistTags":
            SERVICE='/?method=artist.gettoptags&'
            params='mbid='+param+'&api_key='+API_KEY+'&format=json'
        elif service=="topArtists":
            SERVICE='/?method=chart.gettopartists&'
            params='api_key='+API_KEY+'&format=json&limit=5'
        elif service=="topTags":
            SERVICE='/?method=chart.gettoptags&'
            params='api_key='+API_KEY+'&format=json&limit=5'
        elif service=='genreCreate':
            SERVICE='?method=tag.gettoptracks&'
            params="tag="+param+"&api_key="+API_KEY+"&format=json&limit=6"
            params=params.replace(" ","+")
        elif service=='genreNext':
            SERVICE='?method=tag.gettoptracks&'
            params="tag="+param["tag"]+"&api_key="+API_KEY+"&format=json&limit=1&page="+str(param["page"])
            params=params.replace(" ","+")
        elif service=='artistCreate':
            SERVICE='?method=artist.gettoptracks&'
            params="mbid="+param+"&api_key="+API_KEY+"&format=json&limit=6"
            params=params.replace(" ","+")
        elif service=='artistNext':
            SERVICE='?method=artist.gettoptracks&'
            params="mbid="+param["artist"]+"&api_key="+API_KEY+"&format=json&limit=1&page="+str(param["page"])
            params=params.replace(" ","+")   

    elif server=='youtube':
        artist,song=param[0],param[1]
        API_KEY=YOUTUBE_API
        SERVER='gdata.youtube.com'
        SERVICE='/feeds/api/videos?q='
<<<<<<< HEAD
        params=artist+'+'+song+'&max-results=1&v=2&format=5&alt=json&hd=true&key='+API_KEY
=======
        params='"'+song+'+'+artist+'"&max-results=1&v=2&format=5&alt=json&orderby=viewCount&key='+API_KEY
>>>>>>> 7f24c7117ba6990f0b791a96320c7096fcf225f6
        params=params.replace(" ","+")


    elif server=='musicbrainz':
        SERVER = 'www.musicbrainz.org' 
        mbid=param
        if service=='artist':
            SERVICE = '/ws/2/artist/?'         
            x = 'alias:"'+mbid+'"OR artist:"'+mbid+'"'
            params=urllib.urlencode({"query":x.encode('utf8')}).replace("OR+","OR%20")
        elif service=="artist_mbid":
            SERVICE="/ws/2/artist/"
            params=mbid+"?inc=release-groups"
        elif service=='album':
            SERVICE='/ws/2/release-group?'
            params="artist="+mbid+"&type=album"
        elif service=='tracks':
            SERVICE='/ws/2/release?'
            params='release-group='+mbid+'&inc=recordings+artist-credits'
        elif service=='tracksj':
            SERVICE='/ws/2/release?'
            params='release-group='+mbid+'&inc=recordings+artist-credits&fmt=json'
        elif service=='recording':
            SERVICE='/ws/2/recording/'
            params=mbid+'?inc=artists&fmt=json'

    elif server=='fanart':
        
        SERVER='fanart.tv'
        API_KEY=FARNART_API
        mbid=param
        if service=='artist':
            SERVICE='/webservice/artist/'
            params=API_KEY+'/'+mbid+'/json/all/1/1/'
        if service=='album':
            SERVICE='/webservice/album/'
            params=API_KEY+'/'+mbid+'/xml/all/1/1/'


    elif server=='echonest':
        SERVER='developer.echonest.com'
        API_KEY=ECHONEST_API
        mbid=param
        if service=="similar":
            SERVICE='/api/v4/artist/similar?'
            params='api_key='+API_KEY+'&id=musicbrainz:artist:'+mbid+"&format=json&results=5&start=0&bucket=id:musicbrainz"
        if service=="id":
            SERVICE='/api/v4/artist/search?'
            params='api_key='+API_KEY+'&id='+mbid+"&format=xml&bucket=musicbrainz"
        if service=="genre":
            SERVICE='/api/v4/song/search?'
            params='api_key='+API_KEY+'&format=json&results=1&artist='+mbid[0]+'&title='+mbid[1]+'&bucket=song_hotttnesss'
        if service=="playlist":
            SERVICE='/api/v4/playlist/static?'
            params='api_key='+API_KEY+'&format=json&results=50&artist_id=musicbrainz:artist:'+mbid+'&type=artist-radio&adventurousness=0.8&dmca=true'
        if service=="tags":
            SERVICE='/api/v4/artist/list_terms?'
            params='api_key='+API_KEY+'&format=json&type=style'
        if service=="genre":
            SERVICE='/api/v4/playlist/static?'
            params='api_key='+API_KEY+'&format=json&results=50&genre='+mbid.lower()+'&distribution=focused&target_artist_hotttnesss=0.8&target_song_hotttnesss=0.8&type=genre-radio&bucket=id:musicbrainz&limited_interactivity=true&artist_pick=artist_hotttnesss-desc'
        if service=="artist":
            SERVICE='/api/v4/playlist/static?'
            params='api_key='+API_KEY+'&format=json&results=50&artist_id=musicbrainz:artist:'+mbid+'&type=artist&bucket=id:musicbrainz'
        if service=="genreCreate":
            SERVICE='/api/v4/playlist/dynamic/create?'
            params='api_key='+API_KEY+'&format=json&genre='+mbid.lower()+'&distribution=focused&target_artist_hotttnesss=0.8&target_song_hotttnesss=0.8&type=genre-radio&bucket=id:musicbrainz&limited_interactivity=true&artist_pick=artist_hotttnesss-desc'
        if service=="genreNext5":
            SERVICE='/api/v4/playlist/dynamic/next?'
            params='api_key='+API_KEY+'&format=json&session_id='+mbid+'&results=5'
        if service=="genreNext":
            SERVICE='/api/v4/playlist/dynamic/next?'
            params='api_key='+API_KEY+'&format=json&session_id='+mbid+'&results=1'
        if service=="get7digital":
            SERVICE='/api/v4/song/search'
            params='api_key='+API_KEY+'&format=json&results=1&artist='+mbid["artist"]["name"]+'&title='+mbid["name"]+'&bucket=id:7digital-US&bucket=tracks'

    elif server=="7digital":
        SERVER='api.7digital.com'
        API_KEY=DIGITAL_API

        if service=="buytrack":
            SERVICE='/1.2/track/search?'
            params='q=%s %s&oauth_consumer_key=%s&pagesize=1'%(param["name"],param["artist"]["name"],API_KEY)
            params=params.replace(" ","%20")



    url ='http://%s%s%s' % (SERVER,SERVICE,params) 
    

    
    return url

def get_xml(url):
    
    xml=memcache.get(url)
    if xml is not None:
        return xml

    #time.sleep(1) 
    logging.error(url)
    try:
        page=urlfetch.fetch(url,deadline=10)
    
        xml=minidom.parseString(page.content)
    
        
    except:
        return None
    try:
        memcache.set(url,xml)
    except:
        pass
    return xml

def get_json(url):
    p=memcache.get(url)
    if p is  None:
        #time.sleep(1)
        logging.error(url)
        try:
            result = urlfetch.fetch(url)
            
            page=urllib2.urlopen(url)
            p=page.read()
            memcache.set(url,p)
        except:
            return None

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

def clean_genres():
    genres=[]
    genre=list(ndb.gql("select * from Genres"))
    for i in genre:
        if len(i.track_mbid)<=1:
            genres.append(i.key())
            logging.error(i.genre)

    ndb.delete_async(genres)
def delete(key):
    ndb.delete(key)

def check_tracks():
    tracks=list(ndb.gql("select track_mbid from Tracks order by track_mbid limit 200"))
    dupe=''
    for i in tracks:
        if i.track_mbid==dupe:
            logging.error("Drop tracks")
            logging.error(dupe)
            taskqueue.add(url='/worker', params={'f':'tools.delete("%s")'%i.key()})
                    
        dupe=i.track_mbid
