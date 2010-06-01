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

function update_app_form(url, app){
    $("#app_form_dynamic").empty();
    if (app !=""){
        jQuery.getJSON(
            url+"/app_params?app="+app,
            function(data){
                for (param in data){
                    $("#app_form_dynamic").append(
                        '<br/>'+data[param]+':<input name="'+data[param]+'"></input>'
                    );
                }
            }
        ); // makes me sad
        jQuery.getJSON(
            url+"/app_plugins?app="+app,
            function(data){
                if (data.length > 0){
                    $('#app_form_dynamic').append(
                        '<select id="app_form_dynamic_plugins" name="plugins" multiple="multiple" </select>'
                        )
                    for (plugin in data){
                        $("#app_form_dynamic_plugins").append(
                            '<option>'+data[plugin]+'</option>'
                        );
                    }
                }
            }
        ); // makes me sad
        $("#app_form_dynamic").append(
            '<input id="app_form_submit" type="submit"'+
            'onclick="on_valid_form();"/>'
        )
    }
}

