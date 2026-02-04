/* Admin 页面 JavaScript */
var API_BASE_URL = window.location.protocol + '//' + window.location.host;
var allSystems = [];
var currentPage = 1;
var pageSize = 20;
var totalCount = 0;
var totalPages = 0;

var tableWrap = null;
var formModal = null;
var cardModal = null;
var totalCountEl = null;
var editingSystemId = null;
var mode = 'create';

document.addEventListener('DOMContentLoaded', function() {
  tableWrap = document.getElementById('tableWrap');
  formModal = document.getElementById('formModal');
  cardModal = formModal;
  totalCountEl = document.getElementById('totalCount');
  
  var newBtn = document.getElementById('newBtn');
  var refreshBtn = document.getElementById('refreshBtn');
  var modalClose = document.getElementById('modalClose');
  var cancelBtn = document.getElementById('cancelBtn');
  var systemForm = document.getElementById('systemForm');
  
  if (newBtn) newBtn.addEventListener('click', function() { editingSystemId = null; resetForm(); cardModal.style.display = 'block'; });
  if (refreshBtn) refreshBtn.addEventListener('click', refreshList);
  if (modalClose) modalClose.addEventListener('click', closeModal);
  if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
  if (systemForm) systemForm.addEventListener('submit', handleFormSubmit);
  
  refreshList();
});

function resetForm() {
  document.getElementById('system_id').value = '';
  document.getElementById('name').value = '';
  document.getElementById('capacity').value = '';
  document.getElementById('latitude').value = '';
  document.getElementById('longitude').value = '';
  document.getElementById('tiltAngle').value = '';
  document.getElementById('azimuth').value = '';
  document.getElementById('panel_count').value = '';
  document.getElementById('panelWattage').value = '';
  document.getElementById('inverterModel').value = '';
  var isActiveSelect = document.getElementById('is_active');
  if (isActiveSelect) isActiveSelect.value = 'true';
  else document.getElementById('is_active').checked = true;
  document.getElementById('submitBtn').textContent = '创建系统';
  mode = 'create';
}

function collectForm() {
  var pc = document.getElementById('panel_count');
  var pw = document.getElementById('panelWattage');
  var panelCount = pc ? parseInt(pc.value) : null;
  var panelWattage = pw ? parseFloat(pw.value) : null;
  if (isNaN(panelCount)) panelCount = null;
  if (isNaN(panelWattage)) panelWattage = null;
  var capacity = (panelCount && panelWattage) ? (panelCount * panelWattage / 1000) : null;
  var isActiveSelect = document.getElementById('is_active');
  var isActiveValue = isActiveSelect ? isActiveSelect.value : 'true';
  return {
    system_id: document.getElementById('system_id').value.trim(),
    name: document.getElementById('name').value.trim(),
    capacity: capacity,
    panel_count: panelCount,
    panel_wattage: panelWattage,
    inverter_model: document.getElementById('inverterModel') ? document.getElementById('inverterModel').value.trim() : null,
    latitude: parseFloat(document.getElementById('latitude').value) || null,
    longitude: parseFloat(document.getElementById('longitude').value) || null,
    tilt_angle: parseFloat(document.getElementById('tiltAngle').value) || null,
    azimuth: parseFloat(document.getElementById('azimuth').value) || null,
    is_active: isActiveValue === 'true'
  };
}

function refreshList() {
  var url = API_BASE_URL + '/systems/?limit=1000';
  fetch(url).then(function(r) { 
    if (!r.ok) throw new Error('HTTP ' + r.status); 
    return r.json(); 
  }).then(function(d) { 
    var allData = d.systems || d || []; 
    totalCount = allData.length; 
    totalPages = Math.ceil(totalCount / pageSize); 
    var offset = (currentPage - 1) * pageSize; 
    allSystems = allData.slice(offset, offset + pageSize); 
    if (totalCountEl) totalCountEl.textContent = totalCount; 
    renderTable(); 
    renderPagination(); 
  }).catch(function(e) { 
    if (tableWrap) tableWrap.innerHTML = '<div style="padding:20px;color:red;">❌ 加载失败: ' + e.message + '</div>'; 
  });
}

function renderTable() {
  if (!tableWrap) return;
  if (allSystems.length === 0) { tableWrap.innerHTML = '<div style="padding:20px;text-align:center;color:#999;">暂无数据</div>'; return; }
  var rows = allSystems.map(function(item) {
    var cap = (item.panel_count && item.panel_wattage) ? (item.panel_count * item.panel_wattage / 1000).toFixed(2) : (item.capacity || '-');
    var sts = item.is_active ? '<span style="color:green;">●</span> 启用' : '<span style="color:gray;">●</span> 停用';
    var eid = 'e_' + item.system_id.replace(/[^a-zA-Z0-9]/g, '_');
    var did = 'd_' + item.system_id.replace(/[^a-zA-Z0-9]/g, '_');
    return '<tr><td>' + esc(item.name) + '</td><td>' + cap + ' kW</td><td>' + (item.location_name || ('📍 ' + (item.latitude||'-') + ',' + (item.longitude||'-'))) + '</td><td>' + sts + '</td><td><button id="' + eid + '" class="btn-edit">编辑</button> <button id="' + did + '" class="btn-delete">删除</button></td></tr>';
  }).join('');
  tableWrap.innerHTML = '<table><thead><tr><th>名称</th><th>容量(kW)</th><th>地址</th><th>状态</th><th>操作</th></tr></thead><tbody>' + rows + '</tbody></table>';
  allSystems.forEach(function(item) {
    var eid = 'e_' + item.system_id.replace(/[^a-zA-Z0-9]/g, '_');
    var did = 'd_' + item.system_id.replace(/[^a-zA-Z0-9]/g, '_');
    var eb = document.getElementById(eid);
    var db = document.getElementById(did);
    if (eb) eb.addEventListener('click', function() { editSystem(item.system_id); });
    if (db) db.addEventListener('click', function() { deleteSystem(item.system_id); });
  });
}

