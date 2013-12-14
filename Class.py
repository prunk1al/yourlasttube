from google.appengine.ext import ndb

class Tracks(ndb.Model):
    track_name=ndb.StringProperty(required=False, indexed=False)
    track_video=ndb.StringProperty(required=False)
    track_mbid=ndb.StringProperty(required=False,)
    track_number=ndb.IntegerProperty(required=False,indexed=False)
    track_views=ndb.IntegerProperty(default=0, indexed=False)


class Albums(ndb.Model):
    album_mbid=ndb.StringProperty(required=False)
    album_name=ndb.StringProperty(required=False, indexed=False)
    album_date=ndb.StringProperty(required=False,indexed=False)
    album_image=ndb.StringProperty(required=False,indexed=False)
    
class Artists(ndb.Model):
    artist_name=ndb.StringProperty(required=False)
    artist_mbid=ndb.StringProperty(required=False)
    disambiguation=ndb.StringProperty(required=False,indexed=False)
    letter=ndb.StringProperty(required=False)
    logo=ndb.StringProperty(required=False,indexed=False)
    background=ndb.StringProperty(required=False,indexed=False)



class Playlists(ndb.Model):
    playlist_name=ndb.StringProperty(required=True,indexed=False)
    playlist_json=ndb.JsonProperty(indexed=False)
    playlist_videos=ndb.JsonProperty(indexed=False)
class User(ndb.Model):
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
