from __future__ import with_statement
import urllib2
import urllib
import os
import webapp2
import jinja2
import logging
import json
import time
import cgi
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import urlfetch
from xml.dom import minidom



class Tracks(db.Model):
    song=db.StringProperty(required=True)
    video=db.StringProperty(required=True)
    track_mbid=db.StringProperty(required=True)
    album_mbid=db.StringProperty(required=True)
    artist_mbid=db.StringProperty(required=True)
    number=db.IntegerProperty(required=True)
    created=db.DateTimeProperty(auto_now_add=True)

class Artist(db.Model):
    artist=db.StringProperty(required=True)
    mbid=db.StringProperty(required=True)
    created=db.DateTimeProperty(auto_now_add=True)
    disambiguation=db.StringProperty(required=True)
    """similar=db.ListProperty(unicode,required=False)
    has_albums=db.BooleanProperty(required=True)"""

class Album(db.Model):
    mbid=db.StringProperty(required=True)
    image=db.StringProperty(required=True)

class Genres(db.Model):
    genre=db.StringProperty(required=True)
    track_mbid=db.ListProperty(unicode,required=True)



from google.appengine.api import files
from google.appengine.ext import blobstore
from google.appengine.api import images


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


def insert_in_db(data,table):
    mbid='mbid'
    logging.error([table,mbid,data.mbid])
    if data != db.GqlQuery("select mbid from %s where %s='%s'"%(table,mbid,data.mbid)):
    
        logging.error("inserting %s"%data.artist)
        data.put()

        
def get_dbArtist(artist):

    query="select * from Artist where artist='%s'"%artist
    logging.error("get_dbArtist query")
    logging.error(query)
    data=memcache.get(query)
    
    if data is not None:
        if data!= []:
            if data[0].disambiguation is not None:
                data=None
        if data is not None:
            logging.error("mbid from memcache get_dbArtist")
            return data
    
    data=list(db.GqlQuery(query))
    memcache.set(query,data)
    if data != []:
        logging.error("mbid from db get_dbArtist")
    return data




def  get_similar(mbid=""):
    
    data=memcache.get("similar_%s"%mbid)
    logging.error("similar=%s"%data)
    if data is not None:
        return data

    
    logging.error("GETTING SIMILAR FROM ECHONEST")
    url=get_url('echonest','similar',mbid)
    j=get_json(url)
    
    if j is None:
        return []
    
    similar=[]
    
    for i in j['response']['artists']:
        name=i['name']
        s_mbid=i['foreign_ids'][0]['foreign_id'][19:]
        
        similar.append([name,s_mbid])

    logging.error("END OF ECHONEST CODE")



    
    memcache.set("similar_%s"%mbid,similar)

    
    return similar

def get_data(artist,d=False, I=False):
    
    logging.error("getting data of %s"%artist)
    data=get_dbArtist(artist)
    if data != []:
        logging.error("mbid from db or memcache get_data")
        return data
    
    url=get_url('musicbrainz','artist',artist)
    xml=get_xml(url)
    parsed=xml.getElementsByTagName("artist")
    
    disambiguation=" "
    mbid=[]

    logging.error(int(xml.getElementsByTagName("artist-list")[0].attributes.get("count").value))
    logging.error(xml.getElementsByTagName("artist-list")[0].attributes.get("count").value == '1')

    if xml.getElementsByTagName("artist-list")[0].attributes.get("count").value == '1' :
        
        mbidId=parsed[0].attributes.get("id").value
        url="http://musicbrainz.org/ws/2/artist/"+mbidId+"?inc=releases"

        logging.error(url)
        x=get_xml(url)  
        name=xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
        disambiguation=" "
        ar=Artist(artist=name, mbid=mbidId, disambiguation=disambiguation)
        if I==True:
            logging.error("INSERTING %s IN DATABASE"%name)
            insert_in_db(ar,'Artist')
        mbid.append(ar)
        memcache.set("select * from Artist where artist='%s'"%name,[ar])

    else:
        logging.error("yuhuu")
        for a in parsed:
        
            mbidId=a.attributes.get("id").value
            name=a.getElementsByTagName("name")[0].childNodes[0].nodeValue

            try:
                disambiguation=a.getElementsByTagName("disambiguation")[0].childNodes[0].nodeValue
                if d==False:
                    continue
            except:
                disambiguation=" "
            logging.error(mbidId)
            logging.error(name)
            ar=Artist(artist=name, mbid=mbidId, disambiguation=disambiguation)
            mbid.append(ar)
            memcache.set("select * from Artist where artist='%s'"%name,[ar])
    logging.error(mbid)

    return mbid

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


