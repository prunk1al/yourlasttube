
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

import Class
import artist
import album
import track
import image
import tools
import string
import playlists
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




class MainPage(Handler):
    def render_front(self,tracks=""):
        self.render("front.html",tracks=tracks)

    def get(self):
       
        tracks=[]
        video=[]

        
        video=playlists.get_front_playlist()       
       
       
        self.render_front(video)
        
        #taskqueue.add(url='/deleteBlobs',method='GET'); 


    def post(self):
        artist_name=self.request.get('artist')

        artists=artist.search_artist(artist_name)
        
        if len(artists)==1:
            self.redirect("/artist?mbid=%s"%artists[0].artist_mbid)
        else:
            for i in artists:
                try:
                    self.response.headers.add_header('Set-Cookie','yourlastube%s=%s:::%s'%(str(i.artist_mbid),str(i.artist_name.replace(' ','_').replace(",","_")),str(i.disambiguation.replace(' ','_'))))
                except:
                    pass
            self.redirect("/disam")


class deleteBlobs(Handler): 
    def get(self): 
        all = blobstore.BlobInfo.all(); 

        for x in all:
            logging.error(all.count())
            logging.error(x)
            t=x.delete()
            logging.error(x)
        more = (all.count()>0) 
       # blobstore.delete(all); 
        if more: 
            taskqueue.add(url='/deleteBlobs',method='GET'); 


class DisambiguationPage(Handler):
    def render_disam(self, artists=""):
        self.render("disambi.html",artists=artists)

    def get(self):
        c=self.request.cookies
        artists=[]
        nologo=[]

        for i in c:
        
            if i[0:11]!='yourlastube':
                pass
            else:
                name,disambiguation=c[i].split(":::")
                name=name.replace("_"," ")
                logging.error(i)
                mbid=i[11:]
                im=image.get_image(mbid,key='logo')
                logging.error("DISAMBI")
                logging.error(im)
                if im != []:

                    ar=[mbid,name,disambiguation,im]
                    artists.append(ar)
                    #taskqueue.add(url='/worker', params={'f':'artist.get_artist_mb("%s")'%mbid})
                    #taskqueue.add(url='/worker', params={'f':'album.get_albums_mb("%s")'%mbid})
                else:
                    ar=[mbid,name,disambiguation,im]
                    nologo.append(ar)


                self.response.headers.add_header("Set-Cookie", "%s=deleted; Expires=Thu, 01-Jan-1970 00:00:00 GMT"%str(i))
        
        if len(artists)==1:
            self.redirect("/artist?mbid=%s"%artists[0][0])
        if len(artists)==0:
            artists=nologo
        self.render_disam(artists)

class BandPage(Handler):
   

    def render_band(self,artist="",albums="",similar="",images=""):
        
        self.render("band.html",artist=artist,albums=albums,similar=similar,images=images)

    def get(self):
        mbid=self.request.get('mbid')
        
        data=memcache.get("bandpage %s"%mbid) 
        if data is None:
            
            artist_mbid=mbid
        
            artist_data,album_data=artist.get_artist_albums(mbid)

            album_data.sort(key=lambda tup: tup.album_date)
       
            """
            for i in Class.Albums.query().iter():
               
                logging.error(i.key.parent().get())

            """

            similar=artist.get_similar(artist_mbid)

            for s in similar:

                taskqueue.add(url='/worker', params={'f':'artist.get_artist_albums("%s")'%s.artist_mbid})
       
          

            data={"artist":artist_data,"albums":album_data,"similar":similar}
            logging.debug(data)
            """
            data={  artist=Artists
                    albums=[Albums]
                    similar=[Artists]
                    images=[background, logo]

            """
            memcache.set("bandpage %s"%artist_mbid, data)

        self.render_band(**data)

    def post(self):
        mbid=self.request.get('mbid')
        logging.error(mbid)
        url="/artist?mbid=%s"%mbid
        self.get()

