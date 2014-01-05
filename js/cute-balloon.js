/*
 * Cute Balloon script 
 * powered by jQuery (http://www.jquery.com)
 * 
 * written by Daniel Ceillan (http://dcin.com.ar/daniel_ceillan.pdf)
 *
 */

function build_balloon(clase, content)
{
	return '<table class="cute-balloon cute-balloon-' + clase + '" border="0" cellpadding="0" cellspacing="0"><tr><td ><span class="noroeste"></span></td><td class="norte"></td><td><span class="noreste"></span></td></tr><tr><td class="oeste"></td><td class="content">'  + content + '</td><td class="este"></td></tr><tr><td ><span class="suroeste"></span></td><td class="sur"><span class="pso"></span></td><td ><span class="sureste"></span></td></tr></table>';
}

var tipo_sugeribles = Array();

//here you can define various styles to use in the same page
//the index is de class that define the group of elements
tipo_sugeribles['yellow'] = {
default_direccion:'ne',
ajuste_x:-40,
ajuste_y:5,
};

tipo_sugeribles['gray'] = {
default_direccion:'e',
ajuste_x:4,
ajuste_y:-54,
};

function make_cute_balloon(puntero, x, y)
{
    var texto = puntero.attr('tag');
    
    var clase = puntero.attr('clase');
    
    var la_url = puntero.attr('href');
    
    var top = y;
    
    var left = x;
    
    if(clase)
    {
        var default_direccion = tipo_sugeribles[clase]['default_direccion'];
        x += tipo_sugeribles[clase]['ajuste_x'];
        y += tipo_sugeribles[clase]['ajuste_y'];
    }
    
    //remove the preloads if exists
    $("table.cute-balloon").remove();
    
    $("body").append(build_balloon(clase,texto));
    
    puntero_a_tabla = $("table.cute-balloon");
    
    var altura = puntero_a_tabla.height();
    
    var ancho = puntero_a_tabla.width();
    
    //verificar si no me salgo de la pantalla, si me salgo corrijo la dirección del globito. 

    switch(default_direccion)
    {
        case 'ne':
            top = y - altura;
            left = x;
        break;
        case 'e':
            top = y;
        break;
        case 'o':
        break;
        case 'no':
        break;
    }
    
    puntero_a_tabla.fadeOut();
    
    puntero_a_tabla
    .css("top", top + "px")
    .css("left", left + "px");
    
    puntero_a_tabla.fadeIn("slow");
    
    if(la_url)
    {
        puntero_a_content = $("table.cute-balloon td.content");
        /**/
        $.ajax({
            url:  la_url,
            success: function(data) 
            {
                puntero_a_content.html(data);
            }
        });
         /**/
    }
    
    //here you can use the event you like. Mouseout, click, mouseover or a close button.
    puntero_a_tabla.click(function(e)
    {
        $(this).toggle('slow', function(){
            $(this).remove()
            });
    });
}

function cute_balloon_ignite()
{
	//you can call this function either to start or restart the cute balloon
    $("a.cute-balloon").unbind();
    $("a.cute-balloon").click(function(e)
    {
        make_cute_balloon($(this), e.pageX, e.pageY);
        e.preventDefault();
    });
    
    //this pre-load the images 
    var capa_precarga = '<div>' + 
    build_balloon('yellow', 'amarillo!!') + 
    build_balloon('gray', 'griss!!') + 
    '</div>';
    
    $("body").append(capa_precarga);
    
    //~ $("table.cute-balloon")
    //~ .css("top", "10px")
    //~ .css("left", "10px")
    //~ .fadeIn("slow");
    
}

// starting the script on page load
$(document).ready(function(){
    cute_balloon_ignite();
});
