var viewModel=viewModel || {};


var Artist=function(data){
    this.name= ko.observable(data.name);
    this.mbid= ko.observable(data.mbid);
    this.info= ko.observable(data.info);
    this.logo= ko.observable(data.logo);
    this.similars= ko.observableArray(data.similars);
    this.tags= ko.observableArray(data.tags);
};

new Artist({
	name : "",
    mbid : "",
    info : "",
    logo : "",
    similars : new Array(),
    tags : new Array()
    })



getArtistData=function(mbid) {
    
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/xhrArtistData', true);
        xhr.onload = function() {
            var a=JSON.parse(this.responseText);
            info = a["info"];
            name=a["name"];
            tags=a["tags"];

            putArtistInfo(info);
            putArtistRadio(name, mbid);
            putArtistTags(tags);
        };
        var query = {
            "artist": mbid
        };

        xhr.send(JSON.stringify(query));
    //};
};