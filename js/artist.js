var artistCache = new Array()

    function Artist() {
        this.name = "";
        this.mbid = "";
        this.info = "";
        this.logo = "";
        this.similars = new Array();
        this.tags = new Array();
        this.active = false;

    };

Artist.prototype.getAndPut = function() {
    for (var i = 0; i < artistCache.length; i++) {
        if (artistCache[i].mbid == this.id) {
            var x = artistCache[i]
            this.name = x.name;
            this.mbid = x.mbid;
            this.info = x.info;
            this.putInfo()
            this.logo = x.logo;
            this.putLogo()
            this.similars = x.similars;
            this.tags = x.tags;
            this.putTags();
            return;
        }
    };

    this.getSimilar()
    this.getInfo()
    this.getLogo()

    this.getTags()

    artistCache.push(this)

};

Artist.prototype.getInfo = function() {
    var artist = this
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/xhrArtistInfo', true);
    xhr.onload = function() {
        artist.info = this.responseText;
        artist.putInfo()

    };
    var query = {
        "artist": artist.mbid
    };

    xhr.send(JSON.stringify(query));

}

Artist.prototype.putInfo = function() {
    var p = document.getElementById("artistInfo");
    if (p.childNodes.length > 1) {
        p.removeChild(p.childNodes[1]);
    };
    txt = document.createTextNode(this.info);
    p.appendChild(txt);
}

Artist.prototype.getLogo = function() {
    var artist = this
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/xhrLogo', true);
    xhr.onload = function() {
        // do something to response
        artist.logo = this.responseText
        artist.putLogo();
    };
    var query = '{"artist":' + artist.mbid + '}';
    xhr.send(JSON.stringify(query));

}
Artist.prototype.getsLogo = function() {
    var artist = this
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/xhrLogo', true);
    xhr.onload = function() {
        // do something to response
        artist.logo = this.responseText
        artist.putSimilar()

    };
    var query = '{"artist":' + artist.mbid + '}';
    xhr.send(JSON.stringify(query));

}

Artist.prototype.putLogo = function() {
    if (this.logo == "None") {
        this.logo = "http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|38|h|FFFFFF|_|" + this.name;
    }
    var div = document.getElementById("topLogo")
    if (div.hasChildNodes()) {
        for (var i = div.childNodes.length - 1; i >= 0; i--) {
            div.removeChild(div.childNodes[i]);
        };
    }
    var a = document.createElement("a")
    a.href = "/artist/" + this.mbid;
    var img = document.createElement("img");
    img.src = this.logo;
    img.style.width = "250px";
    img.title = this.name;

    a.appendChild(img)
    div.appendChild(a)

}

Artist.prototype.getSimilar = function() {
    var artist = this
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/xhrSimilar', true);
    xhr.onload = function() {
        // do something to response
        var similars = JSON.parse(this.responseText);
        console.log(similars)
        for (var i = similars.length - 1; i >= 0; i--) {
            similar = new Artist()
            similar.name = similars[i].name;
            similar.mbid = similars[i].mbid;
            similar.logo = similar.getsLogo()
            //similar.logo=similars[i].logo;
            artist.similars.push(similar)

        };

    };
    var query = '{"artist":' + artist.mbid + '}';
    xhr.send(JSON.stringify(query));

};

Artist.prototype.putSimilar = function() {

    var table = document.getElementById("similarLogos")

    for (var i = table.rows.length - 1; i >= 0; i--) {
        table.deleteRow(i);
    }

    for (var i = this.similars.length - 1; i >= 0; i--) {
        var similar = this.similars[i];

        if (similar.logo == null) {
            similar.logo = "http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|38|h|FFFFFF|_|" + similar.name;
        }

        var tr = document.createElement("tr")
        var a = document.createElement("a")
        a.href = "/artist/" + similar.mbid
        var img = document.createElement("img");
        img.src = similar.logo;
        img.id = similar.mbid
        img.alt = similar.name
        img.title = similar.name
        img.style.width = "150px"
        a.appendChild(img)
        tr.appendChild(a);
        table.appendChild(tr)

    };

};

Artist.prototype.getTags = function() {
    var artist = this
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/xhrArtistTags', true);
    xhr.onload = function() {
        // do something to response
        var response = JSON.parse(this.responseText)
        var tags = response["tags"]

        for (var i = tags.length - 1; i >= 0; i--) {
            artist.tags.push(tags[i])
        };
        artist.putTags()
    };
    var query = {
        "artist": artist.mbid
    };
    xhr.send(JSON.stringify(query));

}

Artist.prototype.putTags = function() {

    var p = document.getElementById("artistTags");

    for (var i = p.childNodes.length - 1; i >= 0; i--) {
        p.removeChild(p.childNodes[i])
    };
    for (var i = this.tags.length - 1; i >= 0; i--) {
        var a = document.createElement("a")
        a.appendChild(document.createTextNode(this.tags[i]))
        a.href = "/tag/" + this.tags[i]
        p.appendChild(a)
        p.appendChild(document.createTextNode("    "))
    };

}
