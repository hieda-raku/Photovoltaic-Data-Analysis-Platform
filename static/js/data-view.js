// 数据库已经存储本地时间(Asia/Shanghai UTC+8)，无需时区转换
// 数据查看页面逻辑

// 全局状态
let currentSystemId = null;
let currentPage = 1;
const pageSize = 20;
let totalCount = 0;
let totalPages = 0;
let allMeasurements = [];
let irradianceChart = null;
let temperatureChart = null;

// DOM 元素引用
const systemSelect = document.getElementById('systemSelect');
const selectedDateInput = document.getElementById('selectedDate');

const btnQuery = document.getElementById('btnQuery');
const btnRefresh = document.getElementById('btnRefresh');
const btnExport = document.getElementById('btnExport');
const tableWrap = document.getElementById('tableWrap');
const paginationEl = document.getElementById('pagination');
const recordCountEl = document.getElementById('recordCount');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  initDateInputs();
  loadSystems();
  bindEvents();
});

// 绑定事件
function bindEvents() {
  btnQuery.addEventListener('click', queryData);
  btnRefresh.addEventListener('click', queryData);
  btnExport.addEventListener('click', exportData);
  systemSelect.addEventListener('change', onSystemChange);

}

// 初始化日期输入（默认今天）
function initDateInputs() {
  const today = new Date().toISOString().split('T')[0];
  selectedDateInput.value = today;
}

// 加载系统列表
async function loadSystems() {
  try {
    const res = await fetch('/systems/?limit=1000');
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    
    systemSelect.innerHTML = '<option value="">-- 请选择系统 --</option>';
    
    if (Array.isArray(data) && data.length > 0) {
      data.forEach(sys => {
        const option = document.createElement('option');
        option.value = sys.system_id;
        option.textContent = `${sys.name} (${sys.system_id})`;
        systemSelect.appendChild(option);
      });
      
      currentSystemId = data[0].system_id;
      systemSelect.value = currentSystemId;
      
      // 延迟执行查询，确保 Chart.js 已加载
      setTimeout(() => queryData(), 200);
    } else {
      systemSelect.innerHTML = '<option value="">无可用系统</option>';
      showEmpty();
    }
  } catch (err) {
    console.error('加载系统列表失败:', err);
    alert('加载系统列表失败: ' + err.message);
    systemSelect.innerHTML = '<option value="">加载失败</option>';
  }
}

function onSystemChange() {
  currentSystemId = systemSelect.value;
  if (currentSystemId) {
    queryData();
  }
}

