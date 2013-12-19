
var ytplist= new Array();

function getArtistImage(artist){
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrArtistImage', true);
        xhr.onload = function () {
            // do something to response


            console.log(this.responseText);
            var body=document.getElementById("body")
            body.style.backgroundImage="url('"+this.responseText+"')"


            var loading=document.getElementById("loadingBackground")
            body.removeChild(loading)
        };
        var query='{"artist":'+artist+'}';
        console.log(query)
        xhr.send(JSON.stringify(query));
    }


function getBandLogo(artist){
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrLogo', true);
        xhr.onload = function () {
            // do something to response


            console.log(this.responseText);
            var img=document.getElementById("logo")
            img.src=this.responseText
            var loading=document.getElementById("loadingLogo")
            body.removeChild(loading)
        };
        var query='{"artist":'+artist+'}';
        console.log(query)
        xhr.send(JSON.stringify(query));
    
    }


function getSimilarLogo(artist, name){
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrLogo', true);
        xhr.onload = function () {
            // do something to response
            console.log(this.responseText);
            var image=this.responseText

            if (image=="None"){
                image="http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|38|h|FFFFFF|_|"+name;
            }
            var tr=document.getElementById("similar")
            var a=document.createElement("a");
                a.href="xhrArtist?mbid="+artist
            var img=document.createElement("img");
                img.src=image;
                img.id=artist
                img.alt=name
            a.appendChild(img)
            tr.appendChild(a);
            
        };
        var query='{"artist":'+artist+'}';
        console.log(query)
        xhr.send(JSON.stringify(query));
    
    }

function getAlbumImage(album){
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrAlbumImage', true);
        xhr.onload = function () {
            // do something to response
            console.log(this.responseText)

            var img=document.getElementById(album);
            img.src=this.responseText
            
        };
        var query='{"album":'+album+'}';
        console.log(query)
        xhr.send(JSON.stringify(query));
    
    }

function getAlbums(artist){
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrAlbums', true);
        xhr.onload = function () {
            // do something to response


            
            console.log(this.responseText);
            var albums=JSON.parse(this.responseText);

            var table=document.getElementById("album");
            var tr=document.createElement("tr");

            for (var i = albums.length - 1 ; i >= 0; i--) {
                album=albums[i]

                i++;//hacemos trampas para ajustar la cantidad de filas
                if(i%5 == 0 && i > 1 ){
                    table.appendChild(tr)
                    var tr=document.createElement("tr")
                }
                i--;//fin de las trampas


                console.log(table.getElementsByTagName("td").length)
                var td=document.createElement("td")
                var a=document.createElement("a");
                    a.href="xhrAlbum?mbid="+album["mbid"]
                var img=document.createElement("img");
                    img.id=album["mbid"]
                    img.alt=album["name"]
                    img.style.width="140px";
                var br=document.createElement("br")
                var text=document.createTextNode(album["name"].substring(0,20))
                a.appendChild(img)
                a.appendChild(br)
                a.appendChild(text)
                td.appendChild(a)
                tr.appendChild(td);
            };

            table.appendChild(tr);           


            for (var i = albums.length - 1; i >= 0; i--) {
                album=albums[i]
                getAlbumImage(album["mbid"])
            };
        };
        var query='{"artist":'+artist+'}';
        console.log(query)
        xhr.send(JSON.stringify(query));
    
    }

function getSimilar(artist){
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrSimilar', true);
        xhr.onload = function () {
            // do something to response


            console.log(this.responseText);
            var similars=JSON.parse(this.responseText);
            for (var i = similars.length - 1; i >= 0; i--) {
                similar=similars[i];

                getSimilarLogo(similar["mbid"],similar["name"])
            };
            


        };
        var query='{"artist":'+artist+'}';
        console.log("similar")
        xhr.send(JSON.stringify(query));
    
    };

function getTopArtists(){

     var xhr = new XMLHttpRequest();
        xhr.open('GET', '/xhrTopArtists', true);
        xhr.onload = function () {
            // do something to response


            console.log(this.responseText);
            var artists=JSON.parse(this.responseText);
            for (var i = 0; i <  artists.length ; i++) {
                artist=artists[i];

                getTopLogo(artist)
            };


        };
        xhr.send();
    
    };

function getTopLogo(artist){
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrLogo', true);
        xhr.onload = function () {
            // do something to response
            console.log(this.responseText);
            var image=this.responseText
            var name=artist["name"]

            if (image=="None"){
                image="http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|38|h|FFFFFF|_|"+name;
            }
            var tr=document.getElementById("logos");
                    var td =document.createElement("td");
                        var a=document.createElement("a");
                            a.href="xhrArtist?mbid="+artist["mbid"]
                            var img=document.createElement("img");
                                img.src=image;
                                img.id=artist["mbid"]
                                img.alt=name
                                img.style.width="85px";
                        a.appendChild(img)
                    td.appendChild(a)
                tr.appendChild(td)
            
            
        };
        var query='{"artist":'+artist["mbid"]+'}';
        console.log(query)
        xhr.send(JSON.stringify(query));

};


