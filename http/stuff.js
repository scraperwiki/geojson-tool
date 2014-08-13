var stuff_init = function() {
  // $('#source-go').on('click', source_go)
  // $('#source-clear').on('click', source_clear)
  $("#source-url").attr('disabled', false).on('keyup', function(e){
    if(e.which == 13){  // carriage return
      e.preventDefault()
      $('#source-go').trigger('click')
    }
  })
  $('#show-examples').popover({
    content: function(){
      return $('#examples').html()
    },
    placement: "bottom",
    html: true
  })
  $(document).on('click', '#message .popover a', function(e){
    if (!e.metaKey) {
      e.preventDefault()
      $('body').animate({scrollTop: 0}, 200)
      $('#show-examples').popover('hide')
      $("#source-url").val( $(this).attr('href') )
      $('#error, .alert-error').hide()
    }
  })
  $(document).on('click', function(e){
    // Close the "examples" popover when you click anywhere outside it
    var $a = $('#show-examples')
    if( ! $a.is(e.target) && $a.has(e.target).length === 0 && $('.popover').has(e.target).length === 0 ){
      $a.popover('hide')
    }
  })

  if(typeof window.source_url !== "undefined"){
    if(typeof window.source_filename !== "undefined") {
      $('#source-url').val(window.source_filename)
    } else {
      $('#source-url').val(window.source_url)
    }
    source_disable_controls()
  }

  $('#next').val(window.location)
  $('#apikey').val(scraperwiki.readSettings().source.apikey)
  $('#file').on('change', function(){
    if( $(this).val() != '' ){
      $('#source-go').addClass('loading disabled').html("Uploading&hellip;")
      $('#up :submit').trigger('click')
    }
  })
}
