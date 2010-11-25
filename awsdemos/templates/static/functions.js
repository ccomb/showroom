/*
    functions for repoz.bfg demo manager
*/

function execute_command(url, app, params) {
    $('#loading_'+app).css("display", "block");
    $('#debug').text("loading...");
    $.get(url+'app='+app+'&params='+params, function(data){
        $('#debug').text("finished: "+data);
        $('#loading_'+app).css("display", "none");
    });
}

function on_valid_form(button) {
    $('#app_form_submit').attr('disabled', 'disabled');
    $('#loading').css('display', 'block');
    return true;
}

function update_app_form(url, app) {
    $("#app_form_dynamic").empty();
    if (app == ""){ return; }
    jQuery.getJSON(
        url+"/app_params?app="+app,
        function(data){
            params = data['params']
            for (param in params) {
                if (params[param]=='plugins') {
                    $("#app_form_dynamic").append(
                        '<br/>'+params[param]+':<textarea name="plugins"></textarea>'
                    );
                } else {
                  $("#app_form_dynamic").append(
                    '<br/>'+params[param].split('=')[0]+':<input '+(params[param].toLowerCase()=='password' && 'type="password"' || '')+'name="'+params[param].split('=')[0]+'" value="' + (params[param].split('=')[1] || '') + '"></input>'
                  );
                }
            }
        }
    );
    $("#app_form_dynamic").append(
        '<input id="app_form_submit" type="submit"'+
        'onclick="on_valid_form();"/>'
    )
}

