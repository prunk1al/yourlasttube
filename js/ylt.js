function EventedArray(handler) {
   this.stack = [];
   this.isfirst=true;
   this.hasfive=false;
   this.mutationHandler = handler || function() {};
   this.setHandler = function(f) {
      this.mutationHandler = f;
   };
   this.callHandler = function() { 
      if(typeof this.mutationHandler === 'function') {
         this.mutationHandler();
      }
   };
   this.push = function(obj) {
      this.stack.push(obj);
      this.callHandler();
   };
   this.pop = function() {
      //this.callHandler();
      return this.stack.pop();
   };
   this.getArray = function() {
      return this.stack;
   }
}

var handler = function() {
    if (this.isfirst){
        this.isfirst=false;
        var track=this.pop()
        addFirstVideo(track)
    }
    if (!this.hasfive){
        if(this.getArray().length >=5) this.hasfive=true;
        getytTopImages(this)
    }  
};


var ytplist= new EventedArray();
    ytplist.setHandler(handler)
var player;
var artistCache=new Array()


function Artist(){
    this.name="";
    this.mbid="";
    this.info="";
    this.logo="";
    this.similars=new Array();
    this.tags=new Array();
    artistCache.push(this)
};



Artist.prototype.getAll=function(nombre,id){
    for (var i = 0; i < artistCache.length; i++) {
        if(artistCache[i].mbid==id){
            var x=artistCache[i]
            this.name=x.name;
            this.mbid=x.mbid;
            this.info=x.info;
            this.logo=x.logo;
            this.similars=x.similars;
            this.tags=x.tags;
            return;
        }
    };
   
    this.name=nombre;
    this.mbid=id;
    
    
    this.getInfo()
    this.getTags()
    this.getLogo()
    this.getSimilar()
    
};

Artist.prototype.getInfo=function(){
    var artist=this
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrArtistInfo', true);
        xhr.onload = function () {
            artist.info=this.responseText;
 
        };
        var query={"artist":artist.mbid};

        xhr.send(JSON.stringify(query));

}

Artist.prototype.putInfo=function(){
     var p=document.getElementById("artistInfo");
        if (p.childNodes.length>1){
            p.removeChild(p.childNodes[1]); 
        };  
        txt=document.createTextNode(this.info);
        p.appendChild(txt);
}

Artist.prototype.getLogo=function(){
    var artist=this
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrLogo', true);
        xhr.onload = function () {
            // do something to response
            artist.logo=this.responseText
            
        };
        var query='{"artist":'+artist.mbid+'}';
        xhr.send(JSON.stringify(query));
    
    }

Artist.prototype.putLogo=function(){
    if (this.logo==""){
        this.logo="http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|38|h|FFFFFF|_|"+this.name;
    }
    var div=document.getElementById("topLogo")
        if(div.hasChildNodes()){
            for (var i =div.childNodes.length - 1; i >= 0; i--) {
              div.removeChild(div.childNodes[i])
            };
        }
    var a = document.createElement("a")
        a.href="/artist/"+this.mbid
    var img=document.createElement("img");
            img.src=this.logo
           // img.setAttribute("onclick","setPlayList('artist','"+mbid+"')")
            img.style.width="250px";
            img.title=this.name
    
    a.appendChild(img)
    div.appendChild(a)

}

Artist.prototype.getSimilar=function(){
    var artist=this
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrSimilar', true);
        xhr.onload = function () {
            // do something to response
            var similars=JSON.parse(this.responseText);
            for (var i = similars.length - 1; i >= 0; i--) {
                similar=new Artist()
                similar.name=similars[i].name;
                similar.mbid=similars[i].mbid;
                similar.getLogo()
                artist.similars.push(similar)
            };
            
        };
        var query='{"artist":'+artist.mbid+'}';
        xhr.send(JSON.stringify(query));
    
    };



Artist.prototype.putSimilar=function(){

            var table=document.getElementById("similarLogos")

            for(var i=table.rows.length-1; i >=0; i--){
                table.deleteRow(i);
            }
       
        for (var i =this.similars.length - 1; i >= 0; i--) {
            var similar=this.similars[i];
            
            if (similar.logo=="None"){
                similar.logo="http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|38|h|FFFFFF|_|"+similar.name;
            }
          
            var tr=document.createElement("tr")
            var a=document.createElement("a")
                a.href="/artist/"+similar.mbid
            var img=document.createElement("img");
                img.src=similar.logo;
                img.id=similar.mbid
                img.alt=similar.name
                img.title=similar.name
                img.style.width="150px"
                //img.setAttribute("onclick", "setPlayList('artist','"+artist+"')")
                a.appendChild(img)
            tr.appendChild(a);
            table.appendChild(tr)

        };  
   
    };

