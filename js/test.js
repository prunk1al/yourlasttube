
var ytplist= new Array();

function getArtistImage(artist){
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrArtist', true);
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
            var table=document.getElementById("logos");
                var tr=document.createElement("tr");
                    var td =document.createElement("td");
                        var a=document.createElement("a");
                            a.href="xhrArtist?mbid="+artist["mbid"]
                            var img=document.createElement("img");
                                img.src=image;
                                img.id=artist["mbid"]
                                img.alt=name
                        a.appendChild(img)
                    td.appendChild(a)
                tr.appendChild(td)
            table.appendChild(tr)
            
            
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
            video=this.responseText
            //jQuery("#player").tubeplayer("cue", video);
            ytplist.push(video);
            
            var table=document.getElementById("songs");
                var tr=document.createElement("tr");
                    var td = document.createElement("td");
                        var button=document.createElement("button");
                            button.setAttribute("onclick", "addVideoById('"+video+"')")
                            var txt=document.createTextNode(track["name"]+" - "+ track["artist"])

                        button.appendChild(txt);
                    td.appendChild(button);
                tr.appendChild(td);
            table.appendChild(tr);


            
        };
        var query='{"track":'+track["name"]+',"artist":'+track["artist"]+'}';
        console.log(query)
        xhr.send(JSON.stringify(query));

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


var ytplayer;
function onYouTubePlayerReady(playerId) {
      ytplayer = document.getElementById("myytplayer");
      ytplayer.addEventListener("onStateChange", "onytplayerStateChange");
      addVideo(ytplayer)
    }

function addVideo(){
    var player=document.getElementById("myytplayer")

    player.loadVideoById(ytplist.shift())
}
function addVideoById(video){
    var player=document.getElementById("myytplayer")
    player.loadVideoById(video)
}

function onytplayerStateChange(newState) {
   if (newState==0){
    addVideo();
   }
}

