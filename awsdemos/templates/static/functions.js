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
                $("#app_form_dynamic").append(
                    '<br/>'+params[param]+':<input '+(params[param].toLowerCase()=='password' && 'type="password"' || '')+'name="'+params[param]+'"></input>'
                );
            }
            plugins = data['plugins'];
            if (plugins.length > 0) {
                $('#app_form_dynamic').append('PLUGINS'+
                    '<select id="app_form_dynamic_plugins" name="plugins" multiple="multiple" </select>'
                    )
                for (plugin in plugins) {
                    $("#app_form_dynamic_plugins").append(
                        '<option>'+plugins[plugin]+'</option>'
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

