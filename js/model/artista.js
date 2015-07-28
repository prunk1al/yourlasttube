function Artist() {
    this.name = "";
    this.mbid = "";
    this.info = "";
    this.logo = "";
    this.similars = new Array();
    this.tags = new Array();
    this.active = false;

};

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