class AlbumPage(Handler):
    def render_album(self,artist="",artist_mbid="",album="",tracks="",album_id="",bg="",logo=""):
        self.render("album.html",artist=artist,artist_mbid=artist_mbid,album=album,tracks=tracks,album_id=album_id,bg=bg,logo=logo)

    def get(self):

        mbid=self.request.get('mbid')      
        data=memcache.get("albumpage %s"%mbid) 
        data=None
        if data is None:
        
        
            
            album_data=album.get_album_data(mbid)

            artist_data=album_data.key.parent().get()

            tracks=track.get_tracks(mbid)
            

        
            data={"artist":artist_data,"album":album_data,"tracks":tracks}
            """
                data={  artist=Artist
                        album=Album
                        tracks=[Tracks]
                }
            """
            memcache.set("albumpage %s"%mbid,data) 
        self.render_album(**data)


class TrackPage(Handler):
    def render_track(self,artist="",album="", track=""):
        self.render("track.html",artist=artist,album=album, track=track)
   
    def get(self):
       
        track_mbid=self.request.get("mbid")
        
        track_data=Class.Tracks.query(Class.Tracks.track_mbid==track_mbid).get()


        album_data=track_data.key.parent().get()
        artist_data=album_data.key.parent().get()
       
        data={"artist":artist_data,"album":album_data,"track":track_data}
       
        self.render_track(**data)

    def post(self):

        song_mbid=self.request.get("mbid")
        new_video=self.request.get("video")
        artist=self.request.get("artist")
        song=self.request.get("song")
        for entity in Class.Tracks.query(Class.Tracks.track_mbid == song_mbid).fetch(1):
            entity.video=new_video
            #memcache.set(song_mbid,entity)
            entity.put()
            
        
        self.redirect("/track?mbid=%s"%song_mbid)

class PlaylistPage(Handler):
    def render_playlist(self,tracks="", tipo=""):
        self.render("playlist.html",tracks=tracks, tipo=tipo)

    def get(self):
        tipo=self.request.get("tipo")
        song=[]
        if tipo=="album" or tipo == "artist":
            mbid=self.request.get("mbid")

            if tipo=="album":
                song={"data":[]}

                album_data=album.get_album_data(mbid)
                artist_data=album_data.key.parent().get()
                tracks=track.get_tracks(mbid)
                tracks.sort(key=lambda tup: tup.track_number)
                for i in tracks:
                    video={"video_artist":artist_data.artist_name,"video_track":i.track_name,"playlist_videos":i.track_video}
                    song["data"].append(video)

            elif tipo=="artist":

                song=playlists.get_echonest_playlist(tipo,mbid)
                
               
                    
        elif tipo=="lastfm":
            modo=self.request.get("modo")

            artists_mbid=[]
            videos=[]
            playlist=""
            
            tracks="tracks"
            if modo=="hypped":
                url=tools.get_url("lastfm","hyppedtracks", " ")
            elif modo=="top":
                url=tools.get_url("lastfm","toptracks"," ")
            elif modo=="loved":
                url=tools.get_url("lastfm","lovedtracks"," ")
            elif modo=="tag":
                
                genre=self.request.get("genre")
                
                song=playlists.get_lastfmTag_playlist(genre)
            

        elif tipo=="echonest":
            modo=self.request.get("modo")
            if modo == 'radio':
                mbid=self.request.get("mbid")
                song=playlists.get_echonest_radio(tipo,mbid)
            elif modo =='tag':
                genre=self.request.get("genre")
            
                song=playlists.get_echonest_tag_radio(genre)
        
        logging.error(song)  
        self.render_playlist(tracks=song, tipo=tipo)


