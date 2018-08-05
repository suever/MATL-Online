require('jquery')

$(document).ready(() => {
  const $checkbox = $('#optout_check')

  $checkbox.prop('checked', $checkbox.data('status'))

  $checkbox.change(() => {
    $.get({
      url: $checkbox.data('url'),
      data: { value: $checkbox.prop('checked') }
    })
  })
})