# 光伏数据分析平台 - AI 编码指南

## 项目概述

基于 FastAPI 的光伏（太阳能）监控系统时序数据平台。架构涵盖以下关键层次：
- **API 层** (`app/api/`): 测量数据和系统配置的路由处理器
- **数据库层** (`app/database/`): SQLAlchemy ORM 和会话管理
- **模型** (`app/models/`): `Measurement` 和 `SystemConfiguration` 的 SQLAlchemy ORM 模型
- **模式** (`app/schemas/`): 用于请求/响应验证的 Pydantic 模型
- **计算层** (`app/calculations/`): 光伏性能分析占位模块（可扩展）

## 关键架构模式

### 1. 时区处理（系统范围内的模式）
**模式**: 系统有位置坐标 → 自动时区检测 → 时区感知的响应序列化。
- `SystemConfiguration` 存储纬度/经度 → `_resolve_timezone()` 通过 `timezonefinder` 自动检测
- 测量数据以 UTC 时间戳存储；响应包含根据系统时区计算的 `local_time`
- **关键实现**: `_compute_local_time()` 在 [app/api/measurements.py](app/api/measurements.py#L18-L24) 转换 UTC → 本地时区
- 时区存储在系统配置中，由 `_resolve_timezone()` 在 [app/api/systems.py](app/api/systems.py#L17-L21) 自动检测

### 2. 批量操作模式
**设计选择**: 测量数据同时提供单条和批量端点。
- 单条: `POST /measurements/` → 适用于实时单个读数
- 批量: `POST /measurements/batch` → 适用于批量数据导入（高效写入多条记录）
- 两者通过可复用的 `_serialize_measurement()` 辅助函数应用相同的时区逻辑
- 批量操作使用 `db.add_all()` 一次性提交，参考 [app/api/measurements.py](app/api/measurements.py#L89)

### 3. 数据库访问模式
- 所有数据库访问通过 SQLAlchemy ORM 和 FastAPI 依赖注入（`Depends(get_db)`）
- 会话在请求后自动关闭；参考 [app/database/database.py](app/database/database.py#L21-L27)
- 复合索引 `ix_measurements_system_timestamp` 优化按 system_id 的时序查询（见 [app/models/measurement.py](app/models/measurement.py#L28-L30)）
- **数据库 URL 配置**: 通过环境变量 `DATABASE_URL` 或使用默认值 `postgresql://postgres:postgres@localhost:5432/photovoltaic_db`

### 4. 错误处理与验证
- 使用 `HTTPException` 处理 API 错误（400 表示验证失败，404 表示未找到）
- 示例：[app/api/systems.py](app/api/systems.py#L34-L38) 中的系统 ID 唯一性检查
- Pydantic 模式自动验证请求数据；自定义验证逻辑放在 API 处理器中

## 开发工作流

### 设置
```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 设置数据库 URL（默认：localhost PostgreSQL）
# 可设置 DATABASE_URL 环境变量或使用 app/database/database.py 中的默认值
```

### 运行
```bash
# 开发环境（自动重载）
python main.py  # 或 uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API 文档位置：
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

### 数据库初始化与迁移
- `init_db()` 在应用启动时调用（参考 [main.py](main.py#L71-L75) 的 `@app.on_event("startup")`）
- 自动从 SQLAlchemy 模型创建所有表（`Base.metadata.create_all()`）
- **注意**: 当前使用简单的表创建模式，未使用 Alembic 迁移（虽然已安装 alembic==1.13.1）
- 生产环境建议配置 Alembic 用于版本化迁移

### 测试与调试
- 使用 HTTP 请求日志中间件跟踪请求/响应（参考 [main.py](main.py#L38-L52)）
- 访问 http://localhost:8000/docs 进行交互式 API 测试（Swagger UI）
- 访问 http://localhost:8000/redoc 查看 API 文档（ReDoc）
- 访问 http://localhost:8000/admin 查看管理页面（静态 HTML）

## 项目特定约定

### 命名和结构
- **system_id**: 物理光伏系统的字符串标识符（例如 "PV-001"）
- **模型与模式**: 
  - 模型 (`app/models/`) = SQLAlchemy ORM（数据库表示）
  - 模式 (`app/schemas/`) = Pydantic（请求/响应契约）
- 按功能区分（测量与系统），而非按类型区分

### 测量数据字段
必需：`system_id`，可选的环境读数：`irradiance`（W/m²）、`temperature`（°C）、`ambient_temperature`（°C）
- 时间戳以 UTC 格式存储在数据库中，响应包含根据系统时区计算的 `local_time`
- **时间戳默认值**: 如果客户端未提供 `timestamp`，API 自动使用 `datetime.utcnow()` 作为默认值
- 参考 [app/schemas/measurement.py](app/schemas/measurement.py#L13-L27) 中的模式示例

### 系统配置字段结构
- **必需字段**: `system_id`（唯一）、`name`（系统名称）
- **位置信息**: `latitude`/`longitude` → 自动触发时区检测，存储在 `timezone` 字段
- **系统规格**: `capacity`（kW）、`panel_count`、`panel_wattage`（W）、`inverter_model`
- **物理参数**: `tilt_angle`（倾角）、`azimuth`（方位角）
- **元数据**: `extra_metadata`（JSON 字段用于扩展数据）、`is_active`（启用标志）
- 参考 [app/models/system_config.py](app/models/system_config.py) 查看完整模型定义

### API 响应格式
所有响应都包含超出数据库列的计算字段：
- `local_time`: UTC 时间戳转换为系统本地时区
- 通过 `_compute_local_time()` 辅助函数在序列化期间计算
- 减少数据传输；时区逻辑保持在服务器端

### CORS 和安全注意事项
- CORS 当前允许所有来源（参考 [main.py#L60-L65](main.py#L60-L65)）- 生产环境需要修改
- HTTP 请求日志中间件用于调试（参考 [main.py#L38-L52](main.py#L38-L52)）

## 关键依赖和版本锁定
- FastAPI 0.109.1, Uvicorn 0.27.0, SQLAlchemy 2.0.25
- PostgreSQL 驱动: psycopg2-binary 2.9.9
- 时区解析: timezonefinder 6.5.2
- 完整列表参考 [requirements.txt](requirements.txt)

## 添加功能的通用模式

### 添加新的 API 端点
1. 在 `app/api/{domain}.py` 中创建处理器
2. 对查询使用 `SQLAlchemy ORM`，对会话注入使用 `Depends(get_db)`
3. 应用来自 `app/schemas/{domain}.py` 的响应模式
4. 在 [main.py#L65-L66](main.py#L65-L66) 中通过 `app.include_router()` 注册路由

### 添加数据库模型
1. 在 `app/models/{domain}.py` 中创建继承 `Base` 的类
2. 对复合查询使用 `Index()`（例如 [app/models/measurement.py#L28-L30](app/models/measurement.py#L28-L30)）
3. `init_db()` 在下次启动时自动创建

### 添加计算响应字段
遵循时区模式：在序列化期间计算（不在模型中），使用辅助函数保持路由清洁。参考 [app/api/measurements.py#L19-L21](app/api/measurements.py#L19-L21)。
4. 在 [main.py#L65-L66](main.py#L65-L66) 中通过 `app.include_router()` 注册路由

### 添加数据库模型
1. 在 `app/models/{domain}.py` 中创建继承 `Base` 的类
2. 对复合查询使用 `Index()`（例如 [app/models/measurement.py#L28-L30](app/models/measurement.py#L28-L30)）
3. `init_db()` 在下次启动时自动创建

### 添加计算响应字段
遵循时区模式：在序列化期间计算（不在模型中），使用辅助函数保持路由清洁。参考 [app/api/measurements.py#L19-L21](app/api/measurements.py#L19-L21)。
