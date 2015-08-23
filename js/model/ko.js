
var Track=function(data){
    var self=this;
    this.name = ko.observable(data.name);
    this.artist= ko.observable(data.artist);
    this.ytid=ko.observable("");
    this.artistName=ko.computed(function(){
        return self.artist().name()
    })
    
    this.img= ko.computed(function(){
    	return "http://img.youtube.com/vi/"+self.ytid()+"/0.jpg"
    },this);


    this.init=function(){
        this.initVideos();
    }

    this.initVideos=function(){
        var data=localStorage.getItem(self.name()+"-" +self.artist().name());
        if(data){ 
            console.log("loaded from local video")       
            data=JSON.parse(data)
            self.updateVideo(data)
        }
        else{
            console.log("loaded from webservice video")
            self.getAsyncVideo()
        }



    };

     $.post('/xhrGetVideo',JSON.stringify({name: self.name(), 
                                          artist: {name:self.artist().name()}}),function(data){
                        data=JSON.parse(data);
                        ytid=data.ytid
                        //localStorage.setItem(self.name()+"-"+ self.artist().name(), JSON.stringify(ytid))
                        //self.updateVideo(ytid);
                        self.ytid(ytid)

            });

/*
    this.updateVideo=function(data){
        self.ytid(data)
    }

    this.getAsyncVideo=function(){
            
    }

    this.init()
*/
}

var Artist=function(data){
    var self=this;

    this.name= ko.observable(data.name);
    this.mbid= ko.observable(data.mbid);
    this.info= ko.observable(data.info);
    this.logo= ko.observable(data.logo)
    this.similars= ko.observableArray([]);
    this.tags= ko.observableArray(data.tags);

    this.isOpen = ko.observable(false);
    this.text = ko.computed(function(){return self.info()})
    //this.width=ko.observable();

     this.popupInfo=function(){
         this.isOpen(true);  
      //   this.width(400);
        }




    this.init=function(){
        this.initData();
        //this.initLogo();
        this.initSimilars();
    };

    

    this.initData=function(){
        var data=localStorage.getItem(self.mbid()+"Data");
        if(data){
        
            data=JSON.parse(data)
            self.updateData(data)
        }
        else{
        
            self.getAsyncData()
        }
    
    };


    this.initLogo=function(){
        var data=localStorage.getItem(self.mbid()+"Logo");
        if(data){
            console.log("loaded from local logo")
            data=JSON.parse(data)
            console.log(data)
            self.updateLogo(data)
        }
        else{
            console.log("loaded from webservice logo")
            self.getAsyncLogo()
        }
    
    };

     this.initSimilars=function(){
        var data=localStorage.getItem(self.mbid()+"Similars");
        if(data){
            console.log("loaded from local similars")
            data=JSON.parse(data)
            self.updateSimilars(data)
        }
        else{
            console.log("loaded from webservice similars")
            self.getAsyncSimilars()
        }
    
    };


    this.updateData=function(data){
        self.info(data["info"]);
        self.name(data["name"]);
        self.tags(data["tags"]);
    };

    this.updateLogo=function(logo){
        self.logo(logo);
    }

    this.updateSimilars=function(similars){
        self.similars(similars);
    }

    this.getAsyncData=function(){
        var test= $.post('/xhrArtistData', JSON.stringify({"artist":self.mbid()}),function(data){
            var data=JSON.parse(data);
            self.updateData(data)

            localStorage.setItem(self.mbid()+"Data",JSON.stringify(data));
        })
        localStorage.setItem("pruebas",test)
    }

    this.getAsyncLogo=function(){

        $.post('/xhrLogo', JSON.stringify({"artist":self.mbid()}),function(data){
            var data=JSON.parse(data);
            console.log(data)
            self.updateLogo(data)
            if (data!=''){
                localStorage.setItem(self.mbid()+"Logo",JSON.stringify(data));
            }
            $("#loadingLogo").hide();
            
        })

   }

   this.getAsyncSimilars=function(){
        $.post('/xhrSimilar',JSON.stringify({"artist":self.mbid()}),function(data){
            var data=JSON.parse(data)

            self.similars(data);
            localStorage.setItem(self.mbid()+"Similars",JSON.stringify(data));
        })
   }

    this.loadLogo=function(){
        
        self.initLogo();
        return self.logo()
    };

    this.loadSimilars=function(){
        
        self.initSimilars();
        return self.similars()
    };


};



