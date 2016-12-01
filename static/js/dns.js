var apiUrl = '/api/v1/';
var record_apiUrl = apiUrl + 'record/';
var rhistory_apiUrl = apiUrl + 'rhistory/';
var zone_apiUrl = apiUrl + 'zone/';
var serverconfig_apiUrl = apiUrl + 'serverconfig/';

$.views.settings.delimiters("<%", "%>");

function dns_getDataFromApi(url) {

    var api_response = false;
    return $.ajax({
        method: "GET",
        url: url,
        dataType: "text",
        contentType: "application/json",
        error: function (xhr, status, error) {
            $.notify({
                message: 'Failed to get data: ' + xhr.responseText
            },{
                type: 'danger'
            })
        },
    }); 


}

function dns_patchDataApi(url, data) {

    $.ajaxSetup({
        crossDomain: false, // obviates need for sameOrigin test
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        }
    });

    var api_response = false;
    return $.ajax({
        method: "PATCH",
        url: url,
        data: JSON.stringify(data),
        dataType: "text",
        contentType: "application/json",
        error: function (xhr, status, error) {
            $.notify({
                message: 'Failed to patch data: ' + xhr.responseText
            },{
                type: 'danger'
            })
        },
    }); 

}

function dns_patchConfig(config_id) {

    var api_url = [serverconfig_apiUrl, config_id, '/'].join('');

    editor.save()

    var formData = $('#serverConfigForm').serializeArray();
    var data_array = {};

    $.each(formData, function(i, field){
        data_array[field.name] = field.value;
    });

    var api_response = dns_patchDataApi(api_url, data_array);

    api_response.success(function(data) {
        $.notify('Config saved', { type: 'success' });
    });
}

function dns_applyConfig(config_id) {

    var api_url = [serverconfig_apiUrl, 'apply/', config_id, '/'].join('');

    var api_response = dns_getDataFromApi(api_url);

    api_response.success(function(data) {
        
        var json_data = jQuery.parseJSON(data);
        if (json_data.apply.warning[0] != null) {
            $.each( json_data.apply.warning, function( i, val ) {
                $.notify(val, { type: 'warning' })
            });
        }
        $.notify('Config applied', { type: 'success' });
    });
}

function dns_getZones(filter) {

    if (typeof filter === 'undefined' || filter === null) {
        filter = false;
    }

    $('#zoneList').empty();
    
    var api_url = zone_apiUrl;

    if (filter != false) {
        api_url = [zone_apiUrl, '?zone__contains=', filter].join('');
    }

    var api_response = dns_getDataFromApi(api_url);

    api_response.success(function(data) {
        var json_data = jQuery.parseJSON(data);
        var zones = json_data.objects;
        $('#zoneList').append(
            $( '#zoneListTemplate' ).render( zones )
        );
    });


}   

function dns_getRecords(zone_id) {

    if (typeof zone_id === 'undefined' || zone_id === null) {
        zone_id = false;
    }

    $('#recordList').html();

    var api_url = record_apiUrl;

    $('#recordList').html(
        $.templates('#addRecordTemplate').render()
    );

    if (zone_id != false) {
        api_url = [record_apiUrl, '?zone__exact=', zone_id].join('');
    }

    var api_response = dns_getDataFromApi(api_url);

    api_response.success(function(data) {
        var json_data = jQuery.parseJSON(data);
        var records = json_data.objects;
        $('#addRecordTr').after(
            $( '#RecordTemplate' ).render( records )
        );
    });

}

