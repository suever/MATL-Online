var table = null;
var socket = io.connect(window.location.protocol + '//' + document.domain + ':' + location.port);
var uuid;
var running = false;

$('#codeform').on('submit', function(d) {
    d.preventDefault();
});

// Setup the text areas to automatically resize based on content
autosize($('#code'));
autosize($('#inputs'));

// Setup the code and input blocks to resize automatically as needed
$('#code').bind('input propertychange', function(){
    countChar(this);
});

// Listen to the paste input field so that we can check the type
$('#paste_input_field').bind('input propertychange', function(){
    checkInputType(this);
});

function sendAnalyticsEvent(category, type, message) {
    if ( typeof ga !== "undefined" ) {
        ga('send', 'event', category, type, message);
    }
}

function timeoutFcn() {
    // Send a google analytics event if it's defined
    sendAnalyticsEvent('errors', 'error', 'Submit failed');

    // Force the socket to reconnect
    socket.disconnect();
    socket.connect();

    // Attempt to resubmit the job
    submitCode();
}

function submitCode() {
    var form = $('#codeform');

    $('#errorconsoletab').css('font-weight', 'normal');
    $('#errors').html('');
    $('#output').html('');

    var timeoutId = setTimeout(timeoutFcn, 2000);

    socket.emit('submit', {
        code: $('#code').val(),
        inputs: $('#inputs').val(),
        debug: $('#debug').val(),
        version: $('#version').data('version'),
        uid: uuid
    }, function(resp){
        // Make sure that we don't fire the timeout callback
        clearTimeout(timeoutId);

        // Change the status and update the button functionality
        running = true;
        $('#run').text('Kill');

        sendAnalyticsEvent('general', 'workflow', 'Job Submitted');
    });
}

socket.on('connect', function(data){
    console.log('Connected to server.');
    $('#run').removeClass('disabled');
    $('#run').text('Run');
});

// When the server acknowledges that we are connected it will issue
// us an ID which we can use to get updates
socket.on('connection', function(data) {
    uuid = data.session_id;
    console.log('Session ID: ' + uuid);
});

$('#explain').on('click', function(d) {
    var code = $('#code').val();
    var version = $('#version').data('version');

    // Do not submit the form unless there is code
    if ( code === '' ) {
        return;
    }

    $('#modal-explain').text('Parsing...');

    // Going to get the explanation and post it in a balloon
    $('#explainmodal').modal();

    $.ajax({
        url: '/explain',
        method: 'GET',
        data:{
            code: code,
            version: version
        },
        success: function(resp) {
            alltext = '';
            resp['data'].forEach(function (item) {
                alltext = alltext + item.value
            });
            $('#modal-explain').text(alltext);
        }
    });
});

function getlink() {

    var data = {
        'code': $('#code').val(),
        'inputs': $('#inputs').val(),
        'version': $('#version').data('version')};

    var link = $.param(data);

    // Now sanitize for SE
    return link.replace(/[!'()*]/g, function(ch) {
        return '%' + ch.charCodeAt(0).toString(16);
    });
}

socket.on('killed', function(data) {
    $('#run').text('Run');
    running = false;
    console.log('Task killed.');
});

socket.on('complete', function(msg) {
    $('#run').text('Run');
    running = false;
    console.log('Task complete.');
});

$('#run').on('click', function() {
    if ( running ) {
        socket.emit('kill', {uid: uuid});
    } else {
        submitCode();
    }
});

