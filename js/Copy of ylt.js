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
        
        track.active = true;
        var mbid=document.getElementById("accordion");
            mbid.setAttribute("value",track.artist.mbid)
        addFirstVideo(track)
    }
    if (!this.hasfive) {
        if (this.getArray().length >= 5) this.hasfive = true;
        getytTopImages(this)
    }
    getNextPl();
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
 

    this.getSimilar()
    this.getLogo()
    this.getData()
    artistCache.push(this)

};

Artist.prototype.getData=function() {
    var artist=this
    if (typeof this.info !== 'undefined' && typeof this.tags !== 'undefined' && artist.info != "" && artist.tags != ""){
        artist.putInfo();
        artist.putTags();
    }
    else{
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrArtistData', true);
        xhr.onload = function() {
            a=JSON.parse(this.responseText);
            artist.info = a["info"];
            artist.name=a["name"];
            artist.tags=a["tags"];
            artist.putInfo();
            artist.putTags();
        };
        var query = {
            "artist": artist.mbid
        };

        xhr.send(JSON.stringify(query));
    }
}



Artist.prototype.putInfo = function() {



    var p = document.getElementById("artistInfo");
    var txt = document.createTextNode(this.info);

    if(p.childNodes[0].data.trim() != txt.data.trim()){
        
    

    if (p.childNodes.length > 1) {
        p.removeChild(p.childNodes[1]);
    };
    p.appendChild(txt);
    }

    var p = document.getElementById("ArtistRadio");
    if (p.hasChildNodes()) {
        for (var i = p.childNodes.length - 1; i >= 0; i--) {
            p.removeChild(p.childNodes[i]);
        };
    }
    var a =document.createElement("a")
        a.href="/artist-radio/"+this.mbid;
        var txt=document.createTextNode("Play "+this.name+" Radio");
        a.appendChild(txt);
    p.appendChild(a)

}

Artist.prototype.getLogo = function() {
    if(this.logo !="" && typeof this.logo !== 'undefined' && this.logo!=null){
        this.putLogo()
    }
    else{
        var artist = this
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrLogo', true);
        xhr.onloadstart=function() {

            var div = document.getElementById("topLogo")
            if (div.hasChildNodes()) {
                for (var i = div.childNodes.length - 1; i >= 0; i--) {
                    div.removeChild(div.childNodes[i]);
                };
            }
            p=document.createElement("p")
            txt=document.createTextNode("Fetching logo....")
            p.appendChild(txt)
            div.appendChild(p)
            
        }
        xhr.onload = function() {
            // do something to response
            artist.logo = this.responseText
            artist.putLogo();
        };
        var query = {"artist":artist.mbid };
        xhr.send(JSON.stringify(query));
    }
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
    var query = {"artist":artist.mbid};
    xhr.send(JSON.stringify(query));

}