class ArtistsPage(Handler):
    def render_artist(self,artist="",images="",menu="",next_page="",letter=""):
        self.render("artist.html",artist=artist,images=images,menu=menu,next_page=next_page,letter=letter)

    def get(self):
        import image
        letter=self.request.get('letter')
        page=self.request.get('page')
        
        logging.error("letter '%s'"%letter)
        logging.error("page '%s'"%page)

        n=int(page)*9-9
        
        menu=[]
        for i in string.ascii_uppercase:
            menu.append(i)
    

        qry=Class.Artists.query(Class.Artists.letter == letter ).order(Class.Artists.artist_name).fetch(9,offset=n)
               


        images=[]
        for i in qry:
            mbid=i.artist_mbid
            logo=image.get_image_url('logo',mbid)
            if logo is None:
                bg=image.get_image_url('bg',mbid)
                if bg is not None:
                    ima=bg+"=s200"
                else:
                    ima=None
            else:
                ima=logo+"=s200"
            images.append([mbid,ima])

        if len(qry) ==9:
            next_page=int(page)+1
        else:
            next_page=0
        
        self.render_artist(qry,images,menu,next_page,letter=letter)

    def post(self):
        ar=self.request.get('artist')

        mbid=artist.get_data(ar,d=True,I=True)
        
        if len(mbid)==1:
            self.redirect("/artist?mbid=%s"%mbid[0].mbid)
        else:
            for i in mbid:
                try:
                    self.response.headers.add_header('Set-Cookie','%s=%s:::%s'%(str(i.mbid),str(i.artist.replace(' ','_').replace(",","_")),str(i.disambiguation.replace(' ','_'))))
                except:
                    pass
            self.redirect("/disam")


class LastFmPage(Handler):
    
    def get(self):
        genres=memcache.get("lastfm genres")
        if genres is not None:
            self.render("last.html",genres=genres,key="lastfm")
        else:
            url=tools.get_url("lastfm","toptags"," ")
            j=tools.get_json(url)

            genres=[]
            for i in j["tags"]["tag"]:

                genres.append((i["name"],i["url"][23:]))

            memcache.set("lastfm genres",genres)
            logging.error(genres)
            self.render("last.html",genres=genres)

class EchonestPage(Handler):
    
    def get(self):
        genres=memcache.get("echonest genres")
        if genres is not None:
            self.render("last.html",genres=genres,key="echonest")
        else:
            url=tools.get_url("echonest","tags"," ")
            logging.error(url)
            j=tools.get_json(url)

            genres=[]
            for i in j["response"]["terms"]:

                genres.append([i["name"]])

            memcache.set("echonest genres",genres)
            logging.error(genres)
            self.render("last.html",genres=genres,key="echonest")


class xhrArtist(Handler):
    def get(self):
        mbid=self.request.get('mbid') 
        self.render("xhrArtist.html",artist=mbid)

