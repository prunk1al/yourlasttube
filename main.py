import urllib2
import os
import webapp2
import jinja2
import logging
import json
from xml.dom import minidom
import os, re, base64


from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api.labs import taskqueue
from google.appengine.api import files
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import urlfetch
from io import BytesIO
from google.appengine.api import users, images, files

import Class

from echonest import Dynamic
from artist import Artist
from playlists import Playlist
from track import Track
import album
import image
import tools
import string
import playlists

from CorrectArtist import CorrectArtist

jinja_env = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a,**kw)

    def render_str(self,template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)
    
    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))



class xhrGetVideo(Handler):

    def post(self):
    
        j=self.request.body
        data=json.loads(j)
        video=None
        logging.error(data)
        video=memcache.get("video of %s %s"%(data["name"],data["artist"]["name"]))
        trackKey=ndb.Key('Track',data["name"].replace("-", "")+ " - " +data["artist"]["name"] )
        track=trackKey.get()
        if track is None:
            track=Track(key=trackKey)
            track.getVideo()

        video={}
        video["ytid"]=track.ytid
        video["img"]="http://img.youtube.com/vi/"+video["ytid"]+"/0.jpg"

  
        memcache.set("video of %s %s"%(data["name"],data["artist"]["name"]), video)
        
        self.response.out.write(json.dumps(video)) 



class xhrArtistData(Handler):
     def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data["artist"]
        data=None
        key=ndb.Key("Artist",mbid)
        a=key.get()
        if a is None:
            a=Artist(key=key)

        data={"name":a.getName(),
                "info":a.getInfo(),
                "tags":a.getTags()             
        }
        
        self.response.out.write(json.dumps(data))

class xhrLogo(Handler):
    
    def post(self):
        logging.error("INIT LOGO")
        j=self.request.body
        data=json.loads(j)
        mbid=data["artist"]
        logo=None
        #logo=memcache.get("v3 logo of %s"%mbid)
        if logo is None:
            logging.error("LOGO NOT IN MEMCACHE")
            artist=ndb.Key("Artist",mbid)
            logging.error(artist)
            logo=getlogo(artist)
            
            memcache.set("v3 logo of %s"%mbid, logo)
        logging.error(logo)
        self.response.out.write(json.dumps(logo))
@ndb.transactional(xg=True) 
def getlogo(key):
    artist=key.get()
    if artist is None:
        artist=Artist(key=key)
    try:
        logo=images.get_serving_url(artist.getLogo())
    except Exception as e:
        logging.error(e)
        return ""
    return logo


class xhrSimilar(Handler):
    
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data["artist"]
        similars=None
        #similars=memcache.get("v3 similars of %s"%mbid)
        if similars is None:

            artist=ndb.Key("Artist",mbid)
            similars=getSimilar(artist)
            logging.error(similars)
            memcache.set("v3 similars of %s"%mbid, similars)
        self.response.out.write(json.dumps(similars))
@ndb.transactional(xg=True) 
def getSimilar(key):
    artist=key.get()
    if artist is None:
        artist=Artist(key=key)
        return artist.getSimilars()
  
    else:
        similars=[]
        for a in artist.similars:
            print a.getName()

class getTopArtist(Handler):
    def get(self):
        artists=memcache.get("lastfm topArtists")
        if artists is None:
            url=tools.get_url("lastfm","topArtists"," ")
            j=tools.get_json(url)
            artists=[]
            for a in j["artists"]["artist"]:
                artist={}
                artist["name"]=a["name"]
                artist["mbid"]=a["mbid"]
                artists.append(artist)
            memcache.set("lastfm topArtists",artists)
        self.response.out.write(json.dumps(artists))

class getTopTags(Handler):
    def get(self):
        tags=None
        tags=memcache.get("lastfm topTags")
        if tags is None:
            url=tools.get_url("lastfm","topTags"," ")
            j=tools.get_json(url)
            tags=[]
            for t in j["tags"]["tag"]:
                if t["name"]!="seen live":
                    tag={}
                    tag["name"]=t["name"]
                    tags.append(tag)
            memcache.set("lastfm topTags",tags)
        self.response.out.write(json.dumps(tags))


