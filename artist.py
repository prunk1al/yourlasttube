import logging
from google.appengine.api import memcache
from google.appengine.ext import ndb
import tools
import image
import Class
from google.appengine.api.labs import taskqueue
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from io import BytesIO
from google.appengine.api import users, images, files


import track
import time
from CorrectArtist import CorrectArtist

class Artist(ndb.Model):
    name=ndb.StringProperty(required=False)
    logo=ndb.BlobKeyProperty(required=False,indexed=False)
    info=ndb.TextProperty(required=False)
    tags=ndb.PickleProperty(required=False)
    similars=ndb.KeyProperty(kind="Artist",required=False,repeated=True)
    image=ndb.StringProperty(required=False, indexed=False)

    def new(self, name=None, logo=None,info=None,tags=None,similars=[],image=None):
        self.name=name
        self.logo=logo
        self.info=info
        self.tags=tags
        self.similars=similars
        self.image=image

    def getData(self):
        logging.error("getData")

        mbid=self.key.id()
        url=tools.get_url("lastfm","artistInfo",mbid)
        j=tools.get_json(url)
   
        self.info=strip_tags(j["artist"]["bio"]["content"])
        self.name=j["artist"]["name"]
        self.image=j["artist"]["image"][4]["#text"]

        tags=[]
        for t in j["artist"]["tags"]["tag"]:
            tag=t["name"]
            tags.append(tag)
        self.tags=tags

        self.put()


    def getName(self):
        if self.name is None:
            self.getData()
            return self.name
        else:
            return self.name

    def getInfo(self):
        if self.info is None:
            self.getData()
            return self.info
        else:
            return self.info

    def getTags(self):
        if self.tags is None:
            self.getData()
            return self.tags
        else:
            return self.tags

    def getImage(self):
        if self.image is None:
            self.getData()
            return self.image
        else:
            return self.image

    def getSimilars(self):
        if self.similars is None or self.similars==[]:
            self.getSimilarsFromUrl()
        return self.similars


    def getSimilarsFromUrl(self):
        logging.error("getSimilars")
        mbid=self.key.id()
        similars=None
        #similar=memcache.get("similars of %s"%mbid)
        if similars is None:
            similars=[]
            url=tools.get_url('lastfm','similar',mbid)
            j=tools.get_json(url)
            if j is None:
                return []

            try:
                a=j['similarartists']['artist']
            except:
                return []
            for i in a:
                if i["mbid"]!="":
                    try:
      
                        cmbid=CorrectArtist.by_id(i["mbid"])
                        if cmbid is not None:
                            skey=ndb.Key("Artist",cmbid.mbid)
                        else:
                            skey=ndb.Key("Artist",i['mbid'])
                        similars.append(skey)
                    except:
                        pass
            self.similars=similars
            
            
            self.put()

    def serveLogo(self):
        try:
            return images.get_serving_url(self.getLogo())
        except: 
            return ""

    def toJson(self):

        import time
        time_start=time.time()


        artist={}

        artist["mbid"]=self.key.id()
        if self.name is not None:
            artist["name"]=self.name
        else:
            artist["name"]=d["artist"]["name"]
        
        if self.logo is not None:
            artist["logo"]=images.get_serving_url(self.logo)
        else:
            artist["logo"]=""
        if self.info is not None:
            artist["info"]=self.info
        else:
            artist["info"]=""

        if self.tags is not None:
            artist["tags"]=self.tags
        else: artist["tags"]=""

        actual=time.time() - time_start
        logging.error("befire getting similars: %s"%actual)

        if self.similars is not None:
            similars=[]
            s=ndb.get_multi(self.similars)
            for similar in s:
                similars.append({"name":similar.name, "logo":similar.image,"mbid":similar.key.id()})

            artist["similars"]=similars
        else: artist["similars"]=[]

        actual=time.time() - time_start
        logging.error("after getting similars: %s"%actual)

        return artist

    def getLogo(self):
        self.logo=None
        if self.logo is None:
            mbid=self.key.id()
            logging.error("getting Logo")
            url=tools.get_url('fanart','artist',mbid)
            logging.error(url)
            j=tools.get_json(url) 
            logging.error(url)
            logging.error(j)
            if j is None:
                return None

            try:
                logo=j['hdmusiclogo'][0]['url'].replace('fanart/','preview/')
                #logging.error(logo)
            except:
                try:
                    logo=j['musiclogo'][0]['url'].replace('fanart/','preview/')
                    #logging.error(logo)
                except:
                    return None

            data=urlfetch.fetch(logo).content

            logging.error("creating base64")


            content_type, body = BlobstoreUpload.encode_multipart_formdata(
              [], [('file', mbid, data)])

            logging.error("createing uploaddir")
            response = urlfetch.fetch(
              url=blobstore.create_upload_url('/uploadblob'),
              payload=body,
              method=urlfetch.POST,
              headers={'Content-Type': content_type},
              deadline=30
            )
            logging.error("response.content")
            logging.error(response.content)
            blob_key = blobstore.BlobKey(response.content)
            logging.error("blob_key")
            self.logo=blob_key
            logging.error("getLogo")
            logging.error(self)
            self.put()
        return self.logo

