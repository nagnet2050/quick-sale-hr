(function(global){
  function ensureContainer(){
    var el = document.getElementById('toastContainer');
    if(!el){
      el = document.createElement('div');
      el.id = 'toastContainer';
      el.className = 'toast-container position-fixed bottom-0 end-0 p-3';
      el.style.zIndex = 1100;
      document.body.appendChild(el);
    }
    return el;
  }
  function showToast(message, variant){
    var container = ensureContainer();
    var id = 't_'+Date.now()+Math.random().toString().slice(2,6);
    var map = { success:'text-bg-success', warning:'text-bg-warning', danger:'text-bg-danger', info:'text-bg-info' };
    var bg = map[variant] || map.info;
    var div = document.createElement('div');
    div.className = 'toast align-items-center '+bg+' border-0';
    div.id = id;
    div.setAttribute('role','alert');
    div.setAttribute('aria-live','assertive');
    div.setAttribute('aria-atomic','true');
    div.innerHTML = '<div class="d-flex">\n'+
                    '  <div class="toast-body">'+String(message)+'</div>\n'+
                    '  <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>\n'+
                    '</div>';
    container.appendChild(div);
    try{
      var t = new bootstrap.Toast(div, { delay: 4000, autohide: true });
      t.show();
      div.addEventListener('hidden.bs.toast', function(){ div.remove(); });
    }catch(e){
      // Fallback: alert
      try { alert(String(message)); } catch(_) {}
    }
  }
  global.showToast = showToast;
})(window);