class xhrCreateTagPlayList(Handler):
    def post(self):
        logging.error("xhrCreateTagPlayList")
        j=self.request.body
        data=json.loads(j)
        genre=data["data"]
        
        tracks=None
        #tracks=memcache.get("create %s playlist"%genre)
        
        if tracks is None:

            playlist=Playlist()
            playlist.tipo="tag"
            playlist.param=genre
            
            response=playlist.create()
            logging.error(response)
            if response =='Genre not in Echonest':
               tracks=response
            else:
                tracks={"tracks":playlist.getTracks(),"session":playlist.session}
  
        self.response.out.write(json.dumps(tracks))

class xhrArtistRadio(Handler):
    def post(self):
        logging.error("xhrCreateTagPlayList")
        j=self.request.body
        data=json.loads(j)
        genre=data["data"]
        
        tracks=None
  
        
        if tracks is None:

            playlist=Playlist()
            playlist.tipo="artist-radio"
            playlist.param=genre

            playlist.create()
            tracks={"tracks":playlist.getTracks(),"session":playlist.session}
  
          
           
        self.response.out.write(json.dumps(tracks))



class xhrCreateArtistPlayList(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        genre=data["data"]
        tracks=None
        tracks=memcache.get("create %s playlist"%genre)
        
        if tracks is None:

            playlist=Playlist()
            playlist.tipo="artist"
            playlist.param=data["data"]

            playlist.create()
            tracks={"tracks":playlist.getTracks(),"session":playlist.session}

        

            memcache.set("create %s playlist"%genre,tracks)
        self.response.out.write(json.dumps( tracks))



class xhrFrontVideos(Handler):
   

    def get(self):
      
        tracks=memcache.get("front Videos playlists")
        if tracks is None:
            
            playlist=Playlist()
            playlist.tipo="predefined"
            
            playlist.create()
            tracks=playlist.getTracks()

            memcache.set("front Videos playlists",tracks)
        self.response.out.write(json.dumps(tracks))


class xhrGetNextPl(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        logging.error(data)
 
        if "session" in data:
            echo=Dynamic()
            echo.session=data["session"]
            echo.getNext()
            track=echo.tracks.pop()
            logging.error(track)
            self.response.out.write(json.dumps({"tracks":[track]}))
        else:
            
            pass


        

class SearchArtist(Handler):
    def post(self):
        import artist
        j=self.request.body
        data=json.loads(j)
        artist_name=data["name"]
        logging.error(artist_name)
        artists=artist.search_artist(artist_name)

       
        self.response.out.write(json.dumps(artists))




class xhrFront(Handler):
    def renderFront(self, artists=None, genres=None ,playlist=None, disambiguation=None, artist=None):
        self.render("front2.html",artists=artists, genres=genres,playlist=playlist,disambiguation=disambiguation, artist=artist)


    def get(self):

        self.renderFront(artists=memcache.get("lastfm topArtists"), genres=memcache.get("lastfm topTags"), playlist={"tipo":"predefined","data":{"name":"top"}})

    def post(self):
        artist_name=self.request.get('artist')
        artists=artist.search_artist(artist_name)
        if len(artists)==1:
            self.redirect("/artist/%s"%artists[0]["mbid"])
        else:
            self.renderFront(disambiguation=artists)



class Artista(Handler):
    def renderFront(self, artists=None, genres=None ,playlist=None, disambiguation=None, artist=None):
        self.render("front2.html",artists=artists, genres=genres,playlist=playlist,disambiguation=disambiguation, artist=artist)

    def get(self,resource):

        self.renderFront(artists=memcache.get("lastfm topArtists"), genres=memcache.get("lastfm topTags"))

    def post(self,resource):
        artist_name=self.request.get('artist')
  
        artists=artist.search_artist(artist_name)
        if len(artists)==1:
            self.redirect("/artist/%s"%artists[0]["mbid"])
        else:
            self.renderFront(disambiguation=artists)


class Taga(Handler):
    def renderFront(self, artists=None, genres=None ,playlist=None, disambiguation=None, artist=None):
        self.render("front2.html",artists=artists, genres=genres,playlist=playlist,disambiguation=disambiguation, artist=artist)

    def get(self,resource):
        import urllib

        tag=str(urllib.unquote(resource))

        self.renderFront(artists=memcache.get("lastfm topArtists"), genres=memcache.get("lastfm topTags"), playlist={"tipo":"tag","data":{"name":tag}})

    def post(self,resource):
        artist_name=self.request.get('artist')
        artists=artist.search_artist(artist_name)
        if len(artists)==1:
            self.redirect("/tag/%s"%artists[0]["mbid"])
        else:
            self.renderFront(disambiguation=artists)

class ArtistRadio(Handler):
    def renderFront(self, artists=None, genres=None ,playlist=None, disambiguation=None, artist=None):
        self.render("front2.html",artists=artists, genres=genres,playlist=playlist,disambiguation=disambiguation, artist=artist)

    def get(self,resource):
        import urllib

        mbid=str(urllib.unquote(resource))
        key=ndb.Key("Artist",mbid)
        artist=key.get()
        if artist is None:
            artist=Artist(key=key)

        name=artist.getName()


        self.renderFront(artists=memcache.get("lastfm topArtists"), genres=memcache.get("lastfm topTags"), playlist={"tipo":"artist-radio","data":{"mbid":mbid, "name":name}})

    def post(self,resource):
        artist_name=self.request.get('artist')
  
        artists=artist.search_artist(artist_name)
        if len(artists)==1:
            self.redirect("/artist/%s"%artists[0]["mbid"])
        else:
            self.renderFront(disambiguation=artists)

     


class BlobstoreUpload(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    upload_files = self.get_uploads('file')
    blob_info = upload_files[0]
    return self.response.write(blob_info.key())

  @classmethod
  def encode_multipart_formdata(cls, fields, files, mimetype='image/png'):
    """
    Args:
      fields: A sequence of (name, value) elements for regular form fields.
      files: A sequence of (name, filename, value) elements for data to be
        uploaded as files.

    Returns:
      A sequence of (content_type, body) ready for urlfetch.
    """
    boundary = 'paLp12Buasdasd40tcxAp97curasdaSt40bqweastfarcUNIQUE_STRING'
    crlf = '\r\n'
    line = []
    for (key, value) in fields:
      line.append('--' + boundary)
      line.append('Content-Disposition: form-data; name="%s"' % key)
      line.append('')
      line.append(value)
    for (key, filename, value) in files:
      line.append('--' + boundary)
      line.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
      line.append('Content-Type: %s' % mimetype)
      line.append('')
      line.append(value)
    line.append('--%s--' % boundary)
    line.append('')
    
    #body = crlf.join(line)
    s = BytesIO()
    for element in line:
        s.write(str(element))
        s.write(crlf)
    body = s.getvalue()
    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body



class Sitemap(Handler):
    def render_site(self, artists=""):

        self.render("sitemap.xml", artists=artists)

    def get(self):
        
        query= Artist.query()

        artists=[artist.id() for artist in query.iter(keys_only=True)]
     
        self.render_site(artists=artists)
            

class login(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        logging.error(data)
 
       

app = webapp2.WSGIApplication([('/', xhrFront),
                               ('/sitemaps.xml',Sitemap),
                               ('/xhrFront', xhrFront),
                               ('/xhrLogo',xhrLogo),('/xhrSimilar', xhrSimilar),('/xhrFrontVideos', xhrFrontVideos),('/xhrGetVideo',xhrGetVideo),
                               ('/xhrArtistData',xhrArtistData),
                               ('/xhrCreateTagPlayList',xhrCreateTagPlayList),('/xhrCreateArtistRadio',xhrArtistRadio),
                               ('/xhrGetNextPl',xhrGetNextPl),('/xhrCreateArtistPlayList',xhrCreateArtistPlayList),
                               ('/artist/([^/]+)?', Artista),('/tag/([^/]+)?', Taga),('/artist-radio/([^/]+)?',ArtistRadio),
                               ('/predefined',xhrFront),
                               ('/getTopArtist',getTopArtist),('/getTopTags',getTopTags),
                               ('/searchArtist',SearchArtist),

                               ('/uploadblob',BlobstoreUpload)

                               ], debug=True)


import User