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
import artist
import image
import album
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

    """def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))"""

class Tracks(ndb.Model):
    name=ndb.StringProperty(required=True)
    video=ndb.StringProperty(required=True)
    mbid=ndb.StringProperty(required=True)
    number=ndb.IntegerProperty(required=True)
    hottness=ndb.FloatProperty(required=False)
    views=ndb.IntegerProperty(default=0)


class Albums(ndb.Model):
    album_mbid=ndb.StringProperty(required=True)
    album_name=ndb.StringProperty(required=True)
    album_date=ndb.StringProperty(required=True)
    album_image=ndb.StringProperty(required=False)

class Artists(ndb.Model):
    artist_name=ndb.StringProperty(required=True)
    artist_mbid=ndb.StringProperty(required=True)
    disambiguation=ndb.StringProperty(required=True)
    letter=ndb.StringProperty(required=False)
    albums=ndb.StructuredProperty(Albums,repeated=True)
    logo=ndb.StringProperty(required=False)
    background=ndb.StringProperty(required=False)

class Playlists(ndb.Model):
    name=ndb.StringProperty(required=True)
    tracks=ndb.StructuredProperty(Tracks, repeated=True)

class Users(ndb.Model):
    name = ndb.StringProperty(required = True)
    pw_hash = ndb.StringProperty(required = True)
    email = ndb.StringProperty()



    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u








class MainPage(Handler):
    def render_front(self,tracks=""):
        self.render("front.html",tracks=tracks)

    def get(self):
       
        tracks=[]
        video=[]

        if tracks ==[]:
            qry=Tracks.query().order(-Tracks.hottness)
        
            for entity in qry.fetch(10):
                if entity.video not in video:
                    tracks.append(entity)
                    video.append(entity.video) 


        x=len(tracks)
        self.render_front(tracks[0:x])



    def post(self):
        ar=self.request.get('artist')

        mbid=artist.get_data(ar,d=True,I=True)
        
        if len(mbid)==1:
            self.redirect("/artist?mbid=%s"%mbid[0].mbid)
        else:
            for i in mbid:
                try:
                    self.response.headers.add_header('Set-Cookie','yourlastube%s=%s:::%s'%(str(i.mbid),str(i.artist.replace(' ','_').replace(",","_")),str(i.disambiguation.replace(' ','_'))))
                except:
                    pass
            self.redirect("/disam")

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
                im=image.get_image(mbid,name,key='artist')
                logging.error("DISAMBI")
                logging.error(im)
                if im != []:

                    ar=[mbid,name,disambiguation,im]
                    artists.append(ar)
                    taskqueue.add(url='/worker', params={'f':'artist.get_artist_mb("%s")'%mbid})
                    taskqueue.add(url='/worker', params={'f':'album.get_albums_mb("%s")'%mbid})
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
   

    def render_band(self,artist="",albums="",similar="",artist_mbid="",image="",images="",bg=""):
        
        self.render("band.html",artist=artist,albums=albums,similar=similar,artist_mbid=artist_mbid, image=image,images=images,bg=bg)

    def get(self):
        mbid=self.request.get('mbid')
        
        data=memcache.get("bandpage %s"%mbid) 
        if data is None:
            
            artist_mbid=mbid
        
            artist_data,album_data=artist.get_artist_albums(mbid)

            ancestor_key=ndb.Key(Artists,artist_mbid)
            logging.error(ancestor_key)
            
            #qry=Albums.query().ancestor(ancestor_key)

            #logging.error(qry.get())

            for i in Albums.query().iter():
                x=i.key
                logging.error(dir(x))
                logging.error(x.parent())

            similar=artist.get_similar(artist_mbid)
            similar_mbid=[]
            for s in similar:
            
                mbid=s[1]
                s_name=s[0]
                logo=image.get_image(mbid,s[0],'artist')
            
            
                similar_mbid.append((mbid,logo,s_name))
        

            im=image.get_image(artist_data.artist_mbid," ",'artist')
        
            bg=image.get_image(artist_mbid,"artist_name",'bg')

            for a in album_data:
                pass
                #taskqueue.add(url='/worker', params={'f':'track.get_tracks_mb("%s",key="worker")'%a[0]})

            data={"artist":artist_data,"albums":album_data,"similar":similar_mbid, "image":im,"bg":bg}
            logging.error(data)
            """
            data={  artist=Artists
                    albums=[Albums]
                    similar=[Artists]
                    images=[background, logo]

            """
            #memcache.set("bandpage %s"%artist_mbid, data)

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
        #data=memcache.get("albumpage %s"%mbid) 
        data=None
        if data is None:
        
        
            album_name,x=album.get_album_mb(mbid)

            artist_name=x[0]
            artist_mbid=x[1]
            bg=image.get_image(artist_mbid,artist_name,'bg')

            tracks=track.get_tracks_mb(mbid)
        

            videos=[]
            for t in tracks:
            
                videos.append([t.video, (t.track_mbid,t.song)])
                taskqueue.add(url='/worker', params={'f':'track.check_hottness("%s","%s")'%(t.track_mbid,t.hottness)})
        
            logo=image.get_image(artist_mbid,artist_name,'artist')

            data={"artist":artist_name,"artist_mbid":artist_mbid,"album":album_name,"tracks":videos,"album_id":mbid,"bg":bg,"logo":logo}
            #memcache.set("albumpage %s"%mbid,data) 
        self.render_album(**data)
        

