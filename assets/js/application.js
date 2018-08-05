const socketio = require('socket.io-client')
const autosize = require('autosize')
require('jquery.hotkeys')

$(document).ready(function() {
  let table = null
  const socket = socketio(window.location.protocol +
    '//' + document.domain +
    (location.port ? ":" + location.port : ""))
  let uuid
  let running = false

  const $run      = $('#run')
  const $code     = $('#code')
  const $form     = $('#codeform')
  const $save     = $('#save')
  const $inputs   = $('#inputs')
  const $output   = $('#output')
  const $errors   = $('#errors')
  const $explain  = $('#explain')
  const $version  = $('#version')

  const runtext = 'Run (ctrl + enter)'
  const killtext = 'Kill (esc)'

  $form.on('submit', e => e.preventDefault())

  // Setup the text areas to automatically resize based on content
  autosize($code)
  autosize($inputs)

  // Setup the code and input blocks to resize automatically as needed
  $code.bind('input propertychange', () => countChar($code))

  // Listen to the paste input field so that we can check the type
  const $paste = $('#paste_input_field')
  $paste.bind('input propertychange', () => checkInputType($paste))

  jQuery.hotkeys.options.filterContentEditable = false
  jQuery.hotkeys.options.filterInputAcceptingElements = false

  // Bind ctrl+return to submit the code for the user
  $(document).bind('keydown', 'ctrl+return', submitCode)
  $(document).bind('keydown', 'esc', killjob)

  function sendAnalyticsEvent(category, type, message) {
    if (typeof ga !== "undefined") {
      ga('send', 'event', category, type, message)
    }
  }

  function timeoutFcn() {
    Rollbar.warning("SocketIO Connection Failed", { uuid })

    // Send a google analytics event if it's defined
    sendAnalyticsEvent('errors', 'error', 'Submit failed')

    // Force the socket to reconnect
    socket.disconnect()
    socket.connect()

    // Attempt to resubmit the job
    submitCode()
  }

  function submitCode() {
    // If code is already running or there is no code, then skip
    if ( running === true || $code.val() === '') {
      return
    }

    const $debug = $('#debug')

    $('#errorconsoletab').css('font-weight', 'normal')
    $errors.html('')
    $output.html('')

    const timeoutId = setTimeout(timeoutFcn, 2000)

    socket.emit('submit', {
      code:     $code.val(),
      inputs:   $inputs.val(),
      debug:    $debug.val(),
      version:  $version.data('version'),
      uid:      uuid
    }, () => {
      // Make sure that we don't fire the timeout callback
      clearTimeout(timeoutId)

      // Change the status and update the button functionality
      running = true
      $run.text(killtext)

      sendAnalyticsEvent('general', 'workflow', 'Job Submitted')
    })
  }

  socket.on('connect', () => {
    console.log('Connected to server.')
    $run.removeClass('disabled')
    $run.text(runtext)
  })

  // When the server acknowledges that we are connected it will issue
  // us an ID which we can use to get updates
  socket.on('connection', data => {
    console.log(`Session ID: ${uuid = data.session_id}`)
  })

  $explain.on('click', () => {
      const code = $code.val()
      const version = $version.data('version')

      // Do not submit the form unless there is code
      if (code === '') {
          return
      }

      $('#modal-explain').text('Parsing...')

      // Going to get the explanation and post it in a balloon
      $('#explainmodal').modal()

      $.ajax({
          url: '/explain',
          method: 'GET',
          data:{
            code: code,
            version: version
          },
          success: function(resp) {
            const explanation = resp['data'].map(x => x.value).join('')
            $('#modal-explain').text(explanation)
          }
      })
  })

  function getlink() {
    const data = {
      code: $code.val(),
      inputs: $inputs.val(),
      version: $version.data('version')
    }

    const link = $.param(data)

    // Now sanitize for SE
    const sanitize = ch => `%${ch.charCodeAt(0).toString(16)}`
    return link.replace(/[!'()*]/g, sanitize)
  }

  socket.on('killed', () => {
    $run.text(runtext)
    running = false
    console.log('Task killed.')
  })

  socket.on('complete', () => {
    $run.text(runtext)
    running = false
    console.log('Task complete.')
  })

  function killjob() {
    socket.emit('kill', {uid: uuid})
  }

  $run.on('click', () => running ? killjob () : submitCode())

  socket.on('status', function(data) {
    console.log('Output received.')

    // Clear the output
    $output.text('')

    if ( data['session'] === uuid ) {
      data['data'].forEach(function(item) {
        switch ( item.type ) {
          case 'image':
          case 'image_nn':
            // Remove any previous images (simulates drawnow)
            let $thumb = $('.thumb')

            if ($thumb.length) {
              $thumb.find('.imshow').attr('src', item.value)
            } else {
              const $container = $('<div/>', { 'class': 'thumb' })
              const $img = $('<img/>', { 'class': 'imshow', src: item.value })
              $container.append($img)
              $output.append($container)

              const $preview = $('#imagepreview')

              $container.on('click', () => {
                const url = $img.attr('src')
                $preview.attr('src', url)
                const img = $preview.get(0)

                $('#dimensions').text(img.naturalHeight + ' x ' + img.naturalWidth)
                $('#imagemodal').modal('show')
              })

              if (item.type === 'image_nn') {
                $img.addClass('nn-interp')
                $preview.addClass('nn-interp')
              } else {
                $img.removeClass('nn-interp')
                $preview.removeClass('nn-interp')
              }
            }

            break
          case 'audio':
            const $span = $('div', { 'class': 'audio' })
            const fallback = 'Your browser does not support the <code>audio</code> element.'
            const $audio = $('audio', {
              src: item.value,
              controls: "true",
              text: fallback
            })

            $span.append($audio)
            $output.append($span)
            break
          case 'stderr':
            $errors.append(document.createTextNode(item.value + '\n'))
            $('#errorconsoletab').css('font-weight', 'bold')
            break
          default:
            $output.append(document.createTextNode(item.value))
        }
      })
    }
  })

  function refreshHelp() {
    // If the table is initialized, then refresh it
    if (table) {
      const version = $version.data('version')
      table.ajax.url(`help/${version}`).load()
    }
  }

  function checkInputType(obj) {
    // If contains any alpha-numeric characters
    const str = $(obj).val()
    const $array = $('#array_input')
    const $string = $('#string_input')

    if (str.toLowerCase() === str.toUpperCase()){
      // Then we assume that this is numeric
      $array.prop('checked', true)
      $string.prop('checked', false)
    } else {
      $array.prop('checked', false)
      $string.prop('checked', true)
    }
  }

  function parseArray(str) {
    // Replace ][ with ; and [[ with [ and ]] with ]
   return str.replace(/]\s*,?\s*\[/g, '; ').
     replace(/\[\s*\[\s*/g, '[').
     replace(/]\s*]\s*/g, ']').
     replace(/\s+/g, ' ').
     replace(/\s*,\s*/g, ', ')
  }

  function parseString(string) {
    // Parse as raw string
    const parts = string.split('\n')

    // Now pad any strings as needed
    let maxLength = 0
    $.each(parts, (index, val) => {
      maxLength = Math.max(maxLength, val.length)
    })


    let output = parts.length > 1 ? "[" : ''

    for ( let k = 0; k < parts.length; ++k ){
      let num2pad = maxLength - parts[k].length
      parts[k] += new Array(num2pad+1).join(' ')
      output = `${output}'${parts[k]}';`
    }

    output = output.replace(/;$/g, '')

    if (parts.length > 1){
      output = output + ']'
    }

    return output
  }

  $('#paste_apply').on('click', () => {
    const $input = $('#paste_input_field')
    let input
    switch ($('input[name=format]:checked').val()) {
      case 'array':
        input = parseArray($input.val())
        break
      case 'string':
        input = parseString($input.val())
        break
    }

    if ($inputs.val().length) {
      input = '\n' + input
    }

    $inputs.val($inputs.val() + input)

    // Make sure that we resize the inputs field
    autosize.update($inputs)

    $('#pastemodal').modal('toggle')
    $input.val('')
  })

  $('#paste_input').on('click', () => {
    // Open up modal dialog to add data
    $('#pastemodal').modal()
  })

  $('#pastemodal').on('shown.bs.modal', () => {
    $('#paste_input_field').focus()
  })

  $('.version').on('click', e => {
    $version.text(e.target.text).data('version', $(e.target).data('version'))
    refreshHelp()
    e.preventDefault()
  })

  $save.on('click', event => {
    const link = '?' + getlink()
    history.pushState({'Title': '', 'Url': link}, '', link)
    event.preventDefault()
  })

  // When the image preview dialog is closed, reset the share link
  $('#imagemodal').on('hidden.bs.modal', () => {
    $('#share').removeClass('flip-side-2').addClass('flip-side-1')
    $('#sharelink').removeClass('flip-side-1')
  })

  // Be sure that we place the CSRF token in all AJAX request headers
  $.ajaxSetup({
    // Add a header containing the CSRF token if needed
    beforeSend: function(xhr, settings) {
      if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken",
        $('meta[name=csrf-token]').attr('content'))
      }
    }
  })

  $('#share').on('click', () => {
    // Display loading while we upload to imgur and get the link
    const $link = $('#imgurlink')
    $link.val('Loading...').css('color', '')

    // Flip over to the link to prevent the user from clicking share again
    $('#share').addClass('flip-side-2')
    $('#sharelink').addClass('flip-side-1')

    $.post({
      url: '/share',
      data: {'data': $('.thumb').find('.imshow').attr('src')},
      success: resp => {
        // Paste the link into the input box and highlight it
        $link.val(resp.link).prop('disabled', false).css('color', 'black').select()
      },
      error: () => $link.val('SERVER ERROR').css('color', 'red')
    })
  })

  function countChar(val) {
    const count = $(val).val().length
    const text = (count === 1) ? `(${count} character)` : `(${count} characters)`
    $('#charcount').text(text)
  }

  function searchTable(table, string) {
    const origLen = string.length

    // If only one " then replace with ""
    if ((string.match(/"/g) || []).length === 1){
      string = string.replace(/"/g, '""')
    }

    // Determine if it starts with X, Y, or Z
    const hasXYZ = string.match('^[XYZ]')

    // If we have a single character OR the search string
    // starts with X, Y, or Z and is two characters (or 3 if
    // one is a quote)
    if (origLen === 1 || (hasXYZ && origLen === 2)) {
      // Search just the first column (no regex, non-smart,
      // and case-sensitive)
      table.columns(0).search(string, false, false, false).draw()
    } else {
      // Apply the search to the table as a whole
      table.columns(0).search('')
      table.search(string).draw()
    }
  }

  function toggleDocumentation() {
    const navitem = $('#doctoggle').parent()
    const activeClasses = 'col-md-6 col-lg-6 col-sm-6'

    const $left = $('#left_div')
    const $drawer = $('.drawer')

    if (navitem.hasClass('active')) {
      navitem.removeClass('active')
      $left.removeClass(activeClasses)
      $drawer.drawer('hide')
    } else {
      navitem.addClass('active')
      $left.addClass(activeClasses)
      $drawer.drawer('show')

      // Create the DataTable if it doesn't exist already
      if (table === null) {
        table = $('#documentation').DataTable({
          paging: false,
          ordering: false,
          info: false,
          ajax: 'help/' + $version.data('version'),
          stripe: true,
          scrollY: 'calc(100% - 80px)',
          scrollX: false,
          scrollCollapse: true,
          order: [[0, "asc"]],
          columns: [
            {
              data: 'source',
              orderable: true,
              render: src => `<strong>${src}</strong>`
            },
            {
              data: null,
              orderable: false,
              render: data => {
                const parts = [`<strong>${data.brief}</strong>`]
                if (data.arguments) parts.push(data.arguments)
                parts.push(data.description)
                return parts.join('\n')
              }
            }
          ]
        })

        // The events that we'd like to override from DataTables
        const events = 'keyup.DT search.DT input.DT paste.DT cut.DT'

        let searchDelay = null

        // Custom search function to handle single " characters
        $('#documentation_filter input')
          .off(events)
          .on(events, evnt => {
            // Only allow the search to be performed every 250ms
            clearTimeout(searchDelay)
            searchDelay = setTimeout(() => searchTable(table, evnt.target.value), 250)
          })
      }
    }
  }

  $('.drawer').on('shown.bs.drawer', () => {
    $('input[type=search]').focus()
  })

  $('#doctoggle').on('click', event => {
    toggleDocumentation()
    event.preventDefault()
  })

  $('#docbutton').on('click', toggleDocumentation)
})