function dns_searchRecords(offset, limit, host, zone, answer) {

    if (typeof host === 'undefined' || host === null) {
        host = '';
    }
    if (typeof zone === 'undefined' || zone === null) {
        zone = '';
    }
    if (typeof answer === 'undefined' || answer === null) {
        answer = '';
    }
    if (typeof offset === 'undefined' || offset === null) {
        offset = 0;
    }
    if (typeof limit === 'undefined' || limit === null) {
        limit = 40;
    }

    var api_url = record_apiUrl;

    api_url = [record_apiUrl, 
        '?offset=', offset, 
        '&limit=', limit, 
        '&host__contains=', host, 
        '&zone__zone__contains=', zone,
        '&answer__contains=', answer].join('');

    var api_response = dns_getDataFromApi(api_url);

    api_response.success(function(data) {
        var json_data = jQuery.parseJSON(data);
        var records = json_data.objects;
        var total_count = json_data.meta.total_count;
        if (total_count - offset > limit) {
            $( '#showMoreButton').removeClass( 'hidden' );
        } else {
            $( '#showMoreButton').addClass( 'hidden' );
        }
        $('#recordList').append(
            $( '#RecordTemplate' ).render( records )
        );
        $('#totalRecords').html( total_count );
    });
}

function dns_historyRecords(offset, limit, host, zone, answer) {

    if (typeof host === 'undefined' || host === null) {
        host = '';
    }
    if (typeof zone === 'undefined' || zone === null) {
        zone = '';
    }
    if (typeof answer === 'undefined' || answer === null) {
        answer = '';
    }
    if (typeof offset === 'undefined' || offset === null) {
        offset = 0;
    }
    if (typeof limit === 'undefined' || limit === null) {
        limit = 40;
    }

    api_url = [rhistory_apiUrl, 
        '?offset=', offset, 
        '&limit=', limit, 
        '&host__contains=', host, 
        '&zone__zone__contains=', zone,
        '&answer__contains=', answer].join('');

    var api_response = dns_getDataFromApi(api_url);

    api_response.success(function(data) {
        var json_data = jQuery.parseJSON(data);
        var records = json_data.objects;
        var total_count = json_data.meta.total_count;
        if (total_count - offset > limit) {
            $( '#showMoreButton').removeClass( 'hidden' );
        } else {
            $( '#showMoreButton').addClass( 'hidden' );
        }
        $('#recordList').append(
            $( '#RecordTemplate' ).render( records )
        );
        $('#totalRecords').html( total_count );
    });
}

function dns_editRecord(record_id) {

    api_url = [record_apiUrl, record_id].join('');
    var api_response = dns_getDataFromApi(api_url);

    api_response.success(function(data) {
        var json_data = jQuery.parseJSON(data);
        $('#record_' + record_id).html(
            $('#editRecordTemplate').render(json_data)
        );
    });
}

function dns_patchRecord(record_id) {

    api_url = [record_apiUrl, record_id, '/'].join('');

    var form_name = '#editRecordForm_' + record_id;

    var formData = $(form_name).serializeArray();
    var data_array = {};

    $.each(formData, function(i, field){
        data_array[field.name] = field.value;
    });

    var api_response = dns_patchDataApi(api_url, data_array);

    api_response.success(function(data) {
        var json_data = jQuery.parseJSON(data);
        $('#record_' + record_id).replaceWith(
            $( '#RecordTemplate' ).render( json_data )
        );
        if (window.location.pathname == '/main/record/search/') {
            $.notify({ 
                message: $( '#notifyGenerate' ).render(json_data),
            }, {
                type: 'info',
                timer: 7000,
                placement: {
                    align: 'center',
                },
            });
        }
        dns_checkZoneView()
    });


}

function dns_patchCancel(record_id) {


    api_url = [record_apiUrl, record_id].join('');
    var api_response = dns_getDataFromApi(api_url);

    api_response.success(function(data) {
        var json_data = jQuery.parseJSON(data);
        $('#record_' + record_id).replaceWith(
            $('#RecordTemplate').render(json_data)
        );
    });
}

function dns_generateZone(zoneId) {

    api_url = [record_apiUrl, 'generate/', zoneId].join('');

    var api_response = dns_getDataFromApi(api_url);

    api_response.success(function(data) {
        $.notify('Zone generated', { type: 'success' });
    });

}

