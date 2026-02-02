# 光伏数据分析平台 - AI 编码指南

## 项目概述

基于 FastAPI 的光伏（太阳能）监控系统时序数据平台。架构涵盖以下关键层次：
- **API 层** (`app/api/`): 测量数据和系统配置的路由处理器
- **数据库层** (`app/database/`): SQLAlchemy ORM 和会话管理
- **模型** (`app/models/`): `Measurement` 和 `SystemConfiguration` 的 SQLAlchemy ORM 模型
- **模式** (`app/schemas/`): 用于请求/响应验证的 Pydantic 模型

## 关键架构模式

### 1. 时区处理（系统范围内的模式）
**模式**: 系统有位置坐标 → 自动时区检测 → 时区感知的响应序列化。
- `SystemConfiguration` 存储纬度/经度 → `_resolve_timezone()` 通过 `timezonefinder` 自动检测
- 测量数据以 UTC 时间戳存储；响应包含根据系统时区计算的 `local_time`
- 实现参考：[app/api/measurements.py](app/api/measurements.py#L7-L12) 和 [app/api/systems.py](app/api/systems.py#L14-L19)

### 2. 批量操作模式
**设计选择**: 测量数据同时提供单条和批量端点。
- 单条: `POST /measurements/` → 适用于实时单个读数
- 批量: `POST /measurements/batch` → 适用于批量数据导入
- 两者通过可复用的 `_serialize_measurement()` 辅助函数应用相同的时区逻辑
- 参考：[app/api/measurements.py](app/api/measurements.py#L65-L85)

### 3. 数据库访问模式
- 所有数据库访问通过 SQLAlchemy ORM 和 FastAPI 依赖注入（`Depends(get_db)`）
- 会话在请求后自动关闭；参考 [app/database/database.py](app/database/database.py#L21-L27)
- 复合索引 `ix_measurements_system_timestamp` 优化按 system_id 的时序查询

### 4. 错误处理
- 使用 `HTTPException` 处理 API 错误（400 表示验证失败，404 表示未找到）
- 示例：[app/api/systems.py](app/api/systems.py#L30-L35) 中的系统 ID 唯一性检查

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

### 数据库初始化
- `init_db()` 在应用启动时调用（参考 [main.py#L71-L75](main.py#L71-L75)）
- 自动从 SQLAlchemy 模型创建所有表
- 当前无独立迁移设置（未来考虑使用 Alembic 用于生产环境）

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
- 参考 [app/schemas/measurement.py](app/schemas/measurement.py#L13-L27) 中的模式示例

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
