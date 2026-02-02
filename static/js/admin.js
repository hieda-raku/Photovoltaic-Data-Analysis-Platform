/* Admin 页面 JavaScript */
var API_BASE_URL = window.location.protocol + '//' + window.location.host;
var allSystems = [];
var editingSystemId = null;
var form, tableWrap, totalCount, formTitle, formNote, submitBtn, formModal, refreshBtn, newBtn, cancelBtn, modalClose;

function initDOM() {
  form = document.getElementById('systemForm');
  tableWrap = document.getElementById('tableWrap');
  totalCount = document.getElementById('totalCount');
  formTitle = document.getElementById('formTitle');
  formNote = document.getElementById('formNote');
  submitBtn = document.getElementById('submitBtn');
  formModal = document.getElementById('formModal');
  refreshBtn = document.getElementById('refreshBtn');
  newBtn = document.getElementById('newBtn');
  cancelBtn = document.getElementById('cancelBtn');
  modalClose = document.getElementById('modalClose');
}

document.addEventListener('DOMContentLoaded', function() {
  initDOM();
  setupEventListeners();
  refreshList();
});

function setupEventListeners() {
  if (newBtn) newBtn.addEventListener('click', function() { resetForm(); openModal(); });
  if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
  if (modalClose) modalClose.addEventListener('click', closeModal);
  if (refreshBtn) refreshBtn.addEventListener('click', refreshList);
  if (form) form.addEventListener('submit', handleFormSubmit);
  if (formModal) formModal.addEventListener('click', function(e) { if (e.target === formModal) closeModal(); });
}

function openModal() { if (formModal) { formModal.classList.add('show'); document.body.style.overflow = 'hidden'; } }
function closeModal() { if (formModal) { formModal.classList.remove('show'); document.body.style.overflow = 'auto'; setTimeout(resetForm, 150); } }

function resetForm() {
  if (form) form.reset();
  editingSystemId = null;
  if (formTitle) formTitle.textContent = '新建光伏系统';
  if (submitBtn) submitBtn.textContent = '保存';
  if (formNote) formNote.textContent = '';
  var sysIdInput = document.getElementById('system_id');
  if (sysIdInput) sysIdInput.disabled = false;
}

function collectForm() {
  var pc = document.getElementById('panel_count');
  var pw = document.getElementById('panelWattage');
  var panelCount = pc ? parseInt(pc.value) : null;
  var panelWattage = pw ? parseFloat(pw.value) : null;
  if (isNaN(panelCount)) panelCount = null;
  if (isNaN(panelWattage)) panelWattage = null;
  var capacity = (panelCount && panelWattage) ? (panelCount * panelWattage / 1000) : null;
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
    is_active: document.getElementById('is_active').checked
  };
}

function refreshList() {
  fetch(API_BASE_URL + '/systems/').then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }).then(function(d) { allSystems = d.systems || d || []; if (totalCount) totalCount.textContent = allSystems.length; renderTable(); }).catch(function(e) { if (tableWrap) tableWrap.innerHTML = '<div style="padding:20px;color:red;">❌ 加载失败: ' + e.message + '</div>'; });
}

function renderTable() {
  if (!tableWrap) return;
  if (allSystems.length === 0) { tableWrap.innerHTML = '<div style="padding:20px;text-align:center;color:#999;">暂无数据</div>'; return; }
  var rows = allSystems.map(function(item) {
    var cap = (item.panel_count && item.panel_wattage) ? (item.panel_count * item.panel_wattage / 1000).toFixed(2) : (item.capacity || '-');
    var sts = item.is_active ? '<span style="color:green;">●</span> 启用' : '<span style="color:gray;">●</span> 停用';
    var eid = 'e_' + item.system_id.replace(/[^a-zA-Z0-9]/g, '_');
    var did = 'd_' + item.system_id.replace(/[^a-zA-Z0-9]/g, '_');
    return '<tr><td>' + esc(item.system_id) + '</td><td>' + esc(item.name) + '</td><td>' + cap + ' kW</td><td>' + (item.latitude||'-') + ',' + (item.longitude||'-') + '</td><td>' + sts + '</td><td><button id="' + eid + '">编辑</button> <button id="' + did + '" style="background:#999;color:white;">删除</button></td></tr>';
  }).join('');
  tableWrap.innerHTML = '<table><thead><tr><th>系统 ID</th><th>名称</th><th>容量(kW)</th><th>坐标</th><th>状态</th><th>操作</th></tr></thead><tbody>' + rows + '</tbody></table>';
  allSystems.forEach(function(item) {
    var eid = 'e_' + item.system_id.replace(/[^a-zA-Z0-9]/g, '_');
    var did = 'd_' + item.system_id.replace(/[^a-zA-Z0-9]/g, '_');
    var eb = document.getElementById(eid);
    var db = document.getElementById(did);
    if (eb) eb.addEventListener('click', function() { editSystem(item.system_id); });
    if (db) db.addEventListener('click', function() { deleteSystem(item.system_id); });
  });
}

function esc(t) { if (!t) return ''; var d = document.createElement('div'); d.textContent = t; return d.innerHTML; }

function editSystem(sid) {
  fetch(API_BASE_URL + '/systems/' + sid).then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }).then(function(s) {
    editingSystemId = sid;
    if (formTitle) formTitle.textContent = '编辑系统: ' + s.system_id;
    if (submitBtn) submitBtn.textContent = '更新';
    if (formNote) formNote.textContent = '修改信息后点击更新';
    document.getElementById('system_id').value = s.system_id;
    document.getElementById('system_id').disabled = true;
    document.getElementById('name').value = s.name || '';
    document.getElementById('panel_count').value = s.panel_count || '';
    document.getElementById('panelWattage').value = s.panel_wattage || '';
    document.getElementById('inverterModel').value = s.inverter_model || '';
    document.getElementById('latitude').value = s.latitude || '';
    document.getElementById('longitude').value = s.longitude || '';
    document.getElementById('tiltAngle').value = s.tilt_angle || '';
    document.getElementById('azimuth').value = s.azimuth || '';
    document.getElementById('is_active').checked = s.is_active || false;
    openModal();
  }).catch(function(e) { alert('加载系统信息失败: ' + e.message); });
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
