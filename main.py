
import urllib2
import os
import webapp2
import jinja2
import logging
import json
from xml.dom import minidom

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api.labs import taskqueue
from google.appengine.api import files
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import urlfetch

import Class
import artist
import album
import track
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
        mbid=data[10:-1]

        logo=memcache.get("logo of %s"%mbid)
        if logo is None:
            logo=image.get_image(mbid,"logo")
            memcache.set("logo of %s"%mbid, logo)


        self.response.out.write(logo)    


class xhrGetArtistInfo(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data["artist"]
        logging.error(mbid)
        info=memcache.get("info of %s"%mbid)
        if info is None:
            info=artist.getArtistInfo(mbid)
            memcache.set("info of %s"%mbid,info)
        self.response.out.write(info)


class xhrSimilar(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data[10:-1]
        similar=None
        similar=memcache.get("similars of %s"%mbid)
        if similar is None:
            similar=artist.get_xhrsimilar(mbid)
            for x in similar:
                logging.error(similar)
            memcache.set("similars of %s"%mbid, similar)
        self.response.out.write(json.dumps(similar))


class xhrGetArtistTags(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data["artist"]
        tags=memcache.get("tags of %s"%mbid)
        if tags is None:
            tags={"tags":artist.getArtistTags(mbid)}
            memcache.set("tags of %s"%mbid,tags)

        self.response.out.write(json.dumps(tags))


class xhrGetVideo(Handler):

    def post(self):
    
        j=self.request.body
        data=json.loads(j)
        video=None
        video=memcache.get("video of %s %s"%(data["name"],data["artist"]["name"]))
        if video is None:
            video={}
            video["ytid"]=track.get_video(data["artist"]["name"],data["name"])
            video["img"]="http://img.youtube.com/vi/"+video["ytid"]+"/0.jpg"
  
            memcache.set("video of %s %s"%(data["name"],data["artist"]["name"]), video)
        
        self.response.out.write(json.dumps(video)) 


class xhrFrontVideos(Handler):

    def get(self):
        
        tracks=memcache.get("front Videos playlists")
        if tracks is None:
    
            data=playlists.getTopTracks()

            tracks=[]
            i=1
            for d in data["tracks"]["track"]:
                logging.error(d)
                track={}
                track["artist"]={}
                track["artist"]["name"]=d["artist"]["name"]

                cmbid=CorrectArtist.by_id(d["artist"]["mbid"])
                if cmbid is not None:
                    track["artist"]["mbid"]=cmbid.mbid
                else:
                    track["artist"]["mbid"]=d["artist"]["mbid"]
                
                track["name"]=d["name"]
                track["number"]=i
                if tracks not in tracks:
                    tracks.append(track)
                    i+=1
            memcache.set("front Videos playlist", tracks)

        self.response.out.write(json.dumps(tracks))


class xhrTagPlayList(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        genre=data["data"]
        tracks=None
        tracks=memcache.get("%s Videos playlist"%genre)
        if tracks is None:
            data=playlists.getEchoTagTracks(genre)
            tracks=[]
            i=1
            for d in data:
                logging.error(d)
                if "artist_foreign_ids" in d:
                    track={}
                    track["artist"]={}
                    track["artist"]["name"]=d["artist_name"]
                    mbid=d["artist_foreign_ids"][0]['foreign_id'][19:]
                    cmbid=CorrectArtist.by_id(mbid)
                    if cmbid is not None:
                        track["artist"]["mbid"]=cmbid.mbid
                    else:
                        track["artist"]["mbid"]=mbid
                    track["name"]=d["title"]
                    track["number"]=i
                    if tracks not in tracks:
                        tracks.append(track)
                        i+=1
            memcache.set("%s Videos playlist"%genre, tracks)
        self.response.out.write(json.dumps(tracks))


class xhrArtistPlayList(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        genre=data["data"]
        tracks=None
        tracks=memcache.get("%s Videos playlist"%genre)

        if tracks is None:

            data=playlists.getArtistTracks(genre)

            tracks=[]
            i=1
   
            for d in data["toptracks"]["track"]:
                logging.error(d)
        
                track={}
                track["artist"]={}
                track["artist"]["name"]=d["artist"]["name"]

                cmbid=CorrectArtist.by_id(d["artist"]["mbid"])
                if cmbid is not None:
                    track["artist"]["mbid"]=cmbid.mbid
                else:
                    track["artist"]["mbid"]=d["artist"]["mbid"]
                track["name"]=d["name"]

                track["number"]=i
                if tracks not in tracks:
                    tracks.append(track)
                    i+=1
            memcache.set("%s Videos playlist"%genre, tracks)
        
        self.response.out.write(json.dumps(tracks))


class Artista(Handler):
    def renderFront(self, artists=None, playlist=None):
        logging.error(artists)
        logging.error(playlist)
        self.render("front2.html",artists=artists, playlist=playlist)

    def get(self,resource):
        import urllib

        mbid=str(urllib.unquote(resource))
        name=artist.getName(mbid)

        self.renderFront(playlist={"tipo":"artist","data":{"mbid":mbid, "name":name}})

    def post(self,resource):
        artist_name=self.request.get('artist')
        logging.error(artist_name)
        artists=artist.search_artist(artist_name)
        logging.error(artists)
        if len(artists)==1:
            self.redirect("/artist/%s"%artists[0]["mbid"])
        else:
            logging.error(artists)
            self.renderFront(artists)


class Taga(Handler):
    def renderFront(self, artists=None, playlist=None):
        self.render("front2.html",artists=artists, playlist=playlist)

    def get(self,resource):
        import urllib

        tag=str(urllib.unquote(resource))

        self.renderFront(playlist={"tipo":"tag","data":tag})

    def post(self,resource):
        artist_name=self.request.get('artist')
        logging.error(artist_name)
        artists=artist.search_artist(artist_name)
        logging.error(artists)
        if len(artists)==1:
            self.redirect("/tag/%s"%artists[0]["mbid"])
        else:
            logging.error(artists)
            self.renderFront(artists)


class xhrFront(Handler):
    def renderFront(self, artists=None, playlist=None):
        self.render("front2.html",artists=artists, playlist=playlist)

    def get(self):
        self.renderFront(playlist={"tipo":"predefined","tag":"top"})

    def post(self):
        artist_name=self.request.get('artist')
        logging.error(artist_name)
        artists=artist.search_artist(artist_name)
        logging.error(artists)
        if len(artists)==1:
            self.redirect("/artist/%s"%artists[0]["mbid"])
        else:
            logging.error(artists)
            self.renderFront(artists)


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
        url=tools.get_url("lastfm","topArtists"," ")
        j=tools.get_json(url)
        artists=memcache.get("lastfm topArtists")
        if artists is None:
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
        url=tools.get_url("lastfm","topTags"," ")
        j=tools.get_json(url)
        tags=memcache.get("lastfm topTags")
        if tags is None:
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
        j=self.request.body
        data=json.loads(j)
        genre=data["data"]
        data=None
        data=memcache.get("create %s playlist"%genre)
        if data is None:
            url=tools.get_url("lastfm","genreCreate",genre)
            logging.error(url)
            result = urlfetch.fetch(url)      
            page=urllib2.urlopen(url)
            p=page.read()
            j=json.loads(p)

            
            tracks=[]
            for d in j["toptracks"]["track"]:
                
                track={}
                track["artist"]={}
                track["artist"]["name"]=d["artist"]["name"]
                mbid=d["artist"]["mbid"]
                cmbid=CorrectArtist.by_id(mbid)
                if cmbid is not None:
                    track["artist"]["mbid"]=cmbid.mbid
                else:
                    track["artist"]["mbid"]=mbid
                track["name"]=d["name"]

                tracks.append(track)

            data={"tracks":tracks}
            memcache.set("create %s playlist"%genre, data)
        self.response.out.write(json.dumps(data))

class xhrGetNextPl(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        logging.error(data)
        if data["type"]=="artist":
            action="artistNext"
        elif data["type"]=="tag":
            action="genreNext"

        url=tools.get_url("lastfm",action,data)
        logging.error(url)
        result = urlfetch.fetch(url)      
        page=urllib2.urlopen(url)
        p=page.read()
        j=json.loads(p)


        tracks=[]
        d=j["toptracks"]["track"]
        
        track={}
        track["artist"]={}
        track["artist"]["name"]=d["artist"]["name"]
        mbid=d["artist"]["mbid"]
        cmbid=CorrectArtist.by_id(mbid)
        if cmbid is not None:
            track["artist"]["mbid"]=cmbid.mbid
        else:
            track["artist"]["mbid"]=mbid
        track["name"]=d["name"]

        tracks.append(track)

        data={"tracks":tracks}


        data={"tracks":tracks}
        self.response.out.write(json.dumps(tracks))


class xhrCreateArtistPlayList(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        genre=data["data"]
        data=None
        data=memcache.get("create %s playlist"%genre)
        
        if data is None:
            url=tools.get_url("lastfm","artistCreate",genre)
            logging.error(url)
            result = urlfetch.fetch(url)      
            page=urllib2.urlopen(url)
            p=page.read()
            j=json.loads(p)
            

            
            tracks=[]
            for d in j["toptracks"]["track"]:
                
                track={}
                track["artist"]={}
                track["artist"]["name"]=d["artist"]["name"]
                mbid=d["artist"]["mbid"]
                cmbid=CorrectArtist.by_id(mbid)
                if cmbid is not None:
                    track["artist"]["mbid"]=cmbid.mbid
                else:
                    track["artist"]["mbid"]=mbid
                track["name"]=d["name"]

                tracks.append(track)

            data={"tracks":tracks}
            memcache.set("create %s playlist"%genre,data)
        self.response.out.write(json.dumps(data))

class xhrGetNextArtistPl(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        url=tools.get_url("lastfm","artistNext",data)
        result = urlfetch.fetch(url)      
        page=urllib2.urlopen(url)
        p=page.read()
        j=json.loads(p)
     
        tracks=[]
        d=j["toptracks"]["track"]
        
        track={}
        track["artist"]={}
        track["artist"]["name"]=d["artist"]["name"]
        mbid=d["artist"]["mbid"]
        cmbid=CorrectArtist.by_id(mbid)
        if cmbid is not None:
            track["artist"]["mbid"]=cmbid.mbid
        else:
            track["artist"]["mbid"]=mbid
        track["name"]=d["name"]

        tracks.append(track)

        data={"tracks":tracks}


        data={"tracks":tracks}
        self.response.out.write(json.dumps(tracks))

class SearchArtist(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        artist_name=data["name"]
        logging.error(artist_name)
        artists=artist.search_artist(artist_name)
        logging.error(artists)
       
        self.response.out.write(json.dumps(artists))
        

class Buy7digital(Handler):
    def post(self):
        j=self.request.body
        track=json.loads(j)

        url=tools.get_url("7digital", "buytrack", track)
        logging.error(url)
        xml=tools.get_xml(url)

        tracka=xml.getElementsByTagName("track")

        id=tracka[0].attributes.get("id").value


        self.response.out.write(json.dumps(id))

class BuyAmazon(Handler):
    def post(self):
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
                logging.error(x.getElementsByTagName("ASIN")[0].childNodes[0].nodeValue)
                break;        

app = webapp2.WSGIApplication([('/', xhrFront),
                               ('/xhrFront', xhrFront),
                               ('/xhrLogo',xhrLogo),('/xhrSimilar', xhrSimilar),('/xhrFrontVideos', xhrFrontVideos),('/xhrGetVideo',xhrGetVideo),
                               ('/xhrArtistInfo',xhrGetArtistInfo),('/xhrArtistTags',xhrGetArtistTags),
                               ('/xhrTagPlayList',xhrTagPlayList),('/xhrArtistPlayList',xhrArtistPlayList),('/xhrCreateTagPlayList',xhrCreateTagPlayList),('/xhrGetNextPl',xhrGetNextPl),('/xhrCreateArtistPlayList',xhrCreateArtistPlayList),('/xhrGetArtistsNextPl',xhrGetNextArtistPl),
                               ('/artist/([^/]+)?', Artista),('/tag/([^/]+)?', Taga),
                               ('/predefined',xhrFront),('/correctArtist',Correct),
                               ('/getTopArtist',getTopArtist),('/getTopTags',getTopTags),
                               ('/searchArtist',SearchArtist),
                               ('/Buy7digital',Buy7digital),('/BuyAmazon',BuyAmazon)

                               ], debug=True)
