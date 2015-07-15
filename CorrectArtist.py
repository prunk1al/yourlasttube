from google.appengine.ext import ndb

class CorrectArtist(ndb.Model):
    name = ndb.StringProperty(required = True, indexed=False)
    mbid = ndb.StringProperty(required = True, indexed=False)
    

    @classmethod
    def by_id(cls, uid):
        return CorrectArtist.get_by_id(uid)

