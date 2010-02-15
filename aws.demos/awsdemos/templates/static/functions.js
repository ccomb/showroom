/*
    functions for repoz.bfg demo manager
*/

function execute_command(url, app, command){
    $('#loading_'+app).css("display", "block");
    var result = $.getJSON(url+'app='+app+'&action='+command);
    $('#loading_'+app).css("display", "none");
    return result;
}