def get_tracks_mb(mbid):
    


    """CAMBIAR PARA QUE MEMCACHE RECOJA LOS CAMBIOS DE CANCION"""



    """buscamos el album con mayor numero de pistas"""
    query="select * from Tracks where album_mbid='%s'"%mbid
    logging.error(query)

    data=memcache.get(query)
    if data is not None:
        logging.error("mbid from memcache")
        return data
    else:
        logging.error("tracks not in memcache")


    d=list(db.GqlQuery(query))
    
    if d != []:
        logging.error("mbid from db")
        data=[]
        for t in d:
            data.append([t.track_mbid,t.song,t.artist_mbid])
        memcache.set(query,data)

        return data



    logging.error("track data from url")
    url=get_url('musicbrainz','tracks',mbid)
    xml=get_xml(url)
    release=xml.getElementsByTagName("release")

    track_n=0
    for r in release:
        
        track_c=r.getElementsByTagName("track-list")[0].attributes.get("count").value
        artist_mbid=r.getElementsByTagName("artist-credit")[0].getElementsByTagName("artist")[0].attributes.get("id").value
        if track_c > track_n:
            track_n=int(track_c)
            tracks=[]
            for t in r.getElementsByTagName("track"):
                track_mbid=t.getElementsByTagName("recording")[0].attributes.get("id").value
                track_name=t.getElementsByTagName("title")[0].childNodes[0].nodeValue
                track_number=int(t.getElementsByTagName("position")[0].childNodes[0].nodeValue)
                
                

                tracks.append((track_mbid, track_name ,artist_mbid,track_number))
                
    

    """insertamos en la base de datos"""

    album,x=get_album_mb(mbid)
    artist=x[0]
    logging.error(artist)

    for t in tracks:
        song=t[1]
        video=get_video(artist,song)

        if video != []:
            track_genres=get_track_genre(track_mbid)
            if track_genres is not None:

                for genre in track_genres:
                    data=memcache.get(genre)
                    if data is None :
                        k="select * from Genres where genre='%s'"% genre
                        logging.error(k)
                        data=list(db.GqlQuery(k))
                        
                        if data ==[]:
                            data=[Genres(genre=genre)]
                            
                            data[0].track_mbid=[track_mbid]
                    logging.error(genre)                       
                    logging.error(data)
                    if track_mbid not in data[0].track_mbid:
                        data[0].track_mbid.append(track_mbid)
                       
                    data[0].put()
                    
                    memcache.set(genre,data)

        track_mbid=t[0]
        album_mbid=mbid
        artist_mbid=t[2]

        p=Tracks(song=song,video=video,track_mbid=track_mbid,album_mbid=album_mbid,artist_mbid=artist_mbid, number=track_number)
        memcache.set(track_mbid,p)
        p.put()
    memcache.set(query,tracks)
    
    return tracks

def get_artist_mb(mbid):
    data=memcache.get("%s artist="%mbid)
    if data is not None:
        return data

    data=list(db.GqlQuery("select artist from Artist where mbid='%s'"%mbid))
    if data != []:
        memcache.set("%s artist="%mbid, data[0].artist)
        return data[0].artist

    url="http://www.musicbrainz.org/ws/2/artist/?query=arid:"+mbid
    xml=get_xml(url)

    name= xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
    memcache.set("%s artist="%mbid, name)
    a=Artist(artist=name, mbid=mbid,disambiguation=" ")
    a.put()
    return name

def get_album_mb(mbid):
    url="http://www.musicbrainz.org/ws/2/release-group/"+mbid+"?inc=artists"
    logging.error(url)
    xml=get_xml(url)
    logging.error("get_album_mb")
    album=xml.getElementsByTagName("title")[0].childNodes[0].nodeValue
    artist=xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
    mbid=xml.getElementsByTagName("artist")[0].attributes.get("id").value
    return album,(artist,mbid)



def get_video(artist,song):
    song=song.replace(" ","+").replace("-","+").replace("'","")
    
    data=memcache.get("%s,%s"%(artist,song))
    
    if data is None:
        v=[]
        if v !=[]:
            data=v[0].video
        else:
            
            url=get_url('youtube','video',[artist,song])
            xml=get_xml(url)
            if  xml.getElementsByTagName("yt:videoid")!= []:
                data=xml.getElementsByTagName("yt:videoid")[0].childNodes[0].nodeValue
            else:
                data=" "
        memcache.set("%s,%s"%(artist,song),data)
 
    return data


