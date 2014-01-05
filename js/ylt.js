function EventedArray(handler) {
    this.stack = [];
    this.isfirst = true;
    this.hasfive = false;
    this.mutationHandler = handler || function() {};
    this.setHandler = function(f) {
        this.mutationHandler = f;
    };
    this.callHandler = function() {
        if (typeof this.mutationHandler === 'function') {
            this.mutationHandler();
        }
    };
    this.push = function(obj) {
        this.stack.push(obj);
        this.callHandler();
    };
    this.pop = function() {

        return this.stack.pop();
    };
    this.getArray = function() {
        return this.stack;
    }
}

var playing;

var handler = function() {
    if (this.isfirst) {
        this.isfirst = false;
        var track = this.pop()
        playing = track;
        getNextPl();
        track.active = true;
        addFirstVideo(track)
    }
    if (!this.hasfive) {
        if (this.getArray().length >= 5) this.hasfive = true;
        getytTopImages(this)
    }
};

var ytplist = new EventedArray();
ytplist.setHandler(handler);

var plistpage=0;
var player;
var activeTag="";
var activeArtist="";
var type;
var session;
var artistCache = new Array();

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
    img.style.width = "152px";
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
        artist.clearSimilar();
        for (var i = similars.length - 1; i >= 0; i--) {
            similar = new Artist()
            similar.name = similars[i].name;
            similar.mbid = similars[i].mbid;
            //similar.logo = similar.getsLogo()
            similar.logo = similars[i].logo;
            artist.similars.push(similar)
            if (artist.similars.length == similars.length) {
                artist.putSimilar()
            }

        };

    };
    var query = '{"artist":' + artist.mbid + '}';
    xhr.send(JSON.stringify(query));

};

Artist.prototype.clearSimilar = function() {
    var table = document.getElementById("similarLogos")

    for (var i = table.rows.length - 1; i >= 0; i--) {
        table.deleteRow(i);
    }
}

Artist.prototype.putSimilar = function() {

    var table = document.getElementById("similarLogos")

    for (var i = this.similars.length - 1; i >= 0; i--) {
        var similar = this.similars[i]

        if (similar.logo == "None") {
            similar.logo = "http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|38|h|FFFFFF|_|" + similar.name;
        }

        var tr = document.createElement("tr")
        var div = document.createElement("div")
        div.setAttribute("class", "image")
        var a = document.createElement("a")
        a.href = "/artist/" + similar.mbid
        a.setAttribute("class", "hcaption")
        a.setAttribute("data-target", "#" + similar.name)
        var text = document.createElement("div")
        text.id = similar.name
        text.setAttribute("class", "text")
        var h5 = document.createElement("h5")
        text.appendChild(h5.appendChild(document.createTextNode(similar.name)))
        var img = document.createElement("img");
        img.src = similar.logo;
        img.id = similar.mbid
        img.alt = similar.name
        img.title = similar.name
        img.style.height = "175px"
        img.style.width = "235px"
        a.appendChild(img)
        div.appendChild(a)
        div.appendChild(text)
        //tr.appendChild(a);
        tr.appendChild(div);
        table.appendChild(tr)

    };
}

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

function Track(nombre, artista) {
    this.name = nombre
    this.artist = artista
    this.ytid = ""
    this.img = ""
    this.active = false;
    this.searchVideo();
}

Track.prototype.searchVideo = function() {
    var track = this
    var xhr = new XMLHttpRequest();
    xhr.open('post', '/xhrGetVideo', true);
    xhr.onload = function() {
        // do something to response
        var response = JSON.parse(this.responseText);
        track.img = response.img
        track.ytid = response.ytid
        var ytlist = ytplist.getArray();
        var isin = false;

        if (track.ytid == " ") {
            return;
        }

        if (ytlist.length == 0) {
            ytplist.push(track);
            isin = true
        }

        for (var i = 0; i < ytlist.length; i++) {

            if (ytlist[i].ytid == track.ytid) {
                isin = true;
            }
        };

        if (!isin) {
            ytplist.push(track);
        }

    };
    xhr.send(JSON.stringify(this));
};