// 查询数据
// 查询数据
// 查询数据
async function queryData() {
  if (!currentSystemId) {
    alert('请先选择系统');
    return;
  }

  const selectedDate = selectedDateInput.value;

  if (!selectedDate) {
    alert('请选择日期');
    return;
  }

  // 严格查询：从当日 00:00:00 到 23:59:59（或者到现在，如果是今天）
  const parts = selectedDate.split('-');
  const year = parseInt(parts[0]);
  const month = parseInt(parts[1]);
  const day = parseInt(parts[2]);
  
  // 检查是否是今天
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const selectedDateTime = new Date(year, month - 1, day, 0, 0, 0, 0);
  
  console.log('📅 日期解析:', { selectedDate, year, month, day });
  console.log('🕰️ 数据库使用时区: Asia/Shanghai (本地时间)');
  
  const localStart = new Date(year, month - 1, day, 0, 0, 0, 0);
  
  // 如果是今天，结束时间是现在；否则是该天的23:59:59
  let localEnd;
  if (selectedDateTime.getTime() === today.getTime()) {
    localEnd = new Date();  // 当前时间
    console.log('📌 选择的是今天，查询到当前时间');
  } else {
    localEnd = new Date(year, month - 1, day, 23, 59, 59, 999);
  }
  
  console.log('🕐 本地时间:', { 
    localStart: localStart.toLocaleString('zh-CN'),
    localEnd: localEnd.toLocaleString('zh-CN')
  });
  
  // 数据库存储的是本地时间，直接格式化为ISO字符串（不带时区）
  const formatLocal = (d) => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hour = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    const sec = String(d.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day}T${hour}:${min}:${sec}`;
  };
  const localStartStr = formatLocal(localStart);
  const localEndStr = formatLocal(localEnd);
  
  console.log('🌍 本地时间查询:', {
    localStartStr: localStartStr,
    localEndStr: localEndStr
  });
  
  showLoading();

  try {
    // 单次查询获取一天的所有数据（上限1440条，对应一分钟一条数据）
    const url = `/measurements/?system_id=${currentSystemId}&start_time=${localStartStr}&end_time=${localEndStr}&limit=1440`;
    console.log('🔗 完整请求URL:', url);
    console.log('📊 URL参数:', { system_id: currentSystemId, start_time: localStartStr, end_time: localEndStr });
    
    const res = await fetch(url);
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
    const data = await res.json();
    
    if (!Array.isArray(data)) {
      throw new Error('API 返回了非数组数据');
    }

    console.log(`✅ 查询到 ${data.length} 条记录`);
    
    if (data.length > 0) {
      console.log('📝 首条记录:', data[0]);
      console.log('📝 末条记录:', data[data.length - 1]);
    }

    allMeasurements = data;
    updateChart();
    // 保留当前页码，如果超出范围则回到第1页
    const maxPage = Math.ceil(allMeasurements.length / pageSize);
    if (currentPage > maxPage) {
      currentPage = 1;
    }
    renderTable();
    
    if (allMeasurements.length === 0) {
      showEmpty();
    }
  } catch (err) {
    console.error('❌ 查询数据失败:', err);
    alert('查询数据失败: ' + err.message);
    showEmpty();
  }
}

// 更新统计数据

// 更新图表
function updateChart() {
  const irradianceCanvas = document.getElementById('irradianceChart');
  const temperatureCanvas = document.getElementById('temperatureChart');
  
  if (!irradianceCanvas || !temperatureCanvas) {
    console.error('找不到图表 canvas 元素');
    return;
  }
  
  const irradianceCtx = irradianceCanvas.getContext('2d');
  const temperatureCtx = temperatureCanvas.getContext('2d');

  // 销毁旧图表
  if (irradianceChart) {
    irradianceChart.destroy();
    irradianceChart = null;
  }
  if (temperatureChart) {
    temperatureChart.destroy();
    temperatureChart = null;
  }

  if (allMeasurements.length === 0) {
    return;
  }

  // 检查 Chart.js 是否已加载
  if (typeof Chart === 'undefined') {
    console.error('Chart.js 未加载');
    return;
  }

  // 按时间排序
  const sorted = [...allMeasurements].sort((a, b) => 
    new Date(a.timestamp) - new Date(b.timestamp)
  );

  const labels = sorted.map(m => {
    // local_time 已经是本地时间字符串（含时区 +08:00），直接截取显示
    // 格式: "2026-02-03T15:00:00+08:00"
    const timeStr = m.local_time || m.timestamp;
    if (timeStr && timeStr.includes('T')) {
      // 从 "2026-02-03T15:00:00+08:00" 提取 "02-03 15:00"
      const parts = timeStr.split('T');
      const datePart = parts[0].split('-').slice(1).join('-');  // "02-03"
      const timePart = parts[1].split(':').slice(0, 2).join(':');  // "15:00"
      return `${datePart} ${timePart}`;
    }
    return timeStr;
  });

  const irradianceData = sorted.map(m => m.irradiance);
  const temperatureData = sorted.map(m => m.temperature);

  // 通用配置
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: { size: 13 },
        bodyFont: { size: 12 }
      }
    },
    scales: {
      x: {
        grid: {
          display: false
        },
        ticks: {
          maxRotation: 45,
          minRotation: 45,
          font: { size: 11 }
        }
      }
    }
  };

  // 创建辐照度图表
  irradianceChart = new Chart(irradianceCtx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: '总辐射 (W/m²)',
          data: irradianceData,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.3,
          pointRadius: 0,              // 不显示点，避免1440个点重合
          pointHoverRadius: 6,         // 鼠标悬停时显示点
          pointHoverBackgroundColor: '#3b82f6',
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
          borderWidth: 2,
          fill: true
        }
      ]
    },
    options: {
      ...commonOptions,
      scales: {
        ...commonOptions.scales,
        y: {
          type: 'linear',
          title: {
            display: true,
            text: '总辐射 (W/m²)',
            color: '#3b82f6',
            font: { size: 12, weight: '600' }
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        }
      }
    }
  });

  // 创建温度图表
  temperatureChart = new Chart(temperatureCtx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: '设备温度 (°C)',
          data: temperatureData,
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          tension: 0.3,
          pointRadius: 0,              // 不显示点，避免1440个点重合
          pointHoverRadius: 6,         // 鼠标悬停时显示点
          pointHoverBackgroundColor: '#ef4444',
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
          borderWidth: 2,
          fill: true
        }
      ]
    },
    options: {
      ...commonOptions,
      scales: {
        ...commonOptions.scales,
        y: {
          type: 'linear',
          title: {
            display: true,
            text: '设备温度 (°C)',
            color: '#ef4444',
            font: { size: 12, weight: '600' }
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        }
      }
    }
  });
}



// 渲染数据表格
// 渲染数据表格
function renderTable() {
  totalCount = allMeasurements.length;
  totalPages = Math.ceil(totalCount / pageSize);
  recordCountEl.textContent = totalCount;

  if (totalCount === 0) {
    tableWrap.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><div class="empty-state-text">暂无数据</div><div class="empty-state-hint">该时间范围内没有数据</div></div>';
    renderPagination();
    return;
  }

  // 按时间戳从早到晚排序
  const sortedMeasurements = [...allMeasurements].sort((a, b) => 
    new Date(a.timestamp) - new Date(b.timestamp)
  );

  // 分页切片
  const start = (currentPage - 1) * pageSize;
  const end = start + pageSize;
  const pageData = sortedMeasurements.slice(start, end);

  let html = `
    <table class="table">
      <thead>
        <tr>
          <th>序号</th>
          <th>记录时间</th>
          <th>总辐射 (W/m²)</th>
          <th>设备温度 (°C)</th>
        </tr>
      </thead>
      <tbody>
  `;

  pageData.forEach((m, idx) => {
    // 使用 local_time 并格式化为本地时间（带时区）
    let displayTime = '--';
    if (m.local_time) {
      const dt = new Date(m.local_time);
      displayTime = dt.toLocaleString('zh-CN', { 
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short'
      });
    } else if (m.timestamp) {
      const dt = new Date(m.timestamp);
      displayTime = dt.toLocaleString('zh-CN', { 
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short'
      });
    }
    
    const rowNum = start + idx + 1;
    
    html += `
      <tr>
        <td>${rowNum}</td>
        <td>${esc(displayTime)}</td>
        <td>${m.irradiance !== null && m.irradiance !== undefined ? m.irradiance.toFixed(2) : '--'}</td>
        <td>${m.temperature !== null && m.temperature !== undefined ? m.temperature.toFixed(2) : '--'}</td>
      </tr>
    `;
  });
  
  html += `
      </tbody>
    </table>
  `;
  
  tableWrap.innerHTML = html;
  renderPagination();
}

// 渲染分页
function renderPagination() {
  if (totalCount === 0) {
    paginationEl.innerHTML = '';
    return;
  }

  let html = '<div class="pagination">';
  
  // 上一页
  html += `<button class="page-btn ${currentPage === 1 ? 'disabled' : ''}" onclick="goToPage(${currentPage - 1})">← 上一页</button>`;
  
  // 页码
  const maxVisible = 7;
  const startPage = Math.max(1, currentPage - 3);
  const endPage = Math.min(totalPages, startPage + maxVisible - 1);
  
  if (startPage > 1) {
    html += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
    if (startPage > 2) {
      html += `<span class="page-ellipsis">...</span>`;
    }
  }
  
  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      html += `<span class="page-ellipsis">...</span>`;
    }
    html += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
  }
  
  // 下一页
  html += `<button class="page-btn ${currentPage === totalPages ? 'disabled' : ''}" onclick="goToPage(${currentPage + 1})">下一页 →</button>`;
  
  html += '</div>';
  paginationEl.innerHTML = html;
}

// 跳转页面
function goToPage(page) {
  if (page < 1 || page > totalPages || page === currentPage) return;
  currentPage = page;
  renderTable();
  // 不自动滚动，保持用户当前位置
}
function exportData() {
  if (allMeasurements.length === 0) {
    alert('没有数据可导出');
    return;
  }

  // 添加UTF-8 BOM，让Excel正确识别中文
  let csv = '\ufeff序号,系统ID,记录时间,总辐射(W/m²),设备温度(°C)\n';
  
  allMeasurements.forEach((m, idx) => {
    const time = m.local_time || m.timestamp;
    const displayTime = new Date(time).toLocaleString('zh-CN');
    csv += `${idx + 1},${m.system_id},${displayTime},${m.irradiance || ''},${m.temperature || ''}\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  const filename = `测量数据_${currentSystemId}_${selectedDateInput.value}.csv`;
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// 显示加载状态
function showLoading() {
  tableWrap.innerHTML = `
    <div class="loading-spinner">
      <div class="spinner"></div>
      <p style="margin-top: 16px;">加载中...</p>
    </div>
  `;
  paginationEl.innerHTML = '';
}

// 显示空状态
function showEmpty() {
  tableWrap.innerHTML = `
    <div class="empty-state">
      <div class="empty-state-icon">📭</div>
      <div class="empty-state-text">暂无数据</div>
      <div class="empty-state-hint">请选择系统和时间范围后查询</div>
    </div>
  `;
  paginationEl.innerHTML = '';
  recordCountEl.textContent = '0';
  
  
  // 清空图表
  if (irradianceChart) {
    irradianceChart.destroy();
    irradianceChart = null;
  }
  if (temperatureChart) {
    temperatureChart.destroy();
    temperatureChart = null;
  }
}

// HTML 转义
function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