def get_track(mbid):
    data=memcache.get(mbid)
    if data is not None:
        return data
    query="select * from Tracks where track_mbid='%s'"%mbid
    logging.error(query)
    track=list(db.GqlQuery(query))

    data=track[0]
    
    memcache.set(mbid, data)
    return data

def write_blob(content, filename):
    # Open the file and write to it
    with files.open(filename, 'a') as f:
        f.write(content)

    # Finalize the file. Do this before attempting to read it.
    files.finalize(filename)

    # Get the file's blob key
    blob_key = files.blobstore.get_blob_key(filename)
    

def fill_image(server,url):
    
    if server=='fanart':
        logging.error(url)
        j=get_json(url)
        
        if j is None:
            return[]
        
        for artist in j:
            try:
                name=artist

                mbid=j[artist]['mbid_id']

                logo=j[artist]['musiclogo'][0]['url']+'/preview'
            
                bg=j[artist]['artistbackground'][0]['url']
            except:
                return []


            query=blobstore.BlobInfo.all()
            query.filter('filename =','bg_%s.png'%mbid)
            if int(query.count()) >=1:
                blob_key=query[0].key
            else:
                blob_key=None
            

            
            if blob_key is None:
       
                
                file_name = files.blobstore.create(mime_type='image/png',_blobinfo_uploaded_filename='bg_%s.png'%mbid)

                logging.error(bg)
                fil=urllib2.urlopen(bg).read()
                logging.error("create bg from fill")
                
                write_blob(fil,file_name)
            
               
            query=blobstore.BlobInfo.all().filter('filename =','logo_%s.png'%mbid)
            if int(query.count()) >=1:
                blob_key=query[0].key
            else:
                blob_key=None
            

            
            if blob_key is None:
       
                
                file_name = files.blobstore.create(mime_type='image/png',_blobinfo_uploaded_filename='logo_%s.png'%mbid)

                logging.error(logo)
                logging.error("create logo from fill")
                fil=urllib2.urlopen(logo).read()
                
                write_blob(fil,file_name)
                
        
        try: 
            x=j[artist]["albums"]
        except:
            return []
        albums=[]
        for album in j[artist]["albums"]:
            mbid=album
            try:   
                
                url=j[artist]["albums"][album]['albumcover'][0]['url']+'/preview'
                albums.append([url,mbid])
            except:
                url=None
        
        if len(albums)>=1:
            test(albums)


    
    return logo
    

def get_image_url(type,mbid):
    query = blobstore.BlobInfo.all()
    query.filter('filename =', '%s_%s.png'%(type,mbid))
    blob_key=query[0].key()
    url=images.get_serving_url(query[0].key())
    return url


def get_image(mbid,name,key=""):
    
    

    if key=='artist':
        
        try:
            url=get_image_url('logo',mbid)

        except:
            url=get_url('fanart','artist',mbid)
            url=fill_image('fanart',url)
            """j=get_json(url)
        
            if j is None:
                return[]
        
            for artist in j:
                try:
                    name=artist

                    mbid=j[artist]['mbid_id']

                    logo=j[artist]['musiclogo'][0]['url']+'/preview'
            
                    bg=j[artist]['artistbackground'][0]['url']
                except:
                    return []
            


                query=blobstore.BlobInfo.all().filter('filename =','logo_%s.png'%mbid)
                if int(query.count()) >=1:
                    blob_key=query[0].key
                else:
                    blob_key=None
            

            
                if blob_key is None:
    
                
                    file_name = files.blobstore.create(mime_type='image/png',_blobinfo_uploaded_filename='logo_%s.png'%mbid)

                    logging.error(logo)
                    logging.error("create logo from ")
                    fil=urllib2.urlopen(logo).read()
                    
                    write_blob(fil,file_name)"""

                    



    if key=='bg':
        
        
        try:
            

            query = blobstore.BlobInfo.all()
            query.filter('filename =', 'bg_%s.png'%mbid)
            blob_key=query[0].key()
            url=images.get_serving_url(query[0].key())+"=s0"
            

        except:
            url=get_url('fanart','artist',mbid)
            j=get_json(url)
        
            if j is None:
                return[]
        
            for artist in j:
                try:
                    name=artist

                    mbid=j[artist]['mbid_id']

                    logo=j[artist]['musiclogo'][0]['url']+'/preview'
            
                    bg=j[artist]['artistbackground'][0]['url']
                except:
                    return []


                query=blobstore.BlobInfo.all()
                query.filter('filename =','bg_%s.png'%mbid)
                if int(query.count()) >=1:
                    blob_key=query[0].key
                else:
                    blob_key=None
            

            
                if blob_key is None:
       
                
                    file_name = files.blobstore.create(mime_type='image/png',_blobinfo_uploaded_filename='bg_%s.png'%mbid)

                    logging.error(bg)
                    fil=urllib2.urlopen(bg).read()
                    logging.error("create bg from fill")
                
                    write_blob(fil,file_name)
                    url=bg
            
    if key=='album':
        
        
        try:
                     
            query = blobstore.BlobInfo.all()
            query.filter('filename =', 'album_%s.png'%mbid)
            blob_key=query[0].key()
            url=images.get_serving_url(query[0].key())

               

        except:
            try:
                url=get_url('fanart','album',mbid)
                xml=get_xml(url)
                url=xml.getElementsByTagName("album")[0].getElementsByTagName("albumcover")[0].attributes.get('url').value
                
                url=url+"/preview"
                
                file_name = files.blobstore.create(mime_type='image/png',_blobinfo_uploaded_filename='album_%s.png'%mbid)
                logging.error(url)
                image=urllib2.urlopen(url).read()
                logging.error("creating new album in blobstore")
                
                write_blob(image,file_name)
                
            except:
                try:
                    url=get_url('lastfm','album', mbid)
                    xml=get_xml(url)
                   

                except:
                    url=None
  
    return url