function getTopVideo(track){
     var xhr = new XMLHttpRequest();
        xhr.open('post', '/xhrGetVideo', true);
        xhr.onload = function () {
            // do something to response
            console.log(this.responseText);
            var j=JSON.parse(this.responseText);
            video={}
            video["ytid"]=j["video"]
            video["mbid"]=j["artist"]["mbid"]
            
            ytplist.push(video);
            /*
            var table=document.getElementById("songs");
                var tr=document.createElement("tr");
                        tr.setAttribute("class","trsong")
                    var td = document.createElement("td");
                        tr.setAttribute("class","tdsong")
                        var button=document.createElement("button");
                            button.setAttribute("onclick", "parseVideo('"+video["ytid"]+"','"+video["mbid"]+"')")
                            if(track["number"]){
                                var txt=document.createTextNode(track["number"]+" - "+track["name"]+" - "+ track["artist"]["name"])
                            }
                            else{
                                var txt=document.createTextNode(track["name"]+" - "+ track["artist"]["name"])
                            }
                        button.appendChild(txt);
                    td.appendChild(button);
                tr.appendChild(td);
            table.appendChild(tr);
            */

            
        };
        xhr.send(JSON.stringify(track));

};




function loadVideos(){
    var xhr = new XMLHttpRequest();
        xhr.open('GET', '/xhrFrontVideos', true);
        xhr.onload = function () {
            // do something to response
            console.log(this.responseText);
            var tracks=JSON.parse(this.responseText);
            for (var i = 0; i <  tracks.length ; i++) {
                track=tracks[i];

                getTopVideo(track)

            };
        };
        xhr.send();
};

function getAlbumTracks(album){
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrGetAlbumTracks', true);
        xhr.onload = function () {
            // do something to response
           console.log(this.responseText);
           var tracks=JSON.parse(this.responseText);
            
           

            for (var i = 0; i <  tracks.length ; i++) {
                
                track=tracks[i]
                data={}
                data["artist"]=track["artist"]["name"]
                data["name"]=track["name"]
                data["number"]=track["number"]
                getTopVideo(data)
               

            };
            console.log(track["artits"]);
            getArtistImage(track["artist"]["mbid"])
            getBandLogo(track["artist"]["mbid"])

        };
        var query={"album":album};
        console.log(query)
        xhr.send(JSON.stringify(query));
};

function getAlbumTracks2(album){
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrGetAlbumTracks', true);
        xhr.onload = function () {
            // do something to response
           console.log(this.responseText);
           var tracks=JSON.parse(this.responseText);
            
           var table=document.getElementById("tracks");
            var tr=document.createElement("tr");

            for (var i = 0; i <  tracks.length ; i++) {
                if (i%5==0 && i>0){
                    table.appendChild(tr)
                    var tr =document.createElement("tr")
                }
                track=tracks[i];
                console.log(track);
                var td=document.createElement("td")
                    var p=document.createElement("p");
                        p.id=track["mbid"]
                        var txt= document.createTextNode(track["name"])
                        p.appendChild(txt)
                    td.appendChild(p)
                tr.appendChild(td)

                getTrackVideo(track["mbid"])
                console.log(track["artits"]);
                getArtistImage(track["artist"])

            };

        };
        var query={"album":album};
        console.log(query)
        xhr.send(JSON.stringify(query));
};

function getTrackVideo(track){
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrGetTrackVideo', true);
        xhr.onload = function () {
            // do something to response
           console.log(this.responseText);
          var p=document.getElementById(track)
            var a=document.createElement("a")
                a.href="http://www.youtube.com/watch?v="+this.responseText
                a.setAttribute("rel","prettyPhoto[gallery1]")
                var img=document.createElement("img")
                    img.src="http://img.youtube.com/vi/"+this.responseText+"/0.jpg"
                    img.style.width="200px";
                a.appendChild(img);
            p.appendChild(a)

             $("a[rel^='prettyPhoto']").prettyPhoto();
        };
        var query={"track":track};
        console.log(query)
        xhr.send(JSON.stringify(query));
};


function changeArtist(mbid){
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrLogo', true);
        xhr.onload = function () {
            // do something to response
            console.log(this.responseText);
            var image=this.responseText
            

            if (image=="None"){
                image="http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|38|h|FFFFFF|_|"+name;
            }
            
          
            var img=document.getElementById("topLogo");
                    img.src=image
                    img.style.width="250px";
            
            
        };
        var query='{"artist":'+mbid+'}';
        console.log(query)
        xhr.send(JSON.stringify(query));

    getArtistInfo(mbid)
    getArtistTags(mbid)
    getSimilarFront(mbid);
    getytTopImages(ytplist)
};

