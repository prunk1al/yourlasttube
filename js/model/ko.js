
var Track=function(data){
    var self=this;
    this.name = ko.observable(data.name);
    this.artist= ko.observable(data.artist);
    this.ytid=ko.observable("");
    
    
    this.img= ko.computed(function(){
    	return "http://img.youtube.com/vi/"+self.ytid()+"/0.jpg"
    },this);

    $.post('/xhrGetVideo',JSON.stringify({name: self.name(), 
                                  artist: {name:self.artist().name()}}),function(data){
                data=JSON.parse(data);
                ytid=data.ytid
                self.ytid(ytid);


            });

}

var Artist=function(data){
    var self=this;

    this.name= ko.observable(data.name);
    this.mbid= ko.observable(data.mbid);
    this.info= ko.observable(data.info);
    this.logo= ko.observable(data.logo);
    this.similars= ko.observableArray(data.similars);
    this.tags= ko.observableArray(data.tags);

    $.post('/xhrArtistData', JSON.stringify({"artist":self.mbid()}),function(data){
        var a=JSON.parse(data);
        self.info = a["info"];
        self.name=a["name"];
        self.tags=a["tags"];
    })

};



var t={imt:'',
    ytid:''}


var viewModel=function(){
        var self=this;

        this.trackList=ko.observableArray();
        this.currentVideo=ko.observable();
        this.topArtist=ko.observableArray();
        this.topTags=ko.observableArray();
        
        console.log(this.currentVideo())
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

        this.setPlayList=function() {
            var url =$(location).attr('href');

            url=url.split('/');
            console.log(url.length)
            if(url.length ===5){
                var type=url[3];
                var param=url[4];
                if (type==="artist"){
                    $.post("/xhrCreateArtistPlayList",JSON.stringify({data:param}),function(data){
                        data=JSON.parse(data);
                        for (i in data.tracks){
                        var artist=new Artist(data.tracks[i].artist);
                        data.tracks[i].artist=artist;
                        var track=new Track(data.tracks[i]);
                        self.trackList.push(track);

                        }
                    });
                }
            }
            else{
                $.getJSON("/xhrFrontVideos", function(data) { 
                    for (i in data){
                        var artist=new Artist(data[i].artist);
                        data[i].artist=artist;
                        var track=new Track(data[i]);
                        self.trackList.push(track);
                    }
                });
            };



            
        };

        this.nextVideo=function(event){
            if (event.data===0){
                self.changeCurrentVideo(self.trackList()[0])
            }
        }

        this.changeCurrentVideo=function(video){
            self.trackList.splice(self.trackList.indexOf(video),1);
            window.player.loadVideoById(video.ytid(), 0,"large");
            self.currentVideo(video)
            
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
                            console.log(newValue)
                             if ( newValue ) {
                                 subscription.dispose();
                                 // Just get this binding to fire again
                                 var video=viewModel.trackList()[0].ytid
                                if ( video() ==="" ) {
                                    var subscription2;
                                    subscription2 =  video.subscribe( function(newValue) {
                                        console.log(newValue)
                                         if ( newValue ) {
                                             subscription2.dispose();
                                             viewModel.currentVideo(viewModel.trackList()[0]);
                                             viewModel.trackList.splice(viewModel.trackList.indexOf(viewModel.currentVideo()),1);
                                             window.player = new YT.Player( element, {
                                                height: 320,
                                                width: 598,
                                                videoId:viewModel.currentVideo().ytid(),
                                                events: {
                                                    'onStateChange': viewModel.nextVideo
                                                }

                                                });
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
            console.log(valueAccessor)
        }
        
    }
    


ko.applyBindings(new viewModel())




