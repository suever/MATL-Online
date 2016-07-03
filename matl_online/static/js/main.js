var table;
var socket = io.connect('http://' + document.domain + ':' + location.port);
var uuid;
var running = false;

$('#codeform').on('submit', function(d) { d.preventDefault(); });

parseHash();

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

function encodeData(data) {
    var ret = [];
    for (var d in data) {
        ret.push(encodeURIComponent(d) + '=' + encodeURIComponent(data[d]));
    }

    return ret.join('&');
}

function getlink() {
    return encodeData({
        'code': $('#code').val(),
        'inputs': $('#inputs').val(),
        'version': $('#version').data('version')
    });
}

function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

// Parse the hashed information
function parseHash(){
    if ( window.location.hash.length > 1 ){
        $('#code').val(getParameterByName('code'));
        $('#inputs').val(getParameterByName('inputs'));

        version = getParameterByName('version');

        // Make sure that the version is even valid
        versions = $('a.version');
        for ( k = 0; k < versions.length; ++k ) {
            V = $(versions[k]);
            if ( version == V.data('version') ) {
                $('#version').data('version', V.data('version')).text(V.text());
                break
            }
        }

        // Update the character count
        countChar($('#code')[0]);
    }
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
                    val = '<span class="thumb"><img class="imshow" src="' + item.value + '"></span><br>';
                    output.append(val);
                    $('.thumb').on('click', function(e) {
                        var url = $(this).find('.imshow').attr('src');
                        $('#imagepreview').attr('src', url);
                        var img = $('#imagepreview').get(0);

                        $('#dimensions').text(img.naturalHeight + ' x ' + img.naturalWidth);
                        $('#imagemodal').modal('show');
                    });

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
    window.location.hash = '?' + getlink();
    e.preventDefault();
});

table = $('#documentation').DataTable({
    paging: false,
    ordering: false,
    info: false,
    ajax: 'help/' + $('#version').data('version'),
    stripe: true,
    scrollY: '80vh',
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

function countChar(val) {
    var count = val.value.length;

    if ( count == 1 ) {
        $('#charcount').text('(' + count + ' character)');
    } else {
        $('#charcount').text('(' + count + ' characters)');
    }
}
