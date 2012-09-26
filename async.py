from __future__ import with_statement
from google.appengine.api import urlfetch
from google.appengine.api import files
from google.appengine.ext import blobstore


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
