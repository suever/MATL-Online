var table;
var socket = io.connect(window.location.protocol + '//' + document.domain + ':' + location.port);
var uuid;
var running = false;

$('#codeform').on('submit', function(d) { d.preventDefault(); });

function submitCode() {
    var form = $('#codeform');

    $('#errorconsoletab').css('font-weight', 'normal');
    $('#errors').html('');
    $('#output').html('')

    socket.emit('submit', {
        code: $('#code').val(),
        inputs: $('#inputs').val(),
        debug: $('#debug').val(),
        version: $('#version').data('version'),
        uid: uuid
    });

    running = true;

    $('#run').text('Kill');
}

// When the server acknowledges that we are connected it will issue
// us an ID which we can use to get updates
socket.on('connection', function(data) {
    uuid = data.session_id;
});

$('#explain').on('click', function(d) {
    var code = $('#code').val();
    var version = $('#version').data('version');

    // Do not submit the form unless there is code
    if ( code == '' ) {
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
});

socket.on('complete', function(msg) {
    $('#run').text('Run');
    running = false;
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

    // Clear the output
    output.text('');

    if ( data['session'] == uuid ) {
        data['data'].forEach(function(item) {
            switch ( item.type ) {
                case 'image':

                    // Remove any previous images (simulates drawnow)
                    var thumb = $('.thumb');

                    if ( thumb.length ){
                        $(thumb).find('.imshow').attr('src', item.value);
                    } else {
                        val = '<span class="thumb"><img class="imshow nn-interp" src="' + item.value + '"><br/></span>';
                        output.append(val);
                        $('.thumb').on('click', function(e) {
                            var url = $(this).find('.imshow').attr('src');
                            $('#imagepreview').attr('src', url);
                            var img = $('#imagepreview').get(0);

                            $('#dimensions').text(img.naturalHeight + ' x ' + img.naturalWidth);
                            $('#imagemodal').modal('show');
                        });
                    }

                    break;
                case 'stderr':
                    errors.append(item.value + '\n');
                    $('#errorconsoletab').css('font-weight', 'bold');
                    break;
                default:
                    $('#output').append(item.value);
            }
        });
    }
});

function refreshHelp() {
    table.ajax.url('help/' + $('#version').data('version')).load();
}

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

table = $('#documentation').DataTable({
    paging: false,
    ordering: false,
    info: false,
    ajax: 'help/' + $('#version').data('version'),
    stripe: true,
    scrollY: '75vh',
    scrollX: false,
    scrollCollapse: true,
    order: [[ 0, "asc"]],
    columns: [
        {
            data: 'source',
            orderable: true
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

// Custom search function to handle single " characters
$('input[type=search]').on( 'keyup', function () {

    var searchStr = this.value;

    // If only one " then replace with ""
    if ( (searchStr.match(/"/g) || []).length == 1 ){
        searchStr = searchStr.replace(/"/g, '""');
    }

    table.search( searchStr ).draw();
} );

function countChar(val) {
    var count = val.value.length;

    if ( count == 1 ) {
        $('#charcount').text('(' + count + ' character)');
    } else {
        $('#charcount').text('(' + count + ' characters)');
    }
}
