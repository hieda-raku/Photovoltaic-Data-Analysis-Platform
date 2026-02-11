let currentChart = null;
let currentTemperatureChart = null;
let selectedSystem = null;

// 计算距离下一个整点还有多少毫秒
function getMillisecondsToNextHour() {
  const now = new Date();
  const nextHour = new Date(now);
  nextHour.setHours(nextHour.getHours() + 1);
  nextHour.setMinutes(0);
  nextHour.setSeconds(0);
  nextHour.setMilliseconds(0);
  return nextHour - now;
}

// 更新状态面板（已移除页面内调试区域，改为仅在控制台输出）
function updateStatus(message) {
  console.debug('[status]', message);
}

function formatFetchedAt(raw) {
  if (!raw) return null;
  const hasTz = /[zZ]|[+-]\d\d:\d\d$/.test(raw);
  if (!hasTz) {
    const cleaned = raw.replace('T', ' ');
    return cleaned.length >= 16 ? cleaned.slice(0, 16) : cleaned;
  }
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return null;
  const fmt = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
  const parts = Object.fromEntries(fmt.formatToParts(d).map((p) => [p.type, p.value]));
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`;
}


// 加载系统列表并自动选择第一个
async function loadSystems() {
  try {
    updateStatus('📍 正在加载系统列表...');
    const response = await fetch('/systems/');
    const systems = await response.json();
    const systemSelect = document.getElementById('systemSelect');
    systemSelect.innerHTML = '';

    if (systems.length === 0) {
      systemSelect.innerHTML = '<option value="">未找到系统</option>';
      updateStatus('⚠️ 未找到任何系统');
      return;
    }

    systems.forEach((system) => {
      const option = document.createElement('option');
      option.value = system.system_id;
      option.textContent = `${system.name} (${system.system_id})`;
      systemSelect.appendChild(option);
    });

    // 自动选择第一个系统
    systemSelect.value = systems[0].system_id;
    selectedSystem = systems[0];
    updateStatus(`✅ 已加载 ${systems.length} 个系统，选中: ${systems[0].name}`);

    // 加载该系统的数据
    await loadCurrentWeatherData();
    await loadForecastData();
  } catch (error) {
    console.error('加载系统失败:', error);
    updateStatus(`❌ 加载系统失败: ${error.message}`);
  }
}

// 加载当前天气数据
async function loadCurrentWeatherData() {
  try {
    if (!selectedSystem) return;
    
    updateStatus('☀️ 正在获取实时天气数据...');
    const response = await fetch(
      `/weather/current_cached?system_id=${selectedSystem.system_id}`
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    console.log('当前天气数据:', data);

    // 更新实时数据卡片
    const radiationEl = document.getElementById('currentRadiation');
    const cloudEl = document.getElementById('currentCloud');
    const tempEl = document.getElementById('currentTemp');
    const windEl = document.getElementById('currentWind');

    if (radiationEl)
      radiationEl.textContent = (data.shortwave_radiation || 0).toFixed(1);
    if (cloudEl) cloudEl.textContent = (data.cloud_cover || 0).toFixed(0);
    if (tempEl) tempEl.textContent = (data.temperature_2m || 0).toFixed(1);
    if (windEl) windEl.textContent = (data.wind_speed_10m || 0).toFixed(1);
      // 更新实时数据时间戳（使用本地时间）
      const currentUpdateEl = document.getElementById('currentUpdateTime');
      if (currentUpdateEl && data.fetched_at) {
        const timeStr = formatFetchedAt(data.fetched_at);
        if (timeStr) currentUpdateEl.textContent = `最后更新: ${timeStr}`;
      }


    const lastUpdateEl = document.getElementById('lastUpdate');
    if (lastUpdateEl) {
      lastUpdateEl.textContent = `最后更新: ${new Date().toLocaleString(
        'zh-CN'
      )}`;
    }

    updateStatus('✅ 实时数据已更新');
  } catch (error) {
    console.error('加载实时天气失败:', error);
    updateStatus(`❌ 加载实时天气失败: ${error.message}`);
  }
}

// 加载天气预报数据
// 辅助函数：将一分钟级别的实测数据按小时聚合，并平滑处理
async function loadForecastData() {
  try {
    if (!selectedSystem) return;
    
    updateStatus('📊 正在获取预报数据...');
    const response = await fetch(
      `/weather/forecast?system_id=${selectedSystem.system_id}&days=2`
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const forecastData = await response.json();
    console.log('预报数据:', forecastData);

    const system = selectedSystem;
    const hourly = forecastData.hourly || {};
    const times = hourly.time || [];
    const radiationData = hourly.shortwave_radiation || [];
    const temperatureData = hourly.temperature_2m || [];

    // 只显示当天 00:00-23:00 的数据（24 小时）
    // Open-Meteo 返回时间格式如 2026-02-04T00:00
    const today = times[0] ? times[0].split('T')[0] : '';
    const indices = [];
    times.forEach((t, idx) => {
      if (t.startsWith(today)) {
        indices.push(idx);
      }
    });

    // 过滤数据为当天 24 小时
    const todayTimes = indices.map(i => times[i]);
    const todayRadiationData = indices.map(i => radiationData[i]);
    const todayTemperatureData = indices.map(i => temperatureData[i]);

    // Open-Meteo 在设置 timezone 后返回的是本地时间字符串（如 2026-02-04T00:00）
    // 这里直接取时分，避免再次时区转换导致 +8 小时偏移
    const timeLabels = todayTimes.map((t) => {
      if (typeof t === 'string' && t.includes('T')) {
        return t.split('T')[1];
      }
      return t;
    });

        // 显示完整 24 小时（00:00-23:00），不再按当前时间截断
    const displayLabels = timeLabels;
    const displayRadiation = todayRadiationData;

    console.log(`📊 显示范围: 00:00 - ${displayLabels[displayLabels.length - 1]}`);
    createRadiationChart(displayLabels, displayRadiation);

createTemperatureChart(timeLabels, todayTemperatureData);

    const radiationTimeEl = document.getElementById('radiationUpdateTime');
    const temperatureTimeEl = document.getElementById('temperatureUpdateTime');
    // 图表“最后更新”显示数据库返回的预报入库时间（本地时间）
    let lastStr = null;
    if (forecastData.fetched_at) {
      lastStr = formatFetchedAt(forecastData.fetched_at);
    }

    if (!lastStr) {
      lastStr = new Date().toLocaleString('zh-CN');
    }
    if (radiationTimeEl) radiationTimeEl.textContent = `最后更新: ${lastStr}`;
    if (temperatureTimeEl) temperatureTimeEl.textContent = `最后更新: ${lastStr}`;
    updateStatus('✅ 预报数据已加载');
  } catch (error) {
    console.error('加载预报数据失败:', error);
    updateStatus(`❌ 加载预报数据失败: ${error.message}`);
  }
}

// 创建辐射图表
function createRadiationChart(labels, data) {
  const ctx = document.getElementById('radiationChart');
  if (!ctx) return;

  if (currentChart) {
    currentChart.destroy();
  }

  // measuredData已在主函数中聚合为alignedMeasuredData传入
  // 这里直接使用传入的measuredData参数

  currentChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: '预报辐射 (W/m²)',
          data: data,
          borderColor: 'rgba(249, 115, 22, 1)',
          backgroundColor: 'rgba(249, 115, 22, 0.1)',
          tension: 0.3,
          fill: true,
          pointRadius: 3,
          pointHoverRadius: 5,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
        },
        title: {
          display: true,
          text: '太阳辐射 - 时间标签为本地时间 (Asia/Shanghai UTC+8)',
          font: { size: 14, weight: 'bold' },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'W/m²',
          },
        },
        x: {
          title: {
            display: true,
            text: '本地时间 (Asia/Shanghai)',
          },
        },
      },
    },
  });
  
  // 调试输出
  console.log('📊 辐射图表数据对齐检查:');
  console.log('  时间标签数量:', labels.length);
  console.log('  预报数据数量:', data.length);
  console.log('  实测数据数量:', measuredData.length);
  console.log('  对齐后实测数量:', measuredData.filter(x => x !== null).length);
  console.log('  时间标签(首8个):', labels.slice(0, 8));
  console.log('  预报数据(首8个):', data.slice(0, 8));
  if (measuredData.filter(x => x !== null).length > 0) {
    console.log('  ✅ 实测数据成功对齐:', measuredData);
  } else {
    console.warn('  ⚠️ 实测数据对齐失败，全为null');
    if (measuredData.length > 0) {
      console.warn('    原始实测数据:', measuredData);
    }
  }
}

// 创建温度图表
function createTemperatureChart(labels, data) {
  const ctx = document.getElementById('temperatureChart');
  if (!ctx) return;

  if (currentTemperatureChart) {
    currentTemperatureChart.destroy();
  }

  currentTemperatureChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: '气温 (°C)',
          data: data,
          borderColor: 'rgba(239, 68, 68, 1)',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          tension: 0.3,
          fill: true,
          pointRadius: 3,
          pointHoverRadius: 5,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
        },
        title: {
          display: true,
          text: '太阳辐射 - 时间标签为本地时间 (Asia/Shanghai UTC+8)',
          font: { size: 14, weight: 'bold' },
        },
      },
      scales: {
        y: {
          title: {
            display: true,
            text: '°C',
          },
        },
      },
    },
  });
}

// 启动定时轮询：实时数据每5分钟，预报数据只在整点
function scheduleRefresh() {
  // 1. 实时天气数据：每5分钟拉取一次（不受整点限制）
  setInterval(async () => {
    updateStatus('☀️ [定时更新] 实时数据...');
    await loadCurrentWeatherData();
  }, 5 * 60 * 1000); // 每5分钟

  // 2. 预报数据：只在整点时刻拉取
  const msToNextHour = getMillisecondsToNextHour();
  const nextHourTime = new Date(Date.now() + msToNextHour);
  
  updateStatus(`⏱️ 已设置定时轮询 - 预报数据下次拉取时间: ${nextHourTime.toLocaleTimeString('zh-CN')}`);
  
  // 等待到整点，然后执行一次拉取
  setTimeout(async () => {
    updateStatus(`📊 [整点轮询] 拉取预报数据...`);
    await loadForecastData();
    
    // 之后每小时轮询一次（整点时刻）
    setInterval(async () => {
      updateStatus(`📊 [整点轮询] 拉取预报数据...`);
      await loadForecastData();
    }, 60 * 60 * 1000); // 每60分钟拉取一次
  }, msToNextHour);
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
  updateStatus('🚀 页面初始化中...');

  const systemSelect = document.getElementById('systemSelect');
  if (systemSelect) {
    systemSelect.addEventListener('change', async (e) => {
      const systems = await fetch('/systems/').then((r) => r.json());
      selectedSystem = systems.find((s) => s.system_id === e.target.value);
      if (selectedSystem) {
        updateStatus(`🔄 切换到系统: ${selectedSystem.name}`);
        await loadCurrentWeatherData();
        await loadForecastData();
      }
    });
  }

  const btnRefresh = document.getElementById('btnRefresh');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', async () => {
      updateStatus('🔄 手动刷新中...');
      await loadCurrentWeatherData();
      await loadForecastData();
    });
  }

  // 自动加载系统和数据
  loadSystems().then(() => {
    // 系统加载完成后，启动定时轮询
    scheduleRefresh();
  });
});