@ndb.non_transactional(allow_existing=True)
def generatesimilars(skey):
    similar=Artist(key=skey)
    similar.name=i["name"]
    similar.image=i["image"][4]["#text"]
    similar.put()

def search_artist(artist_name):


    logging.error("getting data of %s"%artist_name)
    data = None
    #data=memcache.get("search %s"%artist_name)
    if data is not None:
        logging.error("mbid from ndb or memcache get_data")
        return data

    url=tools.get_url('musicbrainz','artist',artist_name)
    logging.error(url)
    xml=tools.get_xml(url)
    parsed=xml.getElementsByTagName("artist")

    disambiguation=" "
    artists=[]

    if xml.getElementsByTagName("artist-list")[0].attributes.get("count").value == '1' :
        artist={}
        artist["mbid"]=parsed[0].attributes.get("id").value
        artist["name"]=parsed[0].getElementsByTagName("name")[0].childNodes[0].nodeValue
        artists.append(artist)
    else:

        for a in parsed:
            artist={}

            artist["mbid"]=a.attributes.get("id").value
            artist["name"]=a.getElementsByTagName("name")[0].childNodes[0].nodeValue

            try:
                artist["country"]=a.getElementsByTagName("area")[0].getElementsByTagName("name")[0].childNodes[0].nodeValue
            except:
                artist["country"]=""

            try:
                disambiguation=a.getElementsByTagName("disambiguation")[0].childNodes[0].nodeValue
            except:
                disambiguation=" "

            artists.append(artist)

    memcache.set("search %s"%artist_name, artists)

    return artists


def sjson(s):
   
    sim=s.get()
    if sim is None:
        sim=Artist(key=s)
    similar={"name":sim.getName(),
             "logo":sim.getImage(),
             "mbid":sim.key.id()
            }
    return similar 



from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

class BlobstoreUpload(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    upload_files = self.get_uploads('file')
    blob_info = upload_files[0]
    return self.response.write(blob_info.key())

  @classmethod
  def encode_multipart_formdata(cls, fields, files, mimetype='image/png'):
    """
    Args:
      fields: A sequence of (name, value) elements for regular form fields.
      files: A sequence of (name, filename, value) elements for data to be
        uploaded as files.

    Returns:
      A sequence of (content_type, body) ready for urlfetch.
    """
    boundary = 'paLp12Buasdasd40tcxAp97curasdaSt40bqweastfarcUNIQUE_STRING'
    crlf = '\r\n'
    line = []
    for (key, value) in fields:
      line.append('--' + boundary)
      line.append('Content-Disposition: form-data; name="%s"' % key)
      line.append('')
      line.append(value)
    for (key, filename, value) in files:
      line.append('--' + boundary)
      line.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
      line.append('Content-Type: %s' % mimetype)
      line.append('')
      line.append(value)
    line.append('--%s--' % boundary)
    line.append('')

    #body = crlf.join(line)
    s = BytesIO()
    for element in line:
        s.write(str(element))
        s.write(crlf)
    body = s.getvalue()
    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body