Artist.prototype.getTags=function(){
    var artist=this
    var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrArtistTags', true);
        xhr.onload = function () {
            // do something to response
            var response=JSON.parse(this.responseText)
            var tags=response["tags"]
            
            for (var i=tags.length - 1; i >= 0; i--) {
                artist.tags.push(tags[i])
            };
        };
        var query={"artist":artist.mbid};
        xhr.send(JSON.stringify(query));

}

Artist.prototype.putTags=function(){
    
            
            var p=document.getElementById("artistTags");

            for (var i =p.childNodes.length - 1; i >= 0; i--) {
               p.removeChild(p.childNodes[i])
            };
            for (var i=this.tags.length - 1; i >= 0; i--) {
                var a=document.createElement("a")
                    a.appendChild(document.createTextNode(this.tags[i]))
                    a.href="/tag/"+this.tags[i]
                p.appendChild(a)
                p.appendChild(document.createTextNode("    "))
            };
        
}





function Track(nombre,artista){
     this.name=nombre
     this.artist=artista
     this.ytid=""
     this.img=""
}


Track.prototype.searchVideo = function() {
    var track=this
    var xhr = new XMLHttpRequest();
        xhr.open('post', '/xhrGetVideo', true);
        xhr.onload = function () {
            // do something to response
            var response=JSON.parse(this.responseText);
            track.img=response.img
            track.ytid=response.ytid 
            ytplist.push(track)
            
        };
        xhr.send(JSON.stringify(this));
};

           
function setPlayList(tipo,data){

    if (tipo=="tag"){
        url='/xhrTagPlayList';
    }
    else if (tipo=="artist"){
        url='/xhrArtistPlayList';
    }
    else if(tipo=="predefined"){
        loadVideos();
        return;
    };

    var xhr = new XMLHttpRequest();
        xhr.open('POST', url, false);
        xhr.onload = function () {
            var response=JSON.parse(this.responseText);
            if(tipo=="artist"){
                meta=document.getElementById("desc");
                    meta.content=response[0]["artist"]["name"]+" Playlist";
            }
            for (var i = 0; i <  response.length ; i++) {
                var r=response[i];

                var artist=new Artist();
                    artist.getAll(r["artist"]["name"],r["artist"]["mbid"])
                var track=new Track(r["name"],artist);
                    track.searchVideo();
            };
        };
        var query={"data":data};
        xhr.send(JSON.stringify(query));
    };

function loadVideos(){
    var xhr = new XMLHttpRequest();
        xhr.open('GET', '/xhrFrontVideos', true);
        xhr.onload = function () {
            // do something to response
            var tracks=JSON.parse(this.responseText);
            for (var i = 0; i <  tracks.length ; i++) {
                track=tracks[i];

                getTopVideo(track)

            };
        };
        xhr.send();
};


function changeArtist(artist){

    console.log("Pintando");
    console.log(artist);
    artist.putInfo();
    artist.putLogo();
    artist.putSimilar();
    artist.putTags();
    getytTopImages(ytplist)
};





function getytTopImages(ytlist){
    list=ytlist.getArray()
    var div=document.getElementById("ytImages")
    for (var i =div.childNodes.length - 1; i >= 0; i--) {
       div.removeChild(div.childNodes[i]);
    };
   

    for (var i = 0; i < list.length && i<5 ; i++) {
        track=list[i];
        var img=document.createElement("img")
            img.src=track.img;
            img.title=track.name+" - "+ track.artist.name;
            img.style.width="85px";
            img.style.height="64px"
            img.setAttribute("onclick","parseVideo('"+track.ytid+"', '"+ track.mbid+"')");
        div.appendChild(img);
    };
};





function addFirstVideo(track){
    var video=track

    cueVideoById(video)
    var artist=video.artist
    changeArtist(artist);
}
function addVideo(){
    
    var video=ytplist.getArray().shift()
    addVideoById(video)
    var artist=video.artist
    changeArtist(artist);
    
}
function parseVideo(ytid, mbid){
    var ytlist=ytplist.getArray()
    for (var i =ytlist.length - 1; i >= 0; i--) {
       if(ytlist[i]["ytid"]==ytid){
        var video=ytlist.splice(i,1)[0]
       }
    };
    addVideoById(video)
    var artist=video.artist
    changeArtist(artist);
    
}

function addVideoById(video){
    
    player.loadVideoById(video["ytid"], 0, "large")
    
}

function cueVideoById(video){
    
    player.cueVideoById(video["ytid"], 0, "large")

}


function onPlayerStateChange(event) {

   if (event.data==0){
    addVideo();
   }
}



