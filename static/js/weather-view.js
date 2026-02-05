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
      // 更新实时数据时间戳（使用中国时区）
      const currentUpdateEl = document.getElementById('currentUpdateTime');
      if (currentUpdateEl && data.fetched_at) {
        const raw = data.fetched_at;
        const hasTz = /[zZ]|[+-]\d\d:\d\d$/.test(raw);
        const iso = hasTz ? raw : `${raw}Z`;
        const d = new Date(iso);
        const fmt = new Intl.DateTimeFormat('zh-CN', {
          timeZone: 'Asia/Shanghai',
          year: 'numeric', month: '2-digit', day: '2-digit',
          hour: '2-digit', minute: '2-digit', hour12: false
        });
        const parts = Object.fromEntries(fmt.formatToParts(d).map((p) => [p.type, p.value]));
        const timeStr = `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`;
        currentUpdateEl.textContent = `最后更新: ${timeStr}`;
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
async function loadForecastData() {
  try {
    if (!selectedSystem) return;
    
    updateStatus('📊 正在获取预报数据...');
    const response = await fetch(
      `/weather/forecast_cached?system_id=${selectedSystem.system_id}&days=2`
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

    // 获取实际采集的辐射数据
    let measuredData = [];
    try {
      updateStatus('📊 获取实际辐射数据...');
      // 使用预报数据的时间范围来查询实际数据
      const firstTime = todayTimes[0]; // e.g., "2026-02-05T00:00"
      
      if (firstTime && typeof firstTime === 'string') {
        // 从预报时间提取日期
        const dateStr = firstTime.split('T')[0]; // "2026-02-05"
        // 查询该日期的整个UTC时段
        const [year, month, day] = dateStr.split('-').map(Number);
        const todayStart = new Date(Date.UTC(year, month - 1, day, 0, 0, 0));
        const todayEnd = new Date(Date.UTC(year, month - 1, day + 1, 0, 0, 0));
        
        const measuredResponse = await fetch(
          `/weather/measured_radiation?system_id=${selectedSystem.system_id}` +
          `&start_time=${todayStart.toISOString()}` +
          `&end_time=${todayEnd.toISOString()}`
        );
        
        if (measuredResponse.ok) {
          measuredData = await measuredResponse.json();
          console.log('实际辐射数据:', measuredData);
        } else {
          console.warn('获取实际辐射数据失败，HTTP:', measuredResponse.status);
        }
      }
      
      createRadiationChart(timeLabels, todayRadiationData, measuredData);
    } catch (error) {
      console.warn('获取实际辐射数据失败:', error);
      createRadiationChart(timeLabels, todayRadiationData, []);
    }
    
    createTemperatureChart(timeLabels, todayTemperatureData);

    const radiationTimeEl = document.getElementById('radiationUpdateTime');
    const temperatureTimeEl = document.getElementById('temperatureUpdateTime');
    // 图表“最后更新”显示数据库返回的预报入库时间（UTC）
    let lastStr = null;
    if (forecastData.fetched_at) {
      const raw = forecastData.fetched_at;
      const hasTz = /[zZ]|[+-]\d\d:\d\d$/.test(raw);
      const iso = hasTz ? raw : `${raw}Z`;
      const d = new Date(iso);
      if (!Number.isNaN(d.getTime())) {
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
        lastStr = `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`;
      }
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
function createRadiationChart(labels, data, measuredData = []) {
  const ctx = document.getElementById('radiationChart');
  if (!ctx) return;

  if (currentChart) {
    currentChart.destroy();
  }

  // 根据时间标签对齐实测数据
  // 实测数据是对象数组，需要提取对应时间点的辐射值
  // labels 格式为 ['00:00', '01:00', '02:00', ...]
  // measuredData 格式为 [{timestamp: '...', irradiance: 300}, ...]
  const alignedMeasuredData = labels.map(timeLabel => {
    // 找到对应时间点的实测数据
    const timeStr = timeLabel; // e.g., "00:00"
    // 在 measuredData 中查找时间匹配的项
    const match = measuredData.find(m => {
      if (!m.timestamp) return false;
      const mTime = new Date(m.timestamp);
      const mTimeStr = mTime.getHours().toString().padStart(2, '0') + ':' + 
                      mTime.getMinutes().toString().padStart(2, '0');
      return mTimeStr === timeStr;
    });
    return match ? match.irradiance : null;
  });

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
        {
          label: '实测辐射 (W/m²)',
          data: alignedMeasuredData,
          borderColor: 'rgba(59, 130, 246, 1)',
          backgroundColor: 'rgba(59, 130, 246, 0)',
          tension: 0.3,
          fill: false,
          pointRadius: 2,
          pointHoverRadius: 4,
          borderDash: [5, 5],
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
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'W/m²',
          },
        },
      },
    },
  });
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