class TrackPage(Handler):
    def render_track(self,name="",videos="", mbid="",artist="",song=""):
        self.render("track.html",name=name,videos=videos, mbid=mbid,artist=artist,song=song)
   
    def get(self):
       
        song_mbid=self.request.get("mbid")
        
        t=track.get_track(song_mbid)
        taskqueue.add(url='/worker', params={'f':'track.check_hottness("%s","%s")'%(t.track_mbid,t.hottness)})
        song=t.song
        video=t.video
        ar=artist.get_artist_mb(t.artist_mbid)
       

       
        self.render("track.html",artist=ar, song=song,videos=video,mbid=song_mbid)

    def post(self):

        song_mbid=self.request.get("mbid")
        new_video=self.request.get("video")
        artist=self.request.get("artist")
        song=self.request.get("song")
        for entity in Tracks.query(Tracks.track_mbid == song_mbid).fetch(1):
            entity.video=new_video
            #memcache.set(song_mbid,entity)
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
    def render_artist(self,artist="",images="",menu="",next_page="",letter=""):
        self.render("artist.html",artist=artist,images=images,menu=menu,next_page=next_page,letter=letter)

    def get(self):

        letter=self.request.get('letter')
        page=self.request.get('page')
        
        logging.error("letter '%s'"%letter)
        logging.error("page '%s'"%page)




        #prof.main(letter,page)   #profiling


        n=int(page)*9-9
        
        


        menu=[]
        for i in string.ascii_uppercase:
            menu.append(i)
    

        qry=Artist.query(Artist.letter == letter ).order(Artist.artist).fetch(9,offset=n,projection=[Artist.mbid, Artist.artist])
               


        images=[]
        for i in qry:
            mbid=i.mbid
            logo=image.get_image_url('logo',mbid)
            bg=image.get_image_url('bg',mbid)
            if bg is not None:
                bg=bg+"=s200"
            if logo is not None:
                logo=logo+"=s200"
            images.append([mbid,logo,bg])

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


class GenresPage(Handler):
    def render_genre(self,url=""):
        self.render("playlist.html",url=url)

    def get(self):
        genre=self.request.get("genre")
        query="select * from Genres where genre='%s'"%genre
       
        mbid=list(ndb.gql(query))
        a=[]
        first=None
        playlist=""
        random.shuffle(mbid[0].track_mbid)
        for i in mbid:
            
            passed=[]
            for x in i.track_mbid:
                
                query="select video from Tracks where track_mbid='%s'"%x
                
                videos=list(ndb.gql(query))

                
                if videos!=[]:
                    
                    if first is None:
                        
                        
                        first=videos.pop()
                        i=0
                    
                    for d in videos:
                        
                        if d.video!=" ":
                            
                            if d.video not in passed:
                            

                                if i>=140:
                                    break
                                playlist=playlist+d.video+","
                                passed.append(d.video)
                                i=i+1
        

        url="http://www.youtube.com/embed/"+first.video+"?playlist="+playlist
        
        self.render_genre(url=url)
        
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


