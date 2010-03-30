/*
    functions for repoz.bfg demo manager
*/

function execute_command(url, app, params){
    $('#loading_'+app).css("display", "block");
    $('#debug').text("loading...");
    $.get(url+'app='+app+'&params='+params, function(data){
        $('#debug').text("finished: "+data);
        $('#loading_'+app).css("display", "none");
    });
}

function on_valid_form(button){
    $('#app_form_submit').attr('disabled', 'disabled');
    $('#loading').css('display', 'block');
    return true;
}

function update_app_form(app){
    params = jQuery.getJSON("/app_params?app="+app);
    $("#app_form_dynamic").empty();
    for (param in params){
        $("#app_form_dynamic").append('<input name="'+param+'"></input>');
    }
}
