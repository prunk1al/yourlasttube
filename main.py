
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





class xhrLogo(Handler):
    
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data["artist"]
        logo=None
        #logo=memcache.get("v3 logo of %s"%mbid)
        if logo is None:
            
            artist=ndb.Key("Artist",mbid)
            logging.error(artist)
            logo=getlogo(artist)
            
            memcache.set("v3 logo of %s"%mbid, logo)
        
        self.response.out.write(logo)    
@ndb.transactional(xg=True) 
def getlogo(key):
    artist=key.get()
    if artist is None:
        artist=Artist(key=key)
    try:
        logo=images.get_serving_url(artist.getLogo())
    except:
        return ""
    return logo


class xhrSimilar(Handler):
    
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data[10:-1]
        similars=None
        #similars=memcache.get("v3 similars of %s"%mbid)
        if similars is None:

            artist=ndb.Key("Artist",mbid)
            similars=getSimilar(artist)
            memcache.set("v3 similars of %s"%mbid, similars)
        self.response.out.write(json.dumps(similars))
@ndb.transactional(xg=True) 
def getSimilar(key):
    artist=key.get()
    if artist is None:
        artist=Artist(key=key)
    similars=[]
    for s in artist.getSimilars():
        similar=sjson(s)
        similars.append(similar)
    return similars
@ndb.non_transactional(allow_existing=True)    
def sjson(s):
    sim=s.get()
    if sim is None:
        sim=Artist(key=s)
    similar={"name":sim.getName(),
             "logo":sim.getImage(),
             "mbid":sim.key.id()
            }
    return similar    


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


class xhrTagPlayList(Handler):
    def post(self):
        # This is the main function for profiling
        # We've renamed our original main() above to real_main()
        import cProfile, pstats
        prof = cProfile.Profile()
        prof = prof.runctx("self.real_post()", globals(), locals())
        print "<pre>"
        stats = pstats.Stats(prof)
        stats.sort_stats("cumulative")  # Or cumulative
        stats.print_stats(80)  # 80 = how many to print
        # The rest is optional.
        # stats.print_callees()
        # stats.print_callers()
        print "</pre>"

    def real_post(self):
        import time
        time_star=time.time()

        j=self.request.body
        data=json.loads(j)
        genre=data["data"]
        tracks=None
        tracks=memcache.get("%s Videos playlist"%genre)
        if tracks is None:

            playlist=Playlist()
            playlist.tipo="artist"
            playlist.param=data["data"]

            playlist.create()
            tracks=playlist.getTracks()
            memcache.set("%s Videos playlist"%genre, tracks)
        logging.error("total time of playlist= %s"%(time.time()-time.start()))
        self.response.out.write(json.dumps(tracks))