function dns_postDataApi(url, data) {

    $.ajaxSetup({
        crossDomain: false, // obviates need for sameOrigin test
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        }
    });

    var api_response = false;
    return $.ajax({
        method: "POST",
        url: url,
        data: JSON.stringify(data),
        dataType: "text",
        contentType: "application/json",
        error: function (xhr, status, error) {
            $.notify({
                message: 'Failed to post data: ' + xhr.responseText
            },{
                type: 'danger'
            })
        },
    }); 

}

function dns_addRecord() {

    var formData = $('#addRecordForm').serializeArray();
    var data_array = {};


    $.each(formData, function(i, field){
        data_array[field.name] = field.value;
    });
    
    var api_response = dns_postDataApi(record_apiUrl, data_array);

    api_response.success(function(data) {
        var dns_response = jQuery.parseJSON(data);
        var template = $.templates("#RecordTemplate");
        var recordHTML = template.render(dns_response);
        $('#recordTable').find('#addRecordTr').after(recordHTML);
        $.notify('Record added', { type: 'success' });
        dns_checkZoneView();
    });
}

function dns_priorityRecord() {

    var template = '';
    if ($('#record_type option:selected').text() == 'MX') {
        template = $.templates('#priorityWithInput');
    } else {
        template = $.templates('#priorityWithoutInput');
    }

    $('#priorityTd').html(template.render());

}

function dns_deleteRecordTimer(record_id) {

    var deleteNotify = $.notify('Hold 2 seconds to delete');

    downTimer = setTimeout(function() {
        dns_deleteRecord(record_id, deleteNotify);
    }, 1500);

    $(document).mouseup(function(){
        clearInterval(downTimer);
        return false;
    });
    $(document).mouseout(function(){
        clearInterval(downTimer);
        return false;
    });
}


function dns_deleteRecord(record_id, deleteNotify) {

    var record_apiUrl_id = record_apiUrl + record_id;

    var api_response = dns_getDataFromApi(record_apiUrl_id);

    var record = {};
    api_response.success(function(data) {
        record.data = jQuery.parseJSON(data);
    });

    $.ajaxSetup({
        crossDomain: false, // obviates need for sameOrigin test
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        }
    });

    $.ajax({
        method: "DELETE",
        url: record_apiUrl_id, 
        dataType: "text",
        contentType: "application/json",
        error: function (xhr, status, error) {
            deleteNotify.update({
                message: 'Failed to delete record: ' + xhr.responseText,
                type: 'danger',
            })
        },
        success: function () {
            deleteNotify.update({message: 'Record deleted', type: 'success' });
            $('table#recordTable tr#record_'+record_id).remove();
            if (window.location.pathname == '/main/record/search/') {
                $.notify({ 
                    message: $( '#notifyGenerate' ).render(record.data),
                }, {
                    type: 'info',
                    timer: 7000,
                    placement: {
                        align: 'center',
                    },
                });
            }
            dns_checkZoneView()
        }
    });
}

function dns_cloneZoneTimer() {

    var cloneNotify = $.notify('Hold 2 seconds to clone');

    cloneTimer = setTimeout(function() {
        dns_cloneZone(cloneNotify);
    }, 2000);

    $(document).mouseup(function(){
        clearInterval(cloneTimer);
        return false;
    });
    $(document).mouseout(function(){
        clearInterval(cloneTimer);
        return false;
    });
}

function dns_cloneZone(cloneNotify) {

    var form = '#cloneZoneForm';
    var formData = $(form).serializeArray();
    var data_array = {};

    var api_url = zone_apiUrl + 'clone/';

    $.each(formData, function(i, field){
        data_array[field.name] = field.value;
    });

    var api_response = dns_postDataApi(api_url, data_array);

    api_response.success(function(data) {
        var dns_response = jQuery.parseJSON(data);
        cloneNotify.update({message: 'Zone cloned', type: 'success' });
    });
}