Artist.prototype.putLogo = function() {
    if (typeof this.logo==="undefined"){
        this.logo="None"
    }
    if (this.logo == "None") {
        this.logo = "http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|38|h|FFFFFF|_|" + this.name;
    }

    img=document.getElementById("logo")

    if (img != null){
        if (img.src==this.logo){
            return
        }
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
    
    if(this.similars.length>0){
        this.putSimilar();
    }
    else{
        var artist = this
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrSimilar', true);
        xhr.onload = function() {
            // do something to response
            var similars = JSON.parse(this.responseText);
            console.log(this.responseText)
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
        }
    
        var query = '{"artist":' + artist.mbid + '}';
        xhr.send(JSON.stringify(query));
    }
};

Artist.prototype.clearSimilar = function() {
    var table = document.getElementById("similarLogos")

    for (var i = table.rows.length - 1; i >= 0; i--) {
        table.deleteRow(i);
    }
}

Artist.prototype.putSimilar = function() {

    this.clearSimilar();
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
                    var img = document.createElement("img");
                    img.src = similar.logo;
                    img.id = similar.mbid
                    img.alt = similar.name
                    img.title = similar.name
                    img.style.height = "175px"
                    img.style.width = "235px"
                a.appendChild(img)
            div.appendChild(a)
                var text = document.createElement("div")
                    text.id = similar.name
                    text.setAttribute("class", "text")
                        var h5 = document.createElement("h5")
                        text.appendChild(h5.appendChild(document.createTextNode(similar.name)))
                    
            div.appendChild(text)
  
        tr.appendChild(div);
    table.appendChild(tr)

    };
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
    console.log(tipo)
    if (tipo == "tag") {
        url = '/xhrCreateTagPlayList';
        type="tag"
    } else if (tipo == "artist") {
        url = '/xhrCreateArtistPlayList';
        type="artist"
    }
    else if (tipo=="artist-radio"){
        url='/xhrCreateArtistRadio'
        type="artist-radio"
    }
    else if (tipo == "predefined") {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/xhrFrontVideos', true);
        xhr.onload = function() {
            // do something to response
            var response = JSON.parse(this.responseText);
            for (var i = 0; i < response.length; i++) {
                        
                var r = response[i];

                var artist = new Artist();
                artist.name = r["artist"]["name"];
                artist.mbid = r["artist"]["mbid"];
                artist.logo = r["artist"]["logo"];
                artist.similars = r["artist"]["similars"];
                artist.tags = r["artist"]["tags"];
                artist.info = r["artist"]["info"];

                var track = new Track(r["name"], artist);
                track.ytid = r["ytid"]
                track.img = r["img"]

                if (typeof track.ytid==="undefined"){
                    track.searchVideo()
                }
                else{
                    var ytlist = ytplist.getArray();
                    var isin = false;

                    if (track.ytid == " ") {
                        return;
                    }

                    if (ytlist.length == 0) {
                        ytplist.push(track);
                        isin = true
                    }

                    for (var j = 0; j < ytlist.length; j++) {

                        if (ytlist[j].ytid == track.ytid) {
                            isin = true;
                        }
                    };

                    if (!isin) {
                        ytplist.push(track);
                    }

                }
            };
        };
        xhr.send();
        return;
    };

    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, false);
    xhr.onload = function() {
        var response = JSON.parse(this.responseText);
        plistpage=11;
        var response2 = response["tracks"]
        
        if (tipo == "tag") {
            activeTag=data;
            session=response["session"]
            console.log(session)
            
        }
        if(tipo=="artist" || tipo=="artist-radio"){
            activeArtist=data
            session=response["session"]
            console.log(session)
        }
        
        console.log(response2)        
        for (var i = 0; i < response2.length; i++) {
            
            var r = response2[i];
            console.log("test response")
            console.log(r)
            var artist = new Artist();
            artist.name = r["artist"]["name"];
            artist.mbid = r["artist"]["mbid"];
            artist.logo = r["artist"]["logo"];
            artist.similars = r["artist"]["similars"];
            artist.tags = r["artist"]["tags"];
            artist.info = r["artist"]["info"];

            var track = new Track(r["name"], artist);
            track.ytid = r["ytid"]
            track.img = r["img"]

            if (typeof track.ytid==="undefined"){
                track.searchVideo()
            }
            else{
                var ytlist = ytplist.getArray();
                var isin = false;

                if (track.ytid == " ") {
                    return;
                }

                if (ytlist.length == 0) {
                    ytplist.push(track);
                    isin = true
                }

                for (var j = 0; j < ytlist.length; j++) {

                    if (ytlist[j].ytid == track.ytid) {
                        isin = true;
                    }
                };

                if (!isin) {
                    ytplist.push(track);
                }
            }

        };
        console.log(ytplist)
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
        response=response["tracks"]

        for (var i = 0; i < response.length; i++) {
            var r = response[i];

            plistpage=plistpage+1;
            var artist = new Artist();
            artist.name = r["artist"]["name"];
            artist.mbid = r["artist"]["mbid"];
            var track = new Track(r["name"], artist);
            var track = new Track(r["name"], artist);
            track.ytid = r["ytid"]
            track.img = r["img"]

            if (typeof track.ytid==="undefined"){
                track.searchVideo()
            }
            else{
                var ytlist = ytplist.getArray();
                var isin = false;

                if (track.ytid == " ") {
                    return;
                }

                if (ytlist.length == 0) {
                    ytplist.push(track);
                    isin = true
                }

                for (var j = 0; j < ytlist.length; j++) {

                    if (ytlist[j].ytid == track.ytid) {
                        isin = true;
                    }
                };

                if (!isin) {
                    ytplist.push(track);
                }
            }
            getytTopImages();

        }
    };
    var query = {
        "type": type,
        "tag": activeTag,
        "artist":activeArtist,
        "page":plistpage,
        "session":session
    }
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
        var list = document.getElementById("topTags");
        var ul = document.createElement("ul");

        var response = JSON.parse(this.responseText)
        for (var i = 0; i < response.length; i++) {
            tag = response[i]
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
    xhr.send(JSON.stringify(query));
}

function buyButton(track){
    var div = document.getElementById("buyrow");

    for (var i = div.childNodes.length - 1; i >= 0; i--) {
        div.removeChild(div.childNodes[i])
    };

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/BuyAmazon', false);
    xhr.onload = function() {
        var response = JSON.parse(this.responseText);
        
        var tr=document.getElementById("buyrow")
        var td=document.createElement("td")
        var a=document.createElement("a");
            a.href="http://www.amazon.es/gp/product/"+response+"/ref=as_li_tf_tl?ie=UTF8&camp=3626&creative=24790&creativeASIN="+response+"&linkCode=as2&tag=yolatu-21";
            var img=document.createElement("img")
                img.src="/js/amazon.gif"
            a.appendChild(img)
        td.appendChild(a)
        var img2=document.createElement("img")
            img2.src="http://ir-es.amazon-adsystem.com/e/ir?t=yolatu-21&l=as2&o=30&a="+response;
            img2.style.width="1"
            img2.style.height="1"
            img2.style.border="0"
            img.style="border:none !important; margin:0px !important;"
        td.appendChild(img2)
        tr.appendChild(td)
    };
    xhr.send(JSON.stringify(track));


    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/Buy7digital', false);
    xhr.onload = function() {
        var response = JSON.parse(this.responseText);
        
        var tr=document.getElementById("buyrow")
        var td=document.createElement("td")
        var iframe=document.createElement("iframe")
            iframe.src="https://instant.7digital.com/iframe.htm?trackid="+response+"&partnerid=3587&buttontext=Buy Track"
            iframe.setAttribute("seamless","seamless")
            iframe.setAttribute("frameborder","0")
            iframe.setAttribute("height","40")
            iframe.setAttribute("scrolling","no")
        td.appendChild(iframe)
        tr.appendChild(td)
    };
   
    xhr.send(JSON.stringify(track));

}   
   
    