socket.on('status', function(data) {
    var output = $('#output');
    var errors = $('#errors');

    console.log('Output received.');

    // Clear the output
    output.text('');

    if ( data['session'] === uuid ) {
        data['data'].forEach(function(item) {
            switch ( item.type ) {
                case 'image':
                case 'image_nn':

                    // Remove any previous images (simulates drawnow)
                    var thumb = $('.thumb');

                    if ( thumb.length ){
                        $(thumb).find('.imshow').attr('src', item.value);
                    } else {
                        val = '<span class="thumb"><img class="imshow" src="' + item.value + '"><br/></span>';
                        output.append(val);
                        $('.thumb').on('click', function(e) {
                            var url = $(this).find('.imshow').attr('src');
                            $('#imagepreview').attr('src', url);
                            var img = $('#imagepreview').get(0);

                            $('#dimensions').text(img.naturalHeight + ' x ' + img.naturalWidth);
                            $('#imagemodal').modal('show');
                        });


                        if ( item.type === 'image_nn' ){
                            $('.imshow').addClass('nn-interp');
                            $('#imagepreview').addClass('nn-interp');
                        } else {
                            $('.imshow').removeClass('nn-interp');
                            $('#imagepreview').removeClass('nn-interp');
                        }
                    }

                    break;
                case 'stderr':
                    errors.append(document.createTextNode(item.value + '\n'));
                    $('#errorconsoletab').css('font-weight', 'bold');
                    break;
                default:
                    output.append(document.createTextNode(item.value));
            }
        });
    }
});

function refreshHelp() {
    // If the table is initialized, then refresh it
    if ( table ) {
        table.ajax.url('help/' + $('#version').data('version')).load();
    }
}

function checkInputType(obj){
    // If contains any alpha-numeric characters
    var str = $(obj).val();

    if ( str.toLowerCase() === str.toUpperCase() ){
        // Then we assume that this is numeric
        $('#array_input').prop('checked', true);
        $('#string_input').prop('checked', false);
    } else {
        $('#array_input').prop('checked', false);
        $('#string_input').prop('checked', true);
    }
}

function parseArray(str){
    // Replace ][ with ; and [[ with [ and ]] with ]
    return str.replace(/\]\s*,?\s*\[/g, '; ').
               replace(/\[\s*\[\s*/g, '[').
               replace(/\]\s*\]\s*/g, ']').
               replace(/\s+/g, ' ').
               replace(/\s*,\s*/g, ', ');
}

function parseString(str){
    // Parse as raw string
    str = str.split('\n');

    // Now pad any strings as needed
    var maxLength = 0;
    $.each(str, function(index, val){
        maxLength = Math.max(maxLength, val.length);
    });


    if ( str.length > 1 ){
        output = "[";
    } else {
        output = '';
    }

    for ( var k = 0; k < str.length; ++k ){
        num2pad = maxLength - str[k].length;
        str[k] += new Array(num2pad+1).join(' ');
        output = output + "'" + str[k] + "';";
    }

    output = output.replace(/;$/g, '');

    if ( str.length > 1 ){
        output = output + ']';
    }

    return output;
}

$('#paste_apply').on('click', function(evnt){

    var input = $('#paste_input_field').val();

    switch ( $("input[name=format]:checked").val() ) {
        case 'array':
            input = parseArray(input);
            break;
        case 'string':
            input = parseString(input);
            break;
    }

    if ( $('#inputs').val().length ){
        input = '\n' + input;
    }

    $('#inputs').val($('#inputs').val() + input);

    // Make sure that we resize the inputs field
    autosize.update($('#inputs'));

    $('#pastemodal').modal('toggle');
    $('#paste_input_field').val('');
});

$('#paste_input').on('click', function(evnt){
    // Open up modal dialog to add data
    $('#pastemodal').modal();
});

$('#pastemodal').on('shown.bs.modal', function(){
    $('#paste_input_field').focus();
});

$('.version').on('click', function(e) {
    $('#version').text(e.target.text).data('version', $(e.target).data('version'));
    refreshHelp();
    e.preventDefault();
});

$('#save').on('click', function(e) {
    link = '?' + getlink();
    history.pushState({'Title': '', 'Url': link}, '', link);
    e.preventDefault();
});

// When the image preview dialog is closed, reset the share link
$('#imagemodal').on('hidden.bs.modal', function () {
    $('#share').removeClass('flip-side-2').addClass('flip-side-1');
    $('#sharelink').removeClass('flip-side-1');
});

