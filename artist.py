import logging 
from google.appengine.api import memcache
from google.appengine.ext import db

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