function setPlayList(tipo, data) {

    if (tipo == "tag") {
        url = '/xhrCreateTagPlayList';
        type="tag"
    } else if (tipo == "artist") {
        url = '/xhrCreateArtistPlayList';
        type="artist"
    } else if (tipo == "predefined") {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/xhrFrontVideos', true);
        xhr.onload = function() {
            // do something to response
            var tracks = JSON.parse(this.responseText);
            for (var i = 0; i < tracks.length; i++) {
                var artist = new Artist();
                artist.name = tracks[i].artist.name;
                artist.mbid = tracks[i].artist.mbid;
                track = new Track(tracks[i]["name"], artist);

            };
        };
        xhr.send();
        return;
    };

    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, false);
    xhr.onload = function() {
        var response = JSON.parse(this.responseText);
        console.log(response);
        plistpage=6;
            response = response["tracks"]
        if (tipo == "artist") {
            meta = document.getElementById("desc");
            console.log(response);
            meta.content = response[0]["artist"]["name"] + " Playlist";
        }
        if (tipo == "tag") {
            activeTag=data;
            
        }
        if(tipo=="artist"){
            activeArtist=data
        }
        
        for (var i = 0; i < response.length; i++) {
            var r = response[i];

            var artist = new Artist();
            artist.name = r["artist"]["name"];
            artist.mbid = r["artist"]["mbid"];
            var track = new Track(r["name"], artist);

        };
    };
    var query = {
        "data": data
    };
    xhr.send(JSON.stringify(query));
};

function changeArtist(artist) {
    artist.getAndPut()
    getytTopImages()

};

function getytTopImages() {
    var list = ytplist.getArray()
    var div = document.getElementById("ytImages")
    for (var i = div.childNodes.length - 1; i >= 0; i--) {
        div.removeChild(div.childNodes[i]);
    };

    var first = playing;
    var img = document.createElement("img")
    img.src = first.img;
    img.title = first.name + " - " + first.artist.name;
    img.style.width = "85px";
    img.style.height = "64px"
    img.setAttribute("onclick", "parseVideo('" + first.ytid + "', '" + first.mbid + "')");
    img.style.border = "2px solid gold"
    div.appendChild(img);

    for (var i = 0; i < list.length - 1 && i < 4; i++) {
        track = list[i];
        var img = document.createElement("img")
        img.src = track.img;
        img.title = track.name + " - " + track.artist.name;
        img.style.width = "85px";
        img.style.height = "64px"
        img.setAttribute("onclick", "parseVideo('" + track.ytid + "', '" + track.mbid + "')");
        div.appendChild(img);
    };
};

function addFirstVideo(track) {
    var video = track;

    cueVideoById(video);
    var artist = video.artist;
    artist.active = true
    artist.getAndPut();
    getytTopImages();
    buyButton(video)
}

function addVideo() {

    var video = ytplist.getArray().shift()
    playing = video;
    getNextPl();
    addVideoById(video)
    var artist = video.artist
    changeArtist(artist);
    buyButton(video);

}

function parseVideo(ytid, mbid) {
    var ytlist = ytplist.getArray()
    for (var i = ytlist.length - 1; i >= 0; i--) {
        if (ytlist[i]["ytid"] == ytid) {
            var video = ytlist.splice(i, 1)[0];
            playing = video;
            getNextPl();
        }
    };
    addVideoById(video)
    var artist = video.artist
    changeArtist(artist);
    buyButton(video)

}

function addVideoById(video) {

    player.loadVideoById(video["ytid"], 0, "large")

}

function cueVideoById(video) {

    player.cueVideoById(video["ytid"], 0, "large")

}

function onPlayerStateChange(event) {

    if (event.data == 0) {
        addVideo();
    }
}