class Clean(Handler):
    def get(self):
        key=self.request.get('key')
        """if key=='artist':
            ar=list(ndb.gql("select * from Artist order by mbid"))
            dupe=''
            for i in ar:
                if i.letter is None:
                    letter=i.artist[0]
                    i.letter=letter
                    logging.error(i.artist)
                    i.put()

                if i.mbid==dupe:
                    logging.error("Drop artist")
                    logging.error(dupe)
                    ndb.delete(i.key())
                dupe=i.mbid"""

        """if key=='albums':
            albums=list(ndb.gql("select mbid from Album order by mbid"))
            dupe=''
            for i in albums:
                if i.mbid==dupe:
                    logging.error("Drop Album")
                    logging.error(dupe)
                    ndb.delete(i.key())
                dupe=i.mbid"""
        if key=='tracks':
            taskqueue.add(url='/worker', params={'f':'tools.check_tracks()'})
            
            
           
            
            
        
        if key=='genres':
            genres=list(ndb.gql("select * from Genres"))
            for i in genres:
                if count(i.track_mbid)>=2:
                    #taskqueue.add(url='/worker', params={'f':'tools.clean_genres(%i)'%i.genre})
                    pass
            

                


class GenrePage(Handler):
    def get(self):
        genres=memcache.get("genres")
        if genres is None:
            query="select * from Genres order by genre"
            data=list(ndb.gql(query))
            genres=[]
            for i in data:
                if i.track_mbid is None: 
                   pass
                elif len(i.track_mbid)>=50:
                    logging.error(i.track_mbid)
                    genres.append(i)
            memcache.set("genres",genres)
        self.render("genres.html",genres=genres)

class PlaylistPage(Handler):
    def render_playlist(self,url=""):
        self.render("playlist.html",url=url)

    def get(self):
        tipo=self.request.get("tipo")
        if tipo=="album" or tipo == "artist":
            mbid=self.request.get("mbid")

            logging.error(self.request.arguments())

            d={'album':['number','asc'],'artist':['hottness','desc']}

            query="select video from Tracks where %s_mbid='%s' order by %s %s"%(tipo,mbid,d[tipo][0],d[tipo][1])
            data=list(ndb.gql(query))
            f=data.pop(0)
            first=f.video

            playlist=""
            videos=[]
            for d in data:
                if d.video not in videos:
                    playlist=playlist+d.video+","
                    videos.append(d.video)


            
        
        elif tipo=="lastfm":
            modo=self.request.get("modo")

            
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
                """first=memcache.get("lastfm first %s")
                    if first is not None:
                        playlist=memcache.get("lastfm playlist %s")
                        if playlist is not None:
                            url="http://www.youtube.com/embed/"+first+"?playlist="+playlist
                            self.render_playlist(url=url)"""
                genre=self.request.get("genre")
                url=tools.get_url("lastfm","toptagtracks",genre)
                tracks="toptracks"


            j=tools.get_json(url)
            
            for i in j[tracks]['track']:
                track_mbid=i['mbid']
                if track_mbid!="":
                    song=i['name']
                    artist=i['artist']['name']
                    artist_mbid=i['artist']['mbid']
                    t=ndb.gql("select video from Tracks where track_mbid='%s'"%track_mbid)
                
                    if t.get() is None:
                        video=track.get_video(artist,song)
                        if artist_mbid!="":
                            taskqueue.add(url='/artist', params={'mbid':artist_mbid})
                    else:
                        video=t.get().video
                    videos.append(video)

            if len(videos)>=1:
                first=videos.pop(0)
                for i in videos:
                    playlist=playlist+i+","
                        



        url="http://www.youtube.com/embed/"+first+"?playlist="+playlist
        self.render_playlist(url=url)
    


class Blacklist(Handler):
    def render_genres(self,genres=""):
        self.render("blacklist.html",genres=genres)
    def get(self):
        genres=[]
        query="select * from Genres order by genre"
        data=list(ndb.gql(query))
        for i in data:
            genres.append((i.genre,len(i.track_mbid)))
        self.render_genres(genres=genres)
    def post(self):

        logging.error(self.request.arguments())


        genres=[]
        names=[]

        
        for i in self.request.arguments():
            genre=list(ndb.gql("select * from Genres where genre='%s'"%i))
            for i in genre:
                ndb.delete(i.key())
        self.redirect('/Blacklist')
               