// Be sure that we place the CSRF token in all AJAX request headers
$.ajaxSetup({
    // Add a header containing the CSRF token if needed
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken",
                $('meta[name=csrf-token]').attr('content'));
        }
    }
});

$('#share').on('click', function(e){
    // Display loading while we upload to imgur and get the link
    $('#imgurlink').val('Loading...').css('color', '');

    // Flip over to the link to prevent the user from clicking share again
    $('#share').addClass('flip-side-2');
    $('#sharelink').addClass('flip-side-1');

    $.post({
        url: '/share',
        data: {'data': $('.thumb').find('.imshow').attr('src')},
        success: function(resp){
            // Paste the link into the input box and highlight it
            $('#imgurlink').val(resp.link)
                .prop('disabled', false)
                .css('color', 'black')
                .select();
        },
        error: function(resp){
            // Some unspecified error happened (could be CSRF or others)
            $('#imgurlink').val('SERVER ERROR')
                .css('color', 'red');
        }
    });
});

function countChar(val) {
    var count = val.value.length;

    if ( count === 1 ) {
        $('#charcount').text('(' + count + ' character)');
    } else {
        $('#charcount').text('(' + count + ' characters)');
    }
}

function searchTable(table, string) {

    var origLen = string.length;
    var hasQuote = false;

    // If only one " then replace with ""
    if ( (string.match(/"/g) || []).length === 1 ){
        string = string.replace(/"/g, '""');
        hasQuote = true;
    }

    // Determine if it starts with X, Y, or Z
    var hasXYZ = string.match('^[XYZ]');

    // If we have a single character OR the search string
    // starts with X, Y, or Z and is two characters (or 3 if
    // one is a quote)
    if ( origLen === 1 || ( hasXYZ && origLen === 2 ) ) {
        // Search just the first column (no regex, non-smart,
        // and case-sensitive)
        table.columns(0).search(string, false, false, false).draw();
    } else {
        // Apply the search to the table as a whole
        table.columns(0).search('');
        table.search(string).draw();
    }
}

function toggleDocumentation(){

    var navitem = $('#doctoggle').parent();
    var activeClasses = 'col-md-6 col-lg-6 col-sm-6';

    if ( navitem.hasClass('active') ){
        navitem.removeClass('active');
        $('#left_div').removeClass(activeClasses);
        $('.drawer').drawer('hide');
    } else {
        navitem.addClass('active');
        $('#left_div').addClass(activeClasses);
        $('.drawer').drawer('show');

        // Create the datatable if it doesn't exist already
        if ( table === null ){
            table = $('#documentation').DataTable({
                paging: false,
                ordering: false,
                info: false,
                ajax: 'help/' + $('#version').data('version'),
                stripe: true,
                scrollY: 'calc(100% - 80px)',
                scrollX: false,
                scrollCollapse: true,
                order: [[ 0, "asc"]],
                columns: [
                    {
                        data: 'source',
                        orderable: true,
                        render: function(src) {
                            return '<strong>' + src + '</strong>';
                        }
                    },
                    {
                        data: null,
                        orderable: false,
                        render: function(data) {
                            output = '<strong>' + data.brief + '</strong>';
                            if ( data.arguments ){
                                output = output + '\n' + data.arguments;
                            }
                            return output + '\n' + data.description;
                        }
                    }]
            });

            // The events that we'd like to override from datatables
            var events = 'keyup.DT search.DT input.DT paste.DT cut.DT';

            var searchDelay = null;

            // Custom search function to handle single " characters
            $('#documentation_filter input')
            .off(events)
            .on(events, function(evnt){
                // Only allow the search to be performed every 250ms
                clearTimeout(searchDelay)
                searchDelay = setTimeout(function(){
                    searchTable(table, evnt.target.value);
                }, 250);
            });
        }
    }
}

$('.drawer').on('shown.bs.drawer', function(){
    $('input[type=search]').focus();
});

$('#doctoggle').on('click', function(evnt){
    toggleDocumentation();
    evnt.preventDefault();
});

$('#docbutton').on('click', function(evnt){
    toggleDocumentation();
});
