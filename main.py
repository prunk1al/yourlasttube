import urllib2
import os
import webapp2
import jinja2
import logging
import random
import string
import time
import cgi
import json
from xml.dom import minidom
from google.appengine.api import memcache
from google.appengine.ext import db
import tools


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


def search_artist(artist):
    logging.error(artist)
    artist=artist.replace("-"," ")
    if list(db.GqlQuery("select * from Artist where artist='%s'"%artist))==[]:
        logging.error("not in Artist")
        """get_similar_artist(artist)"""



class MainPage(Handler):
    def render_front(self,tracks=""):
        self.render("front.html",tracks=tracks)

    def get(self):

        
        for entity in Tracks.all().filter("video !=", ' ').run(limit=3):
            logging.error(entity.video)

        tracks=""
        self.render_front(tracks)

    def post(self):
        artist=self.request.get('artist')

        mbid=tools.get_data(artist,d=True,I=True)
        logging.error("Ya tenemos a los artistas")
        if len(mbid)==1:
            logging.error("redirigiendo")
            self.redirect("/artist?mbid=%s"%mbid[0].mbid)

        else:
            logging.error("ANTES DE LA REDIRECCION")
            logging.error(len(mbid))
            for i in mbid:
                logging.error(i.mbid)
                logging.error(i.artist)
                logging.error(i.disambiguation)
                try:
                    self.response.headers.add_header('Set-Cookie','%s=%s:::%s'%(str(i.mbid),str(i.artist.replace(' ','_').replace(",","_")),str(i.disambiguation.replace(' ','_'))))
                except:
                    pass
            self.redirect("/disam")

class DisambiguationPage(Handler):
    def render_disam(self, artists=""):
        self.render("disambi.html",artists=artists)

    def get(self):
        c=self.request.cookies
        logging.error("YUHUUUU")
        artists=[]
        for i in c:
            logging.error(i)
            logging.error(c[i].replace('_',' '))
            name,disambiguation=c[i].split(":::")
            image=tools.get_image(i,key='artist')
            artist=[i,name,disambiguation,image]

            artists.append(artist)
            logging.error(artists)
            self.response.headers.add_header("Set-Cookie", "%s=deleted; Expires=Thu, 01-Jan-1970 00:00:00 GMT"%str(i))

        self.render_disam(artists)

    def post(self):
        artist=self.request.get('artist')

        mbid=tools.get_data(artist,d=True,I=True)
        logging.error("Ya tenemos a los artistas")
        if len(mbid)==1:
            logging.error("redirigiendo")
            self.redirect("/artist?mbid=%s"%mbid[0].mbid)

        else:
            logging.error("ANTES DE LA REDIRECCION")
            logging.error(len(mbid))
            for i in mbid:
                logging.error(i.mbid)
                logging.error(i.artist)
                logging.error(i.disambiguation)
                try:
                    self.response.headers.add_header('Set-Cookie','%s=%s:::%s'%(str(i.mbid),str(i.artist.replace(' ','_').replace(",","_")),str(i.disambiguation.replace(' ','_'))))
                except:
                    pass
            self.redirect("/disam")
            



class BandPage(Handler):

    def render_band(self,artist="",albums="",similar="",artist_mbid=""):
        
        self.render("band.html",artist=artist,albums=albums,similar=similar,artist_mbid=artist_mbid)

    def get(self):
        mbid=self.request.get('mbid')
        artist_mbid=mbid
        artist=tools.get_artist_mb(mbid)
        logging.error("ARTISTA:%s"%artist)
        album_mbid=tools.get_albums_mb(mbid)
        logging.error("ALBUMS: %s"%album_mbid)



        similar=tools.get_similar(artist)
        similar_mbid=[]
        for s in similar:
            mbid=tools.get_data(s,d=False,I=False)
            if len(mbid)==1:
                similar_mbid.append(mbid[0])


        
        self.render_band(artist,album_mbid,similar_mbid, artist_mbid=artist_mbid)

      
class AlbumPage(Handler):
    def render_album(self,artist="",album="",tracks="",album_id=""):
        self.render("album.html",artist=artist,album=album,tracks=tracks,album_id=album_id)

    def get(self):

        mbid=self.request.get('mbid')      

        
        
        album,artist=tools.get_album_mb(mbid)
        logging.error("ARTISTA:%s"%artist)

                
        tracks=tools.get_tracks_mb(mbid)
        

        videos=[]
        for t in tracks:
            x=tools.get_track(t[0])
            
            videos.append([x.video, t])
        
        self.render_album(artist=artist,album=album,tracks=videos,album_id=mbid)
        