class Hottness(Handler):
    def get(self):
        query="select track_mbid from Tracks"
        tracks=list(ndb.gql(query))

        for t in tracks:
            taskqueue.add(url='/worker', params={'f':'track.update_hottness("%s")'%t.track_mbid})
class Sitespage(Handler):

    def get(self):
        #get artist:
        url="www.yourlastube.com"
        artists=[]
        a=list(ndb.gql("select mbid from Artist"))
        logging.error(a)
        for i in a:

            if i.mbid not in artist:
                artists.append(i.mbid)

        #get genres
        query="select * from Genres order by genre"
        data=list(ndb.gql(query))
        genres=[]
        for i in data:
            if i.track_mbid is None: 
                pass
            elif len(i.track_mbid)>=50:
                logging.error(i.track_mbid)
                genres.append(i)
        

        artist_url=["www.yourlastube.com/artists"]
        genre_url=["www.yourlastube.com/genres"]
        a="/artist?mbid="
        g="/genre?mbid="
        for i in artists:
            artist_url.append(url+a+i)
        for i in genres:
            genre_url.append(url+g+i)

        logging.error(artist_url)
        logging.error(genre_url)

class LastFmPage(Handler):
    
    def get(self):
        genres=memcache.get("lastfm genres")
        if genres is not None:
            self.render("last.html",genres=genres)
        else:
            url=tools.get_url("lastfm","toptags"," ")
            j=tools.get_json(url)

            genres=[]
            for i in j["tags"]["tag"]:

                genres.append((i["name"],i["url"][23:]))

            memcache.set("lastfm genres",genres)
            logging.error(genres)
            self.render("last.html",genres=genres)
                

        
class Sitespage(Handler):
    
    def get(self):
        #get artist:
        url="http://www.yourlastube.com"
        artist=[]
        artist_url=[]

        a=list(ndb.gql("select mbid from Artist"))
        for i in a:

            if i.mbid not in artist:
                artist.append(i.mbid)

              
        for i in string.ascii_uppercase:
            artist_url.append("http://www.yourlastube.com/artists/artists?letter=%s&amp;page=1"%i)
        
        
        a="/artist?mbid="
     
        for i in artist:
            artist_url.append(url+a+i)
        

        logging.error(artist_url)
       
        
        content="""<?xml version="1.0" encoding="UTF-8"?>
    <urlset
      xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
            http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
                    """

        for i in artist_url:
            content=content+"""<url>
                <loc>"%s"</loc>
                </url>
             """%i
       
        logging.error(content)

        content=content+"""</urlset>
                            """
        self.write(content)
        file_name = files.blobstore.create(mime_type='application/xml',_blobinfo_uploaded_filename='sitemap.xml')
        # Open the file and write to it
        with files.open(file_name, 'a') as f:
            f.write(content)

        # Finalize the file. Do this before attempting to read it.
        files.finalize(file_name)

        # Get the file's blob key
        blob_key = files.blobstore.get_blob_key(file_name)
        logging.error(blob_key)

class sitemap(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        resource='sitemap.xml'
        query=blobstore.BlobInfo.all()
        query.filter('filename =','sitemap.xml')
        if int(query.count()) >=1:
            blob_key=query[0].key()

        blob_info = blobstore.BlobInfo.get(blob_key)
        self.send_blob(blob_key)
        

class Worker(Handler):
    

    def post(self):
        function=self.request.get('f')
        logging.error(function)

        #eval(function)


app = webapp2.WSGIApplication([('/', MainPage),("/sitemap.xml",sitemap),("/sites",Sitespage),('/lastfm',LastFmPage),('/hottness',Hottness),('/Blacklist',Blacklist),
                                ('/worker',Worker),('/clean', Clean),('/disam',DisambiguationPage),('/playlist', PlaylistPage),
                                ('/genres',GenrePage),("/genre",GenresPage),('/artists',ArtistsPage),('/random',RandomPage),
                                ('/track', TrackPage),('/album', AlbumPage),('/artist', BandPage)], debug=True)