var viewModel=function(){
        var self=this;

        this.trackList=ko.observableArray();
        this.currentVideo=ko.observable({img:"",artist:""});
        this.topArtist=ko.observableArray();
        this.topTags=ko.observableArray();
        this.session=ko.observable();
       



        this.init=function(){
            new self.topMenu();
            self.setPlayList();
        };

       

        this.topMenu=function(){

            this.getTopArtist=function(){$.getJSON("/getTopArtist", function(data) { 
                // Now use this data to update your view models, 
                // and Knockout will update your UI automatically 
                for (i in data){
                    self.topArtist.push(data[i])
                }
            })};

            this.getTopTags=function(){$.getJSON("/getTopTags", function(data) { 
                // Now use this data to update your view models, 
                // and Knockout will update your UI automatically 
                for (i in data){
                    self.topTags.push(data[i])
                }
            })};

            this.init=function(){
                this.getTopArtist();
                this.getTopTags();
            };

            this.init()

        };

        this.addTrack=function(track){
             var artist=new Artist(track.artist);
                track.artist=artist;
                           
            var track=new Track(track);
                self.trackList.push(track);
        }

        this.setPlayList=function() {
            var url =$(location).attr('href');

            url=url.split('/');
            if(url.length ===5){
                var type=url[3];
                var param=url[4];
                if (type==="artist"){
                    $.post("/xhrCreateArtistPlayList",JSON.stringify({data:param}),function(data){
                        data=JSON.parse(data);
                        self.session(data.session)
                        for (i in data.tracks){
                           self.addTrack(data.tracks[i])
                        }
                    });
                }
                else{
                    if (type==="tag"){
                        $.post("/xhrCreateTagPlayList",JSON.stringify({data:param}),function(data){
                            data=JSON.parse(data);

                            if (data==='Genre not in Echonest'){
                                $.magnificPopup.open({
                                    items: {
                                        src: '<div class="white-popup"><p>'+data+'</p></div>', // can be a HTML string, jQuery object, or CSS selector
                                        type: 'inline'
                                    }
                                });
                                return;
                            }
                            self.session(data.session)
                            for (i in data.tracks){
                               self.addTrack(data.tracks[i])
                            }
                        });
                    }
                    else{
                        if (type==="artist-radio"){
                            $.post("/xhrCreateArtistRadio",JSON.stringify({data:param}),function(data){
                                data=JSON.parse(data);
                                self.session(data.session)
                                for (i in data.tracks){
                                    self.addTrack(data.tracks[i])
                                }
                            });
                        }
                    }
                }
            }
            else{
                $.getJSON("/xhrFrontVideos", function(data) { 
                    for (i in data){
                        self.addTrack(data[i])
                    }
                });
            };



            
        };

        this.getNextTrack=function(){
            var query = {
                "session":self.session()
            }
            $.post("/xhrGetNextPl",JSON.stringify(query),function(data){
                    data=JSON.parse(data);
                    var artist=new Artist(data.tracks[0].artist);
                        data.tracks[0].artist=artist;
                            
                    var track=new Track(data.tracks[0]);
                        self.trackList.push(track);

                 }
            );
        }

        var hasplayed=false;       

        this.youtube={
            

            nextVideo:function(event){
                if (event.data===1 && !hasplayed){
                    console.log("playing")
                    hasplayed=true;
                };
                if (event.data===0){
                    hasplayed=false;
                    self.youtube.changeCurrentVideo(self.trackList()[0])
                    self.getNextTrack()
                    
                };
            },

            changeCurrentVideo:function(video){
                self.trackList.splice(self.trackList.indexOf(video),1);
                window.player.loadVideoById(video.ytid(), 0,"large");
                self.getNextTrack()
                self.currentVideo(video)
                video.artist().init();
                
            },

            loadplayer:function(){
                self.currentVideo(self.trackList()[0]);
                self.currentVideo().artist().init();
                console.log(self.currentVideo())
                self.trackList.splice(self.trackList.indexOf(self.currentVideo()),1);
                    window.player = new YT.Player( "player", {
                        height: 320,
                        width: 598,
                        videoId:self.currentVideo().ytid(),
                        events: {
                                'onStateChange': self.youtube.nextVideo
                                }

                        });
            }
        },



 this.searchArtist=function(data) {

    var artist = $(data)[0][0].value;

     var query = {
        "name": artist
        }

    $.post('/searchArtist',JSON.stringify(query),function(data){
            data= JSON.parse(data);
            if (data.length == 1) {
                window.location.replace("/artist/" + data[0]["mbid"]);
            } else {
                table = document.createElement("table")
                for (var i = 0; i < data.length; i++) {
                    artist = data[i]
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
        });

    }






this.init()
}


ko.bindingHandlers['player'] = {
        init: function(element, valueAccessor, allBindings, viewModel, bindingContext) {
            // Check if global script and function is declared.
            if ( !document.getElementById('playerScript') ) {
                // Create script
                var tag = document.createElement('script');
                tag.src = "https://www.youtube.com/iframe_api";
                var playerDiv = document.getElementById('player');
                var firstScriptTag = document.getElementsByTagName('script')[0];
                firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

                // Create global function that their API calls back
                window.playerReady = ko.observable(false);
                window.onYouTubeIframeAPIReady = function() {
                    window.playerReady(true);
                    
                     if ( viewModel.trackList().length===0 ) {
                        // YT hasn't invoked global callback.  Subscribe to update
                        var subscription;
                        subscription = viewModel.trackList.subscribe( function(newValue) {
                             if ( newValue ) {
                                 subscription.dispose();
                                 // Just get this binding to fire again
                                 var video=viewModel.trackList()[0].ytid
                                if ( video() ==="" ) {
                                    var subscription2;
                                    subscription2 =  video.subscribe( function(newValue) {
                                         if ( newValue ) {
                                             subscription2.dispose();
                                             viewModel.youtube.loadplayer();
                                        }
                                    });
                                }
                             }
                        });
                    }
                    else{
                        viewModel.currentVideo(viewModel.trackList()[0]);
                        viewModel.trackList.splice(viewModel.trackList.indexOf(viewModel.currentVideo()),1);
                         window.player = new YT.Player( element, {
                            height: 320,
                            width: 598,
                            videoId:viewModel.currentVideo().ytid()
                            });
                    }
                };
            }
        }
        
    }


ko.bindingHandlers.accordion = {
    init: function(element, valueAccessor) {
        var options = valueAccessor() || {};
        setTimeout(function() {
            $(element).accordion(options);
        }, 0);
        
        //handle disposal (if KO removes by the template binding)
          ko.utils.domNodeDisposal.addDisposeCallback(element, function(){
              $(element).accordion("destroy");
          });
    },

}    


ko.applyBindings(new viewModel())
