from google.appengine.ext import ndb

class CorrectArtist(ndb.Model):
    name = ndb.StringProperty(required = True)
    mbid = ndb.StringProperty(required = True)
    

    @classmethod
    def by_id(cls, uid):
        return CorrectArtist.get_by_id(uid)

