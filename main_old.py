class Artista(Handler):
    def renderFront(self, artists=None, genres=None ,playlist=None, disambiguation=None, artist=None):
        self.render("front2.html",artists=artists, genres=genres,playlist=playlist,disambiguation=disambiguation, artist=artist)

    def get(self,resource):
        import urllib

        mbid=str(urllib.unquote(resource))
        key=ndb.Key("Artist",mbid)
        artist=key.get()
        logging.error(artist)
        if artist is None:
            artist=Artist(key=key)
            name=artist.getName()
            self.renderFront(artists=memcache.get("lastfm topArtists"), genres=memcache.get("lastfm topTags"), playlist={"tipo":"artist","data":{"mbid":mbid, "name":name}})


        else:
            artista=artist.toJson()
            logging.error(artista)
            name=artist.name

            self.renderFront(artists=memcache.get("lastfm topArtists"), genres=memcache.get("lastfm topTags"), playlist={"tipo":"artist","data":{"mbid":mbid, "name":name}}, artist=artista)

    def post(self,resource):
        artist_name=self.request.get('artist')
  
        artists=artist.search_artist(artist_name)
        if len(artists)==1:
            self.redirect("/artist/%s"%artists[0]["mbid"])
        else:
            self.renderFront(disambiguation=artists)


class Taga(Handler):
    def renderFront(self, artists=None, genres=None ,playlist=None, disambiguation=None, artist=None):
        self.render("front2.html",artists=artists, genres=genres,playlist=playlist,disambiguation=disambiguation, artist=artist)

    def get(self,resource):
        import urllib

        tag=str(urllib.unquote(resource))

        self.renderFront(artists=memcache.get("lastfm topArtists"), genres=memcache.get("lastfm topTags"), playlist={"tipo":"tag","data":{"name":tag}})

    def post(self,resource):
        artist_name=self.request.get('artist')
        artists=artist.search_artist(artist_name)
        if len(artists)==1:
            self.redirect("/tag/%s"%artists[0]["mbid"])
        else:
            self.renderFront(disambiguation=artists)

class ArtistRadio(Handler):
    def renderFront(self, artists=None, genres=None ,playlist=None, disambiguation=None, artist=None):
        self.render("front2.html",artists=artists, genres=genres,playlist=playlist,disambiguation=disambiguation, artist=artist)

    def get(self,resource):
        import urllib

        mbid=str(urllib.unquote(resource))
        key=ndb.Key("Artist",mbid)
        artist=key.get()
        if artist is None:
            artist=Artist(key=key)

        name=artist.getName()


        self.renderFront(artists=memcache.get("lastfm topArtists"), genres=memcache.get("lastfm topTags"), playlist={"tipo":"artist-radio","data":{"mbid":mbid, "name":name}})

    def post(self,resource):
        artist_name=self.request.get('artist')
  
        artists=artist.search_artist(artist_name)
        if len(artists)==1:
            self.redirect("/artist/%s"%artists[0]["mbid"])
        else:
            self.renderFront(disambiguation=artists)


class Correct(Handler):
   
    def get(self):
        self.render("correct.html")

    def post(self):
        name=self.request.get('name')
        wrong=self.request.get("wrong")
        right=self.request.get("right")
        c=CorrectArtist(name=name, mbid=right, key=ndb.Key('CorrectArtist',wrong))
        c.put()
        self.redirect("/correctArtist")


