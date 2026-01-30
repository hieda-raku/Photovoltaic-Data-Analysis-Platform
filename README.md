# 光伏数据分析平台

一个用于光伏监控系统的简易后端服务，基于 Python 3.11、FastAPI、PostgreSQL 与 SQLAlchemy 构建。

## 概览

该平台提供 REST API，用于接收与管理来自光伏（太阳能板）系统的时序传感器数据。包含测量数据与系统配置的数据库模型，以及用于光伏性能分析的计算模块。

## 特性

- **REST API**：基于 FastAPI 的数据写入与查询接口
- **时序数据**：高效存储与查询传感器测量数据
- **系统管理**：多套光伏系统配置管理
- **性能计算**：光伏分析占位模块（效率、性能比等）
- **自动文档**：交互式 API 文档位于 `/docs` 与 `/redoc`

## 技术栈

- **Python 3.11**：具备最新特性的现代 Python
- **FastAPI**：高性能异步 Web 框架
- **PostgreSQL**：用于时序数据的可靠关系型数据库
- **SQLAlchemy**：数据库交互 ORM
- **Pydantic**：数据校验与序列化
- **Uvicorn**：用于运行应用的 ASGI 服务器

## 项目结构

```
.
├── app/
│   ├── api/                    # API 路由处理
│   │   ├── measurements.py     # 测量数据接口
│   │   └── systems.py          # 系统配置接口
│   ├── calculations/           # 光伏性能计算模块
│   │   └── pv_performance.py   # 性能计算函数
│   ├── database/               # 数据库配置
│   │   └── database.py         # SQLAlchemy 初始化与会话管理
│   ├── models/                 # 数据库模型
│   │   ├── measurement.py      # 测量数据模型
│   │   └── system_config.py    # 系统配置模型
│   └── schemas/                # Pydantic 模式
│       ├── measurement.py      # 测量请求/响应模式
│       └── system_config.py    # 系统配置模式
├── main.py                     # 应用入口
├── requirements.txt            # Python 依赖
└── README.md                   # 本文件
```

## 安装

### 前置条件

- Python 3.11 或更高版本
- PostgreSQL 12 或更高版本
- pip（Python 包管理器）

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/hieda-raku/Photovoltaic-Data-Analysis-Platform.git
   cd Photovoltaic-Data-Analysis-Platform
   ```

2. **创建虚拟环境**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置 PostgreSQL 数据库**
   ```bash
   # 创建数据库
   createdb photovoltaic_db
   
   # 或使用 psql
   psql -U postgres
   CREATE DATABASE photovoltaic_db;
   ```

5. **配置环境变量**（可选）
   ```bash
   cp .env.example .env
   # 编辑 .env，填写数据库连接信息
   ```

6. **运行应用**
   ```bash
   python main.py
   ```
   
   或直接使用 uvicorn：
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

API 地址如下：
- **API**：http://localhost:8000
- **交互式文档**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

## API 接口

### 测量数据

- `POST /measurements/` - 创建单条测量记录
- `POST /measurements/batch` - 批量创建测量记录
- `GET /measurements/` - 获取测量记录（支持过滤）
- `GET /measurements/{id}` - 获取指定测量记录
- `DELETE /measurements/{id}` - 删除测量记录

### 系统配置

- `POST /systems/` - 创建系统配置
- `GET /systems/` - 获取所有系统配置
- `GET /systems/{system_id}` - 获取指定系统配置
- `PUT /systems/{system_id}` - 更新系统配置
- `DELETE /systems/{system_id}` - 删除系统配置

### 健康检查与信息

- `GET /` - API 信息
- `GET /health` - 健康检查接口

## 使用示例

### 创建系统配置

```bash
curl -X POST "http://localhost:8000/systems/" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "PV-001",
    "name": "Rooftop Solar Array",
    "capacity": 10.0,
    "panel_count": 40,
    "latitude": 37.7749,
    "longitude": -122.4194
  }'
```

### 写入测量数据

```bash
curl -X POST "http://localhost:8000/measurements/" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "PV-001",
    "voltage": 48.5,
    "current": 12.3,
    "power": 596.55,
    "irradiance": 850.0,
    "temperature": 35.2
  }'
```

### 查询测量数据

```bash
# 获取指定系统最近的测量记录
curl "http://localhost:8000/measurements/?system_id=PV-001&limit=10"

# 获取指定时间范围内的测量记录
curl "http://localhost:8000/measurements/?start_time=2024-01-01T00:00:00Z&end_time=2024-01-31T23:59:59Z"
```

## 数据模型

### Measurement（测量数据）

存储时序传感器数据：
- `system_id`：光伏系统标识
- `timestamp`：测量时间
- `voltage`：电压（V）
- `current`：电流（A）
- `power`：功率输出（W）
- `irradiance`：太阳辐照度（W/m²）
- `temperature`：组件温度（°C）
- `ambient_temperature`：环境温度（°C）
- `energy`：能量（Wh）
- `efficiency`：系统效率（%）

### System Configuration（系统配置）

存储光伏系统元数据：
- `system_id`：系统唯一标识
- `name`：系统名称
- `capacity`：装机容量（kW）
- `panel_count`：组件数量
- `location`：物理位置
- `latitude`/`longitude`：地理坐标
- `tilt_angle`：组件倾角
- `azimuth`：组件方位角
- `is_active`：系统启用状态

## 性能计算模块

`app/calculations/pv_performance.py` 模块提供以下占位函数：

- **效率计算**：根据功率与辐照度计算系统效率
- **性能比**：比较实际与理论发电量
- **能量估算**：估算日/月发电量
- **异常检测**：识别传感器数据中的异常模式
- **衰减分析**：计算组件随时间的衰减情况

示例用法：
```python
from app.calculations import calculate_efficiency, estimate_daily_energy

# 计算效率
efficiency = calculate_efficiency(power=596.55, irradiance=850.0, area=25.0)

# 估算日发电量
daily_energy = estimate_daily_energy(capacity_kw=10.0, peak_sun_hours=5.0)
```

## 数据库结构

应用在启动时会自动创建数据库表，包括：
- `measurements`：时序传感器数据，含 (system_id, timestamp) 复合索引
- `system_configurations`：光伏系统元数据，system_id 唯一

## 开发

### 开发模式运行

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

`--reload` 参数可在代码变更时自动重载。

### 数据库迁移（可选）

生产环境建议使用 Alembic 进行数据库迁移：

```bash
# 初始化 Alembic
alembic init alembic

# 生成迁移脚本
alembic revision --autogenerate -m "Initial migration"

# 应用迁移
alembic upgrade head
```

## 环境变量

- `DATABASE_URL`：PostgreSQL 连接串（默认：`postgresql://postgres:postgres@localhost:5432/photovoltaic_db`）
- `APP_HOST`：应用监听地址（默认：`0.0.0.0`）
- `APP_PORT`：应用端口（默认：`8000`）

## 说明

- **无鉴权**：这是一个未包含鉴权的最小实现，生产环境请添加鉴权中间件。
- **无前端**：该项目仅包含后端服务，可由任意前端应用调用 API。
- **已启用 CORS**：开发模式下允许所有来源。

## 未来增强

生产部署的潜在改进：
- 身份认证与授权（JWT、OAuth2）
- 限流与请求节流
- 数据聚合与分析接口
- 实时数据流（WebSockets）
- 高级异常检测算法
- 对接外部气象 API
- 告警与通知系统
- 数据导出（CSV、Excel）
- Grafana/Prometheus 监控集成

## 许可证

本项目为开源项目，采用 MIT 许可证。

## 贡献

欢迎贡献！请随时提交 Pull Request。
