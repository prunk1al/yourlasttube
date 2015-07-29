var viewModel=viewModel || {};

viewModel.trackList=ko.observableArray([]);
viewModel.currentVideo=ko.observable();
viewModel.loadVideo=function(){
    addVideoById(this.ytid())
    viewModel.currentVideo(this);
    viewModel.trackList.splice(viewModel.trackList.indexOf(this),1)
}






var Track=function(data){
    var self=this;
    this.name = ko.observable(data.name);
    this.artist= ko.observable(data.artist);
    this.ytid=ko.observable();
    
    
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



