// :todo(drj): move to scraperwiki.js
var smartAlert = function(message, technicalDetails) {
  var reportButton = '<span id="report_btn">Click the big red <strong>Help</strong> button for assistance</span>'
  var detailButton = '<a id="detail_btn">click here to show technical details</a>'
  scraperwiki.alert(message, '<p class="actions">' + reportButton + ' or ' +
    detailButton + '</p><pre>' + technicalDetails + '\n\n' +
    obtainStack() + '</pre>', true)
}

var obtainStack = function() {
  return "Origin:\n\n" + printStackTrace().slice(4).join("\n");
}


// :todo(drj): this function is pretty generic and should be
// in scraperwiki.js
function saveSettings(callback) {
  // Save all elements that have class "sw-persist".
  // :todo(drj): doesn't work for type="checkbox"; fix that.
  var toSave = {}
  $('.sw-persist').each(function(i, element) {
    var $element = $(element)
    toSave[element.id] = $element.val()
  });
  var saveString = JSON.stringify(toSave, null, 4)
  var escapedString = scraperwiki.shellEscape(saveString)
  scraperwiki.exec(
    "printf > allSettings.json '%s' " + escapedString
    , callback)
}
// :todo(drj): this function is pretty generic and should be
// in scraperwiki.js
function loadSettings(callback) {
  // after the exec (below), we call this function to fill in
  // all elements that have the "sw-persist" class.
  var populateElements = function() {
    $('.sw-persist').each(function(i, element) {
      var $element = $(element)
      $element.val(window.allSettings[element.id])
    });
  }

  scraperwiki.tool.exec('touch allSettings.json; cat allSettings.json',
    function(content) {
      window.allSettings = {}
      if(content) {
        try {
          window.allSettings = JSON.parse(content)
        } catch(e) {
          smartAlert("Failed to parse settings file",
            String(e), "\n\n" + content)
        }
      }
      populateElements()
    })
}

$(function() {
    loadSettings()

    // Setup the "submit" button.
    // :todo(drj): make generic and put in scraperwiki.js
    var execSuccess = function(execOutput) {
      // Note: "success" here means that the command executed,
      // but says nothing about what it did.
      if(execOutput != '') {
        smartAlert("An error occurred", execOutput)
        return
      }
      var datasetUrl = "/dataset/" + scraperwiki.box
      scraperwiki.tool.redirect(datasetUrl)
    }
    $('#source-go').on('click', function() {
      $(this).addClass('loading').html('Fetching…')
      saveSettings(function() {
        scraperwiki.exec("tool/geojson.py", execSuccess)
        var q = $('#source-url').val()
        scraperwiki.dataset.name("GeoJSON from " + name_from_url(q))
      })
    })

    setup_behaviour()
})

// :todo(drj): should be generic (in scraperwiki.js?).
var name_from_url = function(url) {
  var bits = url.split("/")
  if (bits.length > 2) {
    var ret = bits[2] 
    ret = ret.replace("www.", "")
    return ret
  }
  return url
}

// Setup various minor bits of user-interface:
//   Pressing return should have same effect as button click;
//   Hovering over the example opens popup;
//   Clicking on popup populates the box.
var setup_behaviour = function() {
  // :todo(drj): should be in scraperwiki.js
  $("#source-url").attr('disabled', false).on('keyup', function(e){
    if(e.which == 13){  // carriage return
      e.preventDefault()
      $('#source-go').trigger('click')
    }
  })

  // :todo(drj): should be in scraperwiki.js
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

  // Make the "show technical details" thing work.
  $(document).on('click', '.alert #detail_btn', function(){
    $(this).parents('.alert').find('pre').slideToggle(250)
  })
}
