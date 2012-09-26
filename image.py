import logging
from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.api import files



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