function renderPagination() {
  var paginationContainer = document.getElementById('pagination');
  if (!paginationContainer) return;
  
  if (totalPages <= 1) {
    paginationContainer.innerHTML = '';
    return;
  }
  
  var html = '<div class="pagination">';
  
  if (currentPage > 1) {
    html += '<button class="page-btn" onclick="goToPage(' + (currentPage - 1) + ')">← 上一页</button>';
  } else {
    html += '<button class="page-btn" disabled>← 上一页</button>';
  }
  
  for (var i = 1; i <= totalPages; i++) {
    if (i === currentPage) {
      html += '<button class="page-btn active">' + i + '</button>';
    } else if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
      html += '<button class="page-btn" onclick="goToPage(' + i + ')">' + i + '</button>';
    } else if (i === currentPage - 3 || i === currentPage + 3) {
      html += '<span class="page-ellipsis">...</span>';
    }
  }
  
  if (currentPage < totalPages) {
    html += '<button class="page-btn" onclick="goToPage(' + (currentPage + 1) + ')">下一页 →</button>';
  } else {
    html += '<button class="page-btn" disabled>下一页 →</button>';
  }
  
  html += '</div>';
  paginationContainer.innerHTML = html;
}

function goToPage(page) {
  if (page < 1 || page > totalPages) return;
  currentPage = page;
  window.scrollTo(0, 0);
  refreshList();
}

function editSystem(sid) {
  var s = allSystems.find(function(x) { return x.system_id === sid; });
  if (!s) {
    fetch(API_BASE_URL + '/systems/' + sid).then(function(r) { return r.json(); }).then(function(s) {
      document.getElementById('system_id').value = s.system_id;
      document.getElementById('system_id').readOnly = true;
      document.getElementById('name').value = s.name;
      document.getElementById('capacity').value = s.capacity || '';
      document.getElementById('latitude').value = s.latitude || '';
      document.getElementById('longitude').value = s.longitude || '';
      document.getElementById('tiltAngle').value = s.tilt_angle || '';
      document.getElementById('azimuth').value = s.azimuth || '';
      document.getElementById('panel_count').value = s.panel_count || '';
      document.getElementById('panelWattage').value = s.panel_wattage || '';
      document.getElementById('inverterModel').value = s.inverter_model || '';
      var isActiveSelect = document.getElementById('is_active');
      if (isActiveSelect) isActiveSelect.value = s.is_active ? 'true' : 'false';
      document.getElementById('submitBtn').textContent = '保存更新';
      cardModal.style.display = 'block';
      editingSystemId = sid;
      mode = 'edit';
    });
  } else {
    document.getElementById('system_id').value = s.system_id;
    document.getElementById('system_id').readOnly = true;
    document.getElementById('name').value = s.name;
    document.getElementById('capacity').value = s.capacity || '';
    document.getElementById('latitude').value = s.latitude || '';
    document.getElementById('longitude').value = s.longitude || '';
    document.getElementById('tiltAngle').value = s.tilt_angle || '';
    document.getElementById('azimuth').value = s.azimuth || '';
    document.getElementById('panel_count').value = s.panel_count || '';
    document.getElementById('panelWattage').value = s.panel_wattage || '';
    document.getElementById('inverterModel').value = s.inverter_model || '';
    var isActiveSelect = document.getElementById('is_active');
    if (isActiveSelect) isActiveSelect.value = s.is_active ? 'true' : 'false';
    document.getElementById('submitBtn').textContent = '保存更新';
    cardModal.style.display = 'block';
    editingSystemId = sid;
    mode = 'edit';
  }
}

function deleteSystem(sid) {
  if (!confirm('确认删除系统 ' + sid + ' 吗?')) return;
  fetch(API_BASE_URL + '/systems/' + sid, { method: 'DELETE' }).then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); alert('删除成功'); refreshList(); }).catch(function(e) { alert('删除失败: ' + e.message); });
}

function handleFormSubmit(e) {
  e.preventDefault();
  var fd = collectForm();
  if (!fd.system_id) { alert('系统 ID 不能为空'); return; }
  if (!fd.name) { alert('系统名称不能为空'); return; }
  var m = editingSystemId ? 'PUT' : 'POST';
  var u = editingSystemId ? (API_BASE_URL + '/systems/' + editingSystemId) : (API_BASE_URL + '/systems/');
  fetch(u, { method: m, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fd) }).then(function(r) { if (!r.ok) return r.json().then(function(err) { throw new Error(err.detail || 'HTTP ' + r.status); }); return r.json(); }).then(function() { alert(editingSystemId ? '更新成功' : '创建成功'); closeModal(); refreshList(); }).catch(function(e) { alert('操作失败: ' + e.message); });
}

function closeModal() {
  cardModal.style.display = 'none';
  editingSystemId = null;
  document.getElementById('system_id').readOnly = false;
  document.getElementById('systemForm').reset();
}

function esc(s) { return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
