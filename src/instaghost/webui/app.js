(function () {
  var form = document.getElementById('job-form');
  if (!form) return;

  var countField = document.getElementById('count-field');
  var urlField = document.getElementById('url-field');
  var userField = document.getElementById('username-field');

  function sync() {
    var checked = form.querySelector('input[name=action]:checked');
    var action = checked ? checked.value : 'profile';
    countField.hidden = !(action === 'posts' || action === 'reels');
    urlField.hidden = action !== 'url';
    userField.hidden = action === 'url';
    userField.querySelector('input').required = action !== 'url';
    urlField.querySelector('input').required = action === 'url';
  }

  Array.prototype.forEach.call(form.querySelectorAll('input[name=action]'), function (radio) {
    radio.addEventListener('change', sync);
  });
  sync();

  form.addEventListener('submit', function () {
    document.getElementById('busy').classList.add('show');
  });
})();
