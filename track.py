import logging 
from google.appengine.api import memcache
from google.appengine.ext import db

def get_tracks_mb(mbid):
    
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