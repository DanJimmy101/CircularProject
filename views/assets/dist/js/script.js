var input = document.querySelector('input[name=categorytexts]'),
    tagify = new Tagify(input, {
      whitelist:[],
      originalInputValueFormat: valuesArr => valuesArr.map(item => item.value).join(',')
    }),
    controller; // for aborting the call

// listen to any keystrokes which modify tagify's input
tagify.on('input', onInput)

function onInput( e ){
  var value = e.detail.value
  tagify.whitelist = null // reset the whitelist

  // https://developer.mozilla.org/en-US/docs/Web/API/AbortController/abort
  controller && controller.abort()
  controller = new AbortController()

  // show loading animation and hide the suggestions dropdown
  tagify.loading(true).dropdown.hide()

  fetch('http://127.0.0.1:8000/data/?value=' + value, {signal:controller.signal})
    .then(RES => RES.json())
    .then(function(newWhitelist){
      tagify.whitelist = newWhitelist // update whitelist Array in-place
      tagify.loading(false).dropdown.show(value) // render the suggestions dropdown
    })
}

window.onload = function(){
  // document.getElementById("tags").value = "";
}