class xhrArtistImage(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data[10:-1]
        logging.error(mbid)
        logging.error(image.get_image(mbid,"bg"))
        self.response.out.write(image.get_image(mbid,"bg"))

   

class xhrLogo(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data[10:-1]

        cache=memcache.get("logo of %s"%mbid)
        if cache is None:
            cache=image.get_image(mbid,"logo")
            memcache.set("logo of %s"%mbid, cache)
        
        self.response.out.write(cache)       

class xhrAlbumImage(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data[9:-1]
        self.response.out.write(image.get_image(mbid,"album"))



class xhrAlbums(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data[10:-1]

        album_data=artist.getXhrAlbums(mbid)

        self.response.out.write(json.dumps(album_data))

class xhrSimilar(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data[10:-1]

        
        similar=artist.get_xhrsimilar(mbid)

        self.response.out.write(json.dumps(similar))

class xhrFront(Handler):
    def renderFront(self, artists=None):
        self.render("xhrfront.html",artists=artists)

    def get(self):
        self.renderFront()


    def post(self):
        artist_name=self.request.get('artist')

        artists=artist.search_artist(artist_name)
        
        if len(artists)==1:
            self.redirect("/xhrArtist?mbid=%s"%artists[0].artist_mbid)
        else:
            self.renderFront(artists)

class xhrTopArtists(Handler):
    def get(self):
        data=playlists.getTopTracks()

        artists=[]
        for d in data["tracks"]["track"]:
            artist={}
            artist["name"]=d["artist"]["name"]
            artist["mbid"]=d["artist"]["mbid"]
            if artist not in artists:
                artists.append(artist)

        self.response.out.write(json.dumps(artists))

class xhrFrontVideos(Handler):

    def get(self):
    
        data=playlists.getTopTracks()

        tracks=[]
        i=1
        for d in data["tracks"]["track"]:
            logging.error(d)
            track={}
            track["artist"]={}
            track["artist"]["name"]=d["artist"]["name"]
            track["artist"]["mbid"]=d["artist"]["mbid"]
            track["name"]=d["name"]
            track["number"]=i
            if tracks not in tracks:
                tracks.append(track)
                i+=1

        self.response.out.write(json.dumps(tracks))



class xhrGetVideo(Handler):

    def post(self):
    
        j=self.request.body
        data=json.loads(j)
        
        cache=None
        #cache=memcache.get("video of %s %s"%(data["name"],data["artist"]["name"]))
        if cache is None:
            data["video"]=track.get_video(data["artist"]["name"],data["name"])
  
            memcache.set("video of %s %s"%(data["name"],data["artist"]["name"]), data)
        
        self.response.out.write(json.dumps(data)) 

class xhrAlbum(Handler):
    def get(self):
        album=self.request.get("mbid")
        self.render("xhrAlbum.html",album=album)

    
class xhrGetAlbumTracks(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data["album"]
        
        tracks=track.getAlbumTracks(mbid)
        logging.error(tracks)
        tracks.sort(key=lambda tup: tup["number"])

        self.response.out.write(json.dumps(tracks))

class xhrGetTrackVideo(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        mbid=data["track"]

        self.response.out.write(track.getTrackVideo(mbid))

class xhrPlaylist(Handler):
    def get(self):
        mbid=self.request.get("mbid")
        tipo=self.request.get("tipo")

        if tipo=="artist":

            songs=playlists.get_echonest_playlist(tipo,mbid)
            tracks=[]
            logging.error(songs)
            for s in songs:
                logging.error(s)
                track={}
                track["artist"]=s["artist_name"]
                track["Ambid"]=s["artist_foreign_ids"][0]["foreign_id"][19:]
                track["name"]=s["title"]
                tracks.append(track)

        self.render("xhrPlaylist.html", tracks=tracks)

class Worker(Handler):
    

    def post(self):
        function=self.request.get('f')
        logging.error(function)

        eval(function)


app = webapp2.WSGIApplication([('/', xhrFront),('/echonest',EchonestPage),('/lastfm',LastFmPage),('/deleteBlobs',deleteBlobs),('/artists',ArtistsPage),('/playlist',PlaylistPage),('/disam',DisambiguationPage),('/worker',Worker),
                               ('/track', TrackPage),('/album',AlbumPage),('/artist', BandPage), 
                               ('/xhrArtist', xhrArtist),('/xhrFront', xhrFront),('/xhrAlbum',xhrAlbum),('/xhrPlaylist',xhrPlaylist),
                               ('/xhrLogo',xhrLogo),('/xhrAlbums', xhrAlbums),('/xhrAlbumImage', xhrAlbumImage),('/xhrSimilar', xhrSimilar),('/xhrTopArtists', xhrTopArtists),('/xhrFrontVideos', xhrFrontVideos),('/xhrGetVideo',xhrGetVideo),
                               ('/xhrGetAlbumTracks',xhrGetAlbumTracks),('/xhrGetTrackVideo',xhrGetTrackVideo),('/xhrArtistImage',xhrArtistImage)
                               ], debug=True)
