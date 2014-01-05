
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
        #similar=memcache.get("similars of %s"%mbid)
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
        artists=[]
        for a in j["artists"]["artist"]:
            artist={}
            artist["name"]=a["name"]
            artist["mbid"]=a["mbid"]
            artists.append(artist)
        self.response.out.write(json.dumps(artists))

class getTopTags(Handler):
    def get(self):
        url=tools.get_url("lastfm","topTags"," ")
        j=tools.get_json(url)
 
        tags=[]
        for t in j["tags"]["tag"]:
            tag={}
            tag["name"]=t["name"]
            tags.append(tag)
        self.response.out.write(json.dumps(tags))

class xhrCreateTagPlayList(Handler):
    def post(self):
        j=self.request.body
        data=json.loads(j)
        genre=data["data"]
        data=None

        url=tools.get_url("lastfm","genreCreate",genre)
        logging.error(url)
        result = urlfetch.fetch(url)      
        page=urllib2.urlopen(url)
        p=page.read()
        logging.error(p)
        j=json.loads(p)
        logging.error(j)

        
        tracks=[]
        for d in j["toptracks"]["track"]:
            logging.error(d)
            
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
        logging.error(data)
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
        logging.error(j)

        tracks=[]
        d=j["toptracks"]["track"]
        logging.error(d)
        
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

        url=tools.get_url("lastfm","artistCreate",genre)
        logging.error(url)
        result = urlfetch.fetch(url)      
        page=urllib2.urlopen(url)
        p=page.read()
        j=json.loads(p)
        

        
        tracks=[]
        for d in j["toptracks"]["track"]:
            logging.error(d)
            
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
        logging.error(data)
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
