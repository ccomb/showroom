/*
functions for repoz.bfg demo manager

*/

function execute_command(url, app, command){
    $('#loading_$app').innerHtml = '<img src="/static/images/loading.gif">';
    var result = $.getJSON(url+'app='+app+'&action='+command);
    $('#loading_$app').innerHtml = '';
}
