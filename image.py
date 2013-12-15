import logging
from xml.dom import minidom

from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.api import files
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache
from google.appengine.api import urlfetch


import tools
import urllib2
import async
import album


def get_album_image_fanart(rpc):
        
        images=None 
        
        try:
            xml=minidom.parseString(rpc.get_result().content)            
            album_url=xml.getElementsByTagName("album")[0].getElementsByTagName("albumcover")[0].attributes.get('url').value+"/preview"
            images=urllib2.urlopen(album_url).read()

        except:
            pass
            
        return images
def  get_album_image_lastfm(rpc):
        
        images=None
                
        xml=minidom.parseString(rpc.get_result().content)
        releases=xml.getElementsByTagName('release')
        for i in releases:
                if images is None:
                    release=i.attributes.get('id').value
                    lastfm_url=tools.get_url("lastfm","album",release)
                    j=tools.get_json(lastfm_url)
                    album_url= j["album"]["image"][1]["#text"]
                    images=urllib2.urlopen(album_url).read()

        return images

def get_album_lastfm(params):

        url=url="http://www.musicbrainz.org/ws/2/release-group/"+params.album_mbid+"?inc=releases"
        rpc=urlfetch.create_rpc(deadline=5)
        urlfetch.make_fetch_call(rpc,url)
        images=get_album_image_lastfm(rpc)

        return images


def getLogoFromFanart(mbid):
    url=tools.get_url('fanart','artist',mbid)
    logging.error(url)        
    j=tools.get_json(url)
    if j is None:
        return None
    
    for i in j:
        try:
            logo=j[i]['hdmusiclogo'][0]['url']+'/preview'
        except:
            try:
                logo=j[i]['musiclogo'][0]['url']+'/preview'
            except:
                return None

    return logo











def fill_image(server,url):
    
    if server=='fanart':
        
        j=tools.get_json(url)
        
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
                
                
                tools.write_blob(fil,file_name)
            
               
            query=blobstore.BlobInfo.all().filter('filename =','logo_%s.png'%mbid)
            if int(query.count()) >=1:
                blob_key=query[0].key
            else:
                blob_key=None
            

            
            if blob_key is None:
       
                
                file_name = files.blobstore.create(mime_type='image/png',_blobinfo_uploaded_filename='logo_%s.png'%mbid)

                logging.error(logo)
                
                fil=urllib2.urlopen(logo).read()
                
                tools.write_blob(fil,file_name)
                
        
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
            async.test(albums)


    
    return logo
    

def get_image_url(type,mbid):
    data=memcache.get('%s,%s'%(type,mbid))
    if data is not None:
        return data
    try:
        query = blobstore.BlobInfo.all()
        query.filter('filename =', '%s_%s.png'%(type,mbid)).fetch(1)
    except:
        return None
    
    try:
        blob_key=query[0].key()
    except:
        return None
    url=images.get_serving_url(query[0].key())
    memcache.set('%s,%s'%(type,mbid),url)
    return url


def get_image(mbid,key=""):
    
    
    url=""
    if key=='logo':
        
        url=get_image_url('logo',mbid)
        if url is not None:
            return url
        else:
            logo=getLogoFromFanart(mbid)

            if logo is None:
                return None

            query=blobstore.BlobInfo.all().filter('filename =','logo_%s.png'%mbid)
            if int(query.count()) >=1:
                blob_key=query[0].key
            else:
                blob_key=None
            

            
            if blob_key is None:
       
                
                file_name = files.blobstore.create(mime_type='image/png',_blobinfo_uploaded_filename='logo_%s.png'%mbid)

                logging.error(logo)
                
                fil=urllib2.urlopen(logo).read()
                
                tools.write_blob(fil,file_name)
                logo=get_image_url('logo', mbid)
            
            #taskqueue.add(url='/worker', params={'f':'image.fill_image("fanart","%s")'%url})
            #url=fill_image('fanart',url)
            url=logo
   
    if key=='bg':
        
        
        try:
            

            query = blobstore.BlobInfo.all()
            query.filter('filename =', 'bg_%s.png'%mbid)
            blob_key=query[0].key()
            url=images.get_serving_url(query[0].key())+"=s1600"
            

        except:
            url=tools.get_url('fanart','artist',mbid)
            j=tools.get_json(url)
        
            if j is None:
                return None
        
            for artist in j:
                try:
                    name=artist

                    mbid=j[artist]['mbid_id']

                    logo=j[artist]['musiclogo'][0]['url']+'/preview'
            
                    bg=j[artist]['artistbackground'][0]['url']
                except:
                    return None


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
                    
                
                    tools.write_blob(fil,file_name)
                    bg=get_image_url('bg', mbid)
                    url=bg
            
    if key=='album':
        
        
        try:
                     
            query = blobstore.BlobInfo.all()
            query.filter('filename =', 'album_%s.png'%mbid)
            blob_key=query[0].key()
            url=images.get_serving_url(query[0].key())

               

        except:
            try:
                url=tools.get_url('fanart','album',mbid)
                xml=tools.get_xml(url)
                url=xml.getElementsByTagName("album")[0].getElementsByTagName("albumcover")[0].attributes.get('url').value
                
                url=url+"/preview"
                
                file_name = files.blobstore.create(mime_type='image/png',_blobinfo_uploaded_filename='album_%s.png'%mbid)
                logging.error(file_name)
                image=urllib2.urlopen(url).read()
                
                
                tools.write_blob(image,file_name)
                
            except:
                try:
                    
                    url="http://www.musicbrainz.org/ws/2/release-group/"+mbid+"?inc=releases"
                    xml=tools.get_xml(url)
                                       
                    
                    releases=xml.getElementsByTagName('release')
                    logging.error(releases)
                    for i in releases:
                        
                            release=i.attributes.get('id').value

                            logging.error("release: %s"%release)
                            url=tools.get_url("lastfm","album",release)
                            logging.error(url)
                            j=tools.get_json(url)

                            file_name = files.blobstore.create(mime_type='image/png',_blobinfo_uploaded_filename='album_%s.png'%mbid)
                            url= j["album"]["image"][1]["#text"]
                            image=urllib2.urlopen(url).read()
                            tools.write_blob(image,file_name)
                            return url


                except:
                    url=None
  
    return url
