



function setPlayList() {

    $.getJSON("/xhrFrontVideos", function(data) { 
        for (i in data){
            var artist=new Artist(data[i].artist);
            data[i].artist=artist;
            var track=new Track(data[i])
            viewModel.trackList.push(track)
        }
    });
};
   
ko.applyBindings(viewModel)



