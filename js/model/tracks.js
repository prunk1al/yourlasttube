var viewModel=viewModel || {};

viewModel.trackList=ko.observableArray([]);
viewModel.firstVideo=ko.computed(function(){ return viewModel.trackList()[0]});
viewModel.helper=ko.computed(function(){
	return "<script>console.log("+viewModel.trackList()[0]+")</script>"
})






var Track=function(data){
    this.name = ko.observable(data.name);
    this.artist= ko.observable(data.artist);
   
    this.ytid= ko.computed(function(){
    	if(typeof data.ytid  !== "undefined"){
    		return data.ytid
    	}
    	else{
			var send=JSON.stringify({name: this.name(), 
								  artist: {name:this.artist().name()}});  		
    		$.post('/xhrGetVideo',send,function(data){
    			viewModel.trackList.push(this)
    			return data.ytid
    		});
    	}
    },this);
    
    this.img= ko.observable(function(){
    	return "http://img.youtube.com/vi/"+this.ytid+"/0.jpg"
    },this);
}



new Track({
	name:"",
	artist:"",
	ytid:" ",
	img:" "
})