class TrackPage(Handler):
    def render_track(self,name="",videos="", mbid="",artist="",song=""):
        self.render("track.html",name=name,videos=videos, mbid=mbid,artist=artist,song=song)
   
    def get(self):
       
        song_mbid=self.request.get("mbid")
        
        track=tools.get_track(song_mbid)
       
        song=track.song
        video=track.video
        artist=tools.get_artist_mb(track.artist_mbid)
        genres=tools.get_track_genre(song_mbid) 
       
        self.render("track.html",artist=artist, song=song,videos=video,mbid=song_mbid)

    def post(self):

        song_mbid=self.request.get("mbid")
        new_video=self.request.get("video")
        artist=self.request.get("artist")
        song=self.request.get("song")
        for entity in Tracks.all().filter("track_mbid =", song_mbid).fetch(1):
            entity.video=new_video
            memcache.set(song_mbid,entity)
            
            entity.put()
            
        
        self.redirect("/track?mbid=%s"%song_mbid)


        






class RandomPage(Handler):
    def render_random(self,lista=""):
        first=lista.pop()
        playlist=""
        for i in lista:
            playlist=playlist+i+","
        logging.error(first)
        logging.error(playlist)
        url="http://www.youtube.com/embed/"+first+"?playlist="+playlist
        self.render("random.html", url=url)

        self.redirect(str(url))
    def get(self):
        
        videos=None

        if videos is None:
            videos=[]
            for entity in Tracks.all().filter("video !=", " ").fetch(150):
                videos.append(entity.video)
                            

        
        random.shuffle(videos)
        self.render_random(videos[0:150])

class ArtistsPage(Handler):
    def render_artist(self,artist=""):
        self.render("artist.html",artist=artist)

    def get(self):

                
        
        
        artist=list(db.GqlQuery("select * from Artist order by artist"))
            
        

        self.render_artist(artist)

    def post(self):
        artist=self.request.get('artist')
        artist=artist.replace(" ","-")
        
        search(artist)
        self.redirect("/"+artist)


class GenresPage(Handler):
    def render_genre(self,url=""):
        self.render("playlist.html",url=url)

    def get(self):
        genre=self.request.get("genre")
        query="select * from Genres where genre='%s'"%genre
        logging.error(query)
        mbid=list(db.GqlQuery(query))
        a=[]
        first=None
        playlist=""
        for i in mbid:
            passed=[]
            for x in i.track_mbid:
                logging.error(x)
                query="select video from Tracks where track_mbid='%s'"%x
                logging.error(query)
                videos=list(db.GqlQuery(query))
                logging.error(videos)
                if videos!=[]:
                    
                    if first is None:
                        first=videos.pop()
                    
                    for d in videos:
                        if d.video not in passed:
                            playlist=playlist+d.video+","
                            passed.append(d.video)
        

        url="http://www.youtube.com/embed/"+first.video+"?playlist="+playlist
        logging.error(url)
        self.render_genre(url=url)
        


class Clean(Handler):
    def get(self):
        artist=list(db.GqlQuery("select mbid from Artist order by mbid"))
        dupe=''
        for i in artist:
            if i.mbid==dupe:
                logging.error("Drop artist")
                logging.error(dupe)
                db.delete(i.key())
            dupe=i.mbid

        albums=list(db.GqlQuery("select mbid from Album order by mbid"))
        dupe=''
        for i in albums:
            if i.mbid==dupe:
                logging.error("Drop Album")
                logging.error(dupe)
                db.delete(i.key())
            dupe=i.mbid

        track=list(db.GqlQuery("select track_mbid from Tracks order by track_mbid"))
        dupe=''
        for i in track:
            if i.track_mbid==dupe:
                logging.error("Drop tracks")
                logging.error(dupe)
                db.delete(i.key())
            dupe=i.track_mbid

class GenrePage(Handler):
    def get(self):
        query="select genre from Genres order by genre"
        data=list(db.GqlQuery(query))
        self.render("genres.html",genres=data)

class PlaylistPage(Handler):
    def render_playlist(self,url=""):
        self.render("playlist.html",url=url)

    def get(self):
        tipo=self.request.get("tipo")
        mbid=self.request.get("mbid")

        logging.error(self.request.arguments())
        query="select video from Tracks where %s_mbid='%s' and video!=' '"%(tipo, mbid)
        data=list(db.GqlQuery(query))
        first=data.pop()
        playlist=""
        videos=[]
        for d in data:
            if d.video not in videos:
                playlist=playlist+d.video+","
                videos.append(d.video)

        logging.error(first.video)
        logging.error(playlist)
        url="http://www.youtube.com/embed/"+first.video+"?playlist="+playlist
        self.render_playlist(url=url)





app = webapp2.WSGIApplication([('/', MainPage),('/clean', Clean),('/disam',DisambiguationPage),('/playlist', PlaylistPage),('/genres',GenrePage),("/genre",GenresPage),('/artists',ArtistsPage),('/random',RandomPage),('/track', TrackPage),('/album', AlbumPage),('/artist', BandPage)], debug=True)