def get_track_genre(mbid):

    data=memcache.get("genre %s"%mbid)
    if data is not None:
        return data

    logging.error("Getting Track Genre")

    
    url=get_url('lastfm','genres', mbid)
    

    try:
        
        xml=get_xml(url)
        
        tags=xml.getElementsByTagName("tag")

        genre=[]
        for tag in tags:
            name=tag.childNodes[1].childNodes[0].nodeValue.replace("'"," ").title()
            count=tag.getElementsByTagName("count")[0].childNodes[0].nodeValue
            logging.error(name)
            if int(count)>=50 or len(genre)>=5:
                if name not in genre:
                    genre.append(name)

            else:
                break
        
        memcache.set("genre %s"%mbid,genre)
        return genre
    except:
        logging.error("fallo al descargar TrackTags")
        return None

def handle_image(rpc,mbid):
    logging.error("create albums from fill")
    result = rpc.get_result()
    fil=result.content
    file_name = files.blobstore.create(mime_type='image/png',_blobinfo_uploaded_filename='album_%s.png'%mbid)           
    write_blob(fil,file_name)

    # ... Do something with result...

# Use a helper function to define the scope of the callback.
def create_image(rpc,mbid):
    return lambda: handle_image(rpc,mbid)


def test(urls):
    
    rpcs = []
    for url in urls:
        query=blobstore.BlobInfo.all().filter('filename =','album_%s.png'%url[1])
        if int(query.count()) >=1:
            blob_key=query[0].key
        else:
            rpc = urlfetch.create_rpc(deadline = 5)
            urlfetch.make_fetch_call(rpc, url[0])
            rpc.callback = create_image(rpc,url[1])

            rpcs.append(rpc)

    for rpc in rpcs:
        rpc.wait()


def main(mbid):

    # This is the main function for profiling
    # We've renamed our original main() above to real_main()
    import cProfile, pstats, StringIO
    prof = cProfile.Profile()
    prof = prof.runctx("real_main()", globals(), locals())
    stream = StringIO.StringIO()
    stats = pstats.Stats(prof, stream=stream)
    stats.sort_stats("cumulative")  # Or cumulative
    stats.print_stats(80)  # 80 = how many to print
    logging.info("Profile data:\n%s", stream.getvalue())

def real_main():
    mbid="6b966946-5274-4e3d-aabb-7563814d805f"
    artist=get_artist_mb(mbid)
    logging.error(artist)
        
    album_mbid=get_albums_mb(mbid)
    images=[]



    similar=get_similar(mbid)
    similar_mbid=[]
    for s in similar:
        logging.error(s)
        mbid=s[1]
        logo=get_image(mbid,s[0],'artist')
        logging.error(s[0])
        similar_mbid.append((mbid,logo))
            
                
    image=get_image(mbid,artist,'artist')
        
    bg=get_image(mbid,artist,'bg')
