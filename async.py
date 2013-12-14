from __future__ import with_statement
from google.appengine.api import urlfetch
from google.appengine.api import files
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.api import memcache

import logging
import tools
import image
import json
from xml.dom import minidom

def handle_rpc(rpc,type,params):
    
    page=rpc.get_result()
    
    if type == "videos":
        
        content_type=page.headers['content-type']

 
        
        j=json.loads(page.content)
        try:
            data=j["feed"]["entry"][0]['media$group']['yt$videoid']['$t'] 
        except:
            data=" "
            
        params.track_video=data
            
    elif type == "albums_image":
        
        
        images=image.get_album_image_fanart(page)
        
        if images is None:
            images=image.get_album_lastfm(params)
            
            
        file_name = files.blobstore.create(mime_type='image/png',_blobinfo_uploaded_filename='album_%s.png'%params.album_mbid)
        
        if images is not None:
            tools.write_blob(images,file_name)      
            params.album_image=image.get_image_url('album',params.album_mbid)  

        memcache.set("get_album_data %s"%params.album_mbid,params)
    
    return params
        


def procces_rpc(rpc,type,params):
    result=handle_rpc(rpc,type,params)
    
    return result


def get_urls(urls,type="",params=""):
    
    rpcs=[]
    i=0
    async=[]
    logging.info("starting async")

    for url in urls:
        
        rpc=urlfetch.create_rpc(deadline=5)
        urlfetch.make_fetch_call(rpc,url)
        
        result=procces_rpc(rpc,type,params[i])
        rpc.callback=result
        
        async.append(result)
        i=i+1
        
    for rpc in rpcs:
        rpc.wait()

    logging.info("end async")
    return async   
