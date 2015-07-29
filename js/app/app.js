var viewModel=viewModel || {};



viewModel["setPlayList"]=function() {
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
	            viewModel.trackList.push(track);

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
	            viewModel.trackList.push(track);

	        }
	    });
	}
}();
   
ko.applyBindings(viewModel)





function searchArtist() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/searchArtist', true);
    xhr.onload = function() {
        response = JSON.parse(this.responseText);
        if (response.length == 1) {
            window.location.replace("/artist/" + response[0]["mbid"]);
        } else {
            table = document.createElement("table")
            for (var i = 0; i < response.length; i++) {
                artist = response[i]
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

    };
    var artist = document.getElementById("searchInput").value;
    var query = {
        "name": artist
    }
    xhr.send(JSON.stringify(query));
}
