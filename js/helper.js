
function initflip(){
	var typelist=localStorage.getItem("yourlastube-typelist")
	if(!typelist){
		console.log(typelist)
		typelist=$("#flip-1").val();
		localStorage.setItem("yourlastube-typelist",typelist)
	}
	else{
		$("#flip-1").val(typelist)
	}
}

initflip();

$("#flip-1").change(function(data){
	console.log(this.value)
	localStorage.setItem("yourlastube-typelist",this.value)
})