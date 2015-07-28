var viewModel=viewModel || {};

viewModel.topArtist=ko.observableArray([]);
viewModel.topTags=ko.observableArray([]);


$.getJSON("/getTopArtist", function(data) { 
    // Now use this data to update your view models, 
    // and Knockout will update your UI automatically 
    for (i in data){
    	viewModel.topArtist.push(data[i])
    }
});


$.getJSON("/getTopTags", function(data) { 
    // Now use this data to update your view models, 
    // and Knockout will update your UI automatically 
    for (i in data){
    	viewModel.topTags.push(data[i])
    }
});