class xhrArtistPlayList(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        genre=data["data"]
        tracks=None
        tracks=memcache.get("%s Videos playlist"%genre)

        if tracks is None:
            playlist=Playlist()
            playlist.tipo="artist"
            playlist.param=data["data"]

            playlist.create()
            tracks=playlist.getTracks()

         
            memcache.set("%s Videos playlist"%genre, tracks)
        
        self.response.out.write(json.dumps(tracks))



class Artista(Handler):
    def renderFront(self, artists=None, genres=None ,playlist=None, disambiguation=None, artist=None):
        self.render("front2.html",artists=artists, genres=genres,playlist=playlist,disambiguation=disambiguation, artist=artist)

    def get(self,resource):
        import urllib

        mbid=str(urllib.unquote(resource))
        key=ndb.Key("Artist",mbid)
        artist=key.get()
        logging.error(artist)
        if artist is None:
            artist=Artist(key=key)
            name=artist.getName()
            self.renderFront(artists=memcache.get("lastfm topArtists"), genres=memcache.get("lastfm topTags"), playlist={"tipo":"artist","data":{"mbid":mbid, "name":name}})


        else:
            artista=artist.toJson()
            logging.error(artista)
            name=artist.name

            self.renderFront(artists=memcache.get("lastfm topArtists"), genres=memcache.get("lastfm topTags"), playlist={"tipo":"artist","data":{"mbid":mbid, "name":name}}, artist=artista)

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


class Correct(Handler):
   
    def get(self):
        self.render("correct.html")

    def post(self):
        name=self.request.get('name')
        wrong=self.request.get("wrong")
        right=self.request.get("right")
        c=CorrectArtist(name=name, mbid=right, key=ndb.Key('CorrectArtist',wrong))
        c.put()
        self.redirect("/correctArtist")

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
            #memcache.set("lastfm topArtists",artists)
        self.response.out.write(json.dumps(artists))

class getTopTags(Handler):
    def get(self):
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

            playlist.create()
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

     
class xhrGetNextPl(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        if "type" in data:
                if "session" in data:
                    echo=Dynamic()
                    echo.session=data["session"]
                    echo.getNext()
                    self.response.out.write(json.dumps({"tracks":[echo.tracks.pop()]}))
                else:
                    
                    pass


             


class xhrCreateArtistPlayList(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        genre=data["data"]
        tracks=None
        #tracks=memcache.get("create %s playlist"%genre)
        
        if tracks is None:

            playlist=Playlist()
            playlist.tipo="artist"
            playlist.param=data["data"]

            playlist.create()
            tracks={"tracks":playlist.getTracks(),"session":playlist.session}

        

            memcache.set("create %s playlist"%genre,tracks)
        self.response.out.write(json.dumps( tracks))



class SearchArtist(Handler):
    def post(self):
        import artist
        j=self.request.body
        data=json.loads(j)
        artist_name=data["name"]
        logging.error(artist_name)
        artists=artist.search_artist(artist_name)

       
        self.response.out.write(json.dumps(artists))
        

class Buy7digital(Handler):
    def post(self):
    
        j=self.request.body
        track=json.loads(j)
        id=memcache.get("7digital of %s"%track)
        if id is None:
            url=tools.get_url("7digital", "buytrack", track)
            logging.error(url)
            xml=tools.get_xml(url)

            tracka=xml.getElementsByTagName("track")

            id=tracka[0].attributes.get("id").value

            memcache.set("7digital of %s"%track,id)

        self.response.out.write(json.dumps(id))

class BuyAmazon(Handler):
    def post(self):
        if True:
            asin=None
            j=self.request.body
            track=json.loads(j)
            import bottlenose
            amazon = bottlenose.Amazon("AKIAJBTO4RI6WUVCVFEA", "TGfzGuc+/U+t2jwNZSSIZrOrVlm8yDNZz0tij81+", "yolatu-21")
            response = amazon.ItemSearch(Keywords=track["name"]+' '+track["artist"]["name"], SearchIndex="MP3Downloads")
            logging.error("AMAZON")
            from xml.dom import minidom
            xml=minidom.parseString(response)
            #logging.error(xml.toprettyxml())
            items=xml.getElementsByTagName("Item")
            for x in items:
                if x.getElementsByTagName("Title")[0].childNodes[0].nodeValue==track["name"] and x.getElementsByTagName("Creator")[0].childNodes[0].nodeValue==track["artist"]["name"]:
                    asin=x.getElementsByTagName("ASIN")[0].childNodes[0].nodeValue
                    break;
                    

        self.response.out.write(json.dumps(asin))   

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
            



app = webapp2.WSGIApplication([('/', xhrFront),
                               ('/sitemaps.xml',Sitemap),
                               ('/xhrFront', xhrFront),
                               ('/xhrLogo',xhrLogo),('/xhrSimilar', xhrSimilar),('/xhrFrontVideos', xhrFrontVideos),('/xhrGetVideo',xhrGetVideo),
                               ('/xhrArtistData',xhrArtistData),
                               ('/xhrTagPlayList',xhrTagPlayList),('/xhrArtistPlayList',xhrArtistPlayList),('/xhrCreateTagPlayList',xhrCreateTagPlayList),('/xhrCreateArtistRadio',xhrArtistRadio),
                               ('/xhrGetNextPl',xhrGetNextPl),('/xhrCreateArtistPlayList',xhrCreateArtistPlayList),
                               ('/artist/([^/]+)?', Artista),('/tag/([^/]+)?', Taga),('/artist-radio/([^/]+)?',ArtistRadio),
                               ('/predefined',xhrFront),('/correctArtist',Correct),
                               ('/getTopArtist',getTopArtist),('/getTopTags',getTopTags),
                               ('/searchArtist',SearchArtist),
                               ('/Buy7digital',Buy7digital),('/BuyAmazon',BuyAmazon),
                               ('/uploadblob',BlobstoreUpload)

                               ], debug=True)
