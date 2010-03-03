/*
    functions for repoz.bfg demo manager
*/

function execute_params(url, app, params){
    $('#loading_'+app).css("display", "block");
    $('#debug').text("loading...");
    $.get(url+'app='+app+'&action='+params, function(data){
        $('#debug').text("finished: "+data);
        $('#loading_'+app).css("display", "none");
    });
}