function getNextPl() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/xhrGetNextPl', true);
    xhr.onload = function() {
        var response = JSON.parse(this.responseText);

        for (var i = 0; i < response.length; i++) {
            var r = response[i];
            plistpage=plistpage+1;
            var artist = new Artist();
            artist.name = r["artist"]["name"];
            artist.mbid = r["artist"]["mbid"];
            var track = new Track(r["name"], artist);
            track.searchVideo();
            getytTopImages();

        }
    };
    var query = {
        "type": type,
        "tag": activeTag,
        "artist":activeArtist,
        "page":plistpage
    }
    console.log(query);
    xhr.send(JSON.stringify(query));
}

function getTopArtist() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/getTopArtist', true);
    xhr.onload = function() {

        var list = document.getElementById("topArtists");
        var ul = document.createElement("ul");

        var response = JSON.parse(this.responseText)
        for (var i = 0; i < response.length; i++) {
            artist = response[i]
            var li = document.createElement("li")
            var a = document.createElement("a")
            a.href = "/artist/" + artist["mbid"]
            a.appendChild(document.createTextNode(artist["name"]))
            li.appendChild(a)
            ul.appendChild(li)

        };
        list.appendChild(ul)
        $(function() {
            $('#main-menu').smartmenus();
        });
    };
    xhr.send();
}

function getTopTags() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/getTopTags', true);
    xhr.onload = function() {
        console.log(this.responseText)
        var list = document.getElementById("topTags");
        var ul = document.createElement("ul");

        var response = JSON.parse(this.responseText)
        for (var i = 0; i < response.length; i++) {
            tag = response[i]
            console.log(tag);
            var li = document.createElement("li")
            var a = document.createElement("a")
            a.href = "/tag/" + tag["name"]
            a.appendChild(document.createTextNode(tag["name"]))
            li.appendChild(a)
            ul.appendChild(li)

        };
        list.appendChild(ul)
        $(function() {
            $('#main-menu').smartmenus();
        });
    };

    xhr.send();

}

function searchArtist() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/searchArtist', true);
    xhr.onload = function() {
        response = JSON.parse(this.responseText);
        console.log(response);
        if (response.length == 1) {
            window.location.replace("/artist/" + response[0]["mbid"]);
        } else {
            table = document.createElement("table")
            for (var i = 0; i < response.length; i++) {
                artist = response[i]
                var tr = document.createElement("tr");
                var td = document.createElement("td");
                var a = document.createElement("a")
                a.href = "/artist/" + artist["mbid"]
                a.appendChild(document.createTextNode(artist["name"] + ": "))
                td.appendChild(a)
                tr.appendChild(td)
                var td2 = document.createElement("td")
                td2.appendChild(document.createTextNode(artist["country"]))
                tr.appendChild(td2)
                table.appendChild(tr)

            };
            console.log(table.innerHTML);
            $.magnificPopup.open({
                items: {
                    src: '<div class="white-popup"><table>'+table.innerHTML+'</table></div>', // can be a HTML string, jQuery object, or CSS selector
                    type: 'inline'
                }
            });
        }

    };
    var artist = document.getElementById("searchInput").value;
    var query = {
        "name": artist
    }
    console.log(query);
    xhr.send(JSON.stringify(query));
}

function buyButton(track){
    var div = document.getElementById("buyButtons");

    for (var i = div.childNodes.length - 1; i >= 0; i--) {
        div.removeChild(div.childNodes[i])
    };

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/Buy7digital', true);
    xhr.onload = function() {
        response = JSON.parse(this.responseText);
        console.log(response);
        
        var div=document.getElementById("buyButtons")
        var iframe=document.createElement("iframe")
            iframe.src="https://instant.7digital.com/iframe.htm?trackid="+response+"&partnerid=3587&buttontext=Buy Track"
            iframe.setAttribute("seamless","seamless")
            iframe.setAttribute("frameborder","0")
            iframe.setAttribute("height","40")
            iframe.setAttribute("scrolling","no")
        div.appendChild(iframe)
    };
   
    xhr.send(JSON.stringify(track));

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/BuyAmazon', true);
    xhr.onload = function() {
        response = JSON.parse(this.responseText);
        console.log(response);
        
        var div=document.getElementById("buyButtons")
        
        div.appendChild(iframe)
    };
   
    xhr.send(JSON.stringify(track));
}