function getytTopImages(ytlist){
    var div=document.getElementById("ytImages")
    for (var i =div.childNodes.length - 1; i >= 0; i--) {
       div.removeChild(div.childNodes[i])
    };

    for (var i = 0; i < ytlist.length; i++) {
        var img=document.createElement("img")
            img.src="http://img.youtube.com/vi/"+ytlist[i]["ytid"]+"/0.jpg"
            img.style.width="85px"
            img.setAttribute("onclick","parseVideo('"+ytlist[i]["ytid"]+"', '"+ ytlist[i]["mbid"]+"')")
        div.appendChild(img)
    };
}

function getArtistTags(mbid){
     var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrArtistTags', true);
        xhr.onload = function () {
            // do something to response


            console.log(this.responseText);
            var tags=JSON.parse(this.responseText)
            var tl=tags["tags"]
            var p=document.getElementById("artistTags");
            for (var i=tl.length - 1; i >= 0; i--) {
            console.log(tl[i])
                var a=document.createElement("a")
                    a.href=tl[i]
                    a.appendChild(document.createTextNode(tl[i]))
                p.appendChild(a)
                p.appendChild(document.createTextNode("    "))
            };


        };
        var query={"artist":mbid};
        console.log("artistInfo")
        xhr.send(JSON.stringify(query));
    
    };


function getArtistInfo(mbid){
     var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrArtistInfo', true);
        xhr.onload = function () {
            // do something to response


            console.log(this.responseText);
            var p=document.getElementById("artistInfo")
            if (p.childNodes.length>1){
                p.removeChild(p.childNodes[1]) 
            }  
            txt=document.createTextNode(this.responseText)
            p.appendChild(txt)
           


        };
        var query={"artist":mbid};
        console.log("artistInfo")
        xhr.send(JSON.stringify(query));
    
    };

function getSimilarFront(mbid){
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrSimilar', true);
        xhr.onload = function () {
            // do something to response


            console.log(this.responseText);
            var similars=JSON.parse(this.responseText);
            
            var table=document.getElementById("similarLogos")
            console.log(table.rows.length);

            for(var i=table.rows.length-1; i >=0; i--){
                table.deleteRow(i);
            }


            for (var i = similars.length - 1; i >= 0; i--) {
                similar=similars[i];

                getSimilarLogo(similar["mbid"],similar["name"])
            };
            


        };
        var query='{"artist":'+mbid+'}';
        console.log("similar")
        xhr.send(JSON.stringify(query));
    
    };
function getSimilarLogo(artist, name){
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrLogo', true);
        xhr.onload = function () {
            // do something to response
            console.log(this.responseText);
            var image=this.responseText

           
            if (image=="None"){
                image="http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|38|h|FFFFFF|_|"+name;
            }
            var table=document.getElementById("similarLogos")
            var tr=document.createElement("tr")
            var a=document.createElement("a");
                a.href="xhrArtist?mbid="+artist
            var img=document.createElement("img");
                img.src=image;
                img.id=artist
                img.alt=name
                img.style.width="200px"
            a.appendChild(img)
            tr.appendChild(a);
            table.appendChild(tr)
            
        };
        var query='{"artist":'+artist+'}';
        console.log(query)
        xhr.send(JSON.stringify(query));
    
    }


var player;
function onYouTubeIframeAPIReady() {
        player = new YT.Player('player', {
          height: '390',
          width: '425',
            events: {
                'onStateChange': onPlayerStateChange,
                "onReady": addVideo
            }
        });
 
}

function addVideo(){

    if(ytplist.length<=0){
        
        window.setTimeout(addVideo(),1000)
        return;
    }
    var video=ytplist.shift()
    console.log(video);
    addVideoById(video)
    
}
function parseVideo(ytid, mbid){
    for (var i =ytplist.length - 1; i >= 0; i--) {
       if(ytplist[i]["ytid"]==ytid){
        ytplist.splice(i,1)
       }
    };
    video={"ytid":ytid,"mbid":mbid}
    addVideoById(video)
}

function addVideoById(video){
    
    player.loadVideoById(video["ytid"], 0, "large")
    changeArtist(video["mbid"]);
}

function onPlayerStateChange(event) {

   if (event.data==0){
    addVideo();
   }
}

function createIframe(){
    // 2. This code loads the IFrame Player API code asynchronously.
      var tag = document.createElement('script');

      tag.src = "https://www.youtube.com/iframe_api";
      var firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

}

