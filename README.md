# 学生信息管理系统

基于 **Flask + MySQL** 构建的前后端一体化学生综合管理平台，覆盖用户认证、基础信息管理、教学教务、考勤成绩、通知公告及系统运维等模块，支持角色/权限控制、批量数据处理和基础数据可视化。

## 核心功能概览
- **账号与权限**：登录 / 注册 / 忘记密码 / 首次登陆强制改密 / 角色-权限体系（管理员、教师、学生）
- **系统仪表盘**：关键数据统计、快捷操作入口、近期公告、个人待办、消息提醒、成绩与考勤图表
- **学生管理**：搜索筛选、分页、详情、增改删、头像上传、Excel 批量导入、Excel 导出
- **班级管理**：班级维护、班主任配置、学生分班
- **教师管理**：教师档案维护、任教班级查询
- **课程管理**：课程档案、授课教师与班级关联、课表维护、选课分配
- **成绩管理**：按班级/课程录入成绩、成绩查询、多维统计图表、Excel 导出
- **考勤与请假**：按班级/课程签到、考勤统计、学生在线请假、请假审批
- **通知公告**：公告发布、置顶、按角色范围推送
- **个人中心**：资料维护、头像上传、密码修改、消息中心
- **系统设置**：用户角色分配、系统参数、数据备份（演示版生成 SQL 文件）、操作日志
- **辅助能力**：表单校验、操作日志、文件上传、批量导入导出、响应式布局、REST API 数据接口

![img.png](img.png)

![img_1.png](img_1.png)

![img_2.png](img_2.png)

![img_3.png](img_3.png)



## 目录结构
```
.
├── app
│   ├── __init__.py          # 应用工厂，注册蓝图
│   ├── extensions.py        # SQLAlchemy / LoginManager 实例
│   ├── models.py            # 所有数据模型与初始化逻辑
│   ├── utils.py             # 通用工具（权限校验、Excel 导入导出、日志等）
│   ├── api.py               # REST API（学生/课程/成绩/考勤等）
│   ├── views                # 模块化蓝图（auth/dashboard/students/...）
│   ├── static
│   │   ├── css/style.css
│   │   └── uploads/         # 运行期上传文件（头像/导入文件）
│   └── templates            # Jinja2 模板，按模块划分
├── config.py                # 配置（数据库、上传、Cookie 等）
├── db
│   └── schema.sql           # MySQL 初始化脚本（可选执行）
├── requirements.txt         # Python 依赖
└── run.py                   # 入口脚本
```

## 快速开始
### 1. 环境依赖
- Python 3.10+
- MySQL 8.x（或兼容版本）

### 2. 创建数据库
```bash
mysql -u root -p < db/schema.sql
# schema.sql 会创建全部业务表并导入示例数据（角色、用户、课程、成绩等）
```
> 默认 `config.py` 中连接串：`mysql+pymysql://root:root123456@localhost:3306/school_db`
> 可通过环境变量 `DATABASE_URL` 覆盖（例如部署到云数据库）。

### 3. 安装依赖 & 运行
```bash
python -m venv .venv
source .venv/bin/activate        # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt

# 首次运行会自动创建基础表、内置角色与管理员账号
python run.py
# 浏览器访问 http://127.0.0.1:5000/
```

### 4. 默认账号
- 管理员：`admin / Admin@123`
- 首次登录会强制要求修改密码

## 主要模块说明
| 模块 | 关键页面 | 功能点 |
| ---- | ---- | ---- |
| 登录/认证 | 登录、注册、忘记密码、首次改密 | 支持多角色选择、记住登录、令牌式重置密码 |
| 仪表盘 | `/` | 数据统计、快捷入口、公告、个人待办新增、未读消息、成绩/考勤可视化 |
| 学生管理 | `/students/` | 搜索筛选分页、详情、增改删、头像上传、Excel 导入导出 |
| 班级管理 | `/classes/` | 班级档案、班主任配置、学生分班（多选） |
| 教师管理 | `/teachers/` | 教师档案、任教班级查询 |
| 课程管理 | `/courses/` | 课程档案、课表维护、选课学生分配 |
| 成绩管理 | `/grades/entry` 等 | 班级/课程成绩录入、查询、进度可视化、导出 |
| 考勤管理 | `/attendance/check` 等 | 按班级/课程签到、考勤统计、学生请假、审批流 |
| 通知公告 | `/announcements/` | 列表、详情、置顶、按角色推送、发布 |
| 个人中心 | `/profile/*` | 资料维护、头像上传、密码修改、消息中心 |
| 系统设置 | `/settings/*` | 用户角色分配、参数配置、数据备份（示例）、操作日志 |

## REST API 摘要
所有接口均需登录后访问，响应 JSON。

| 方法 | 路径 | 描述 |
| ---- | ---- | ---- |
| GET | `/api/dashboard/summary` | 仪表盘统计数据 |
| GET/POST/PUT/DELETE | `/api/students(/<id>)` | 学生列表、创建、更新、删除 |
| GET | `/api/classes` | 班级列表及人数 |
| GET | `/api/courses` | 课程列表 |
| GET | `/api/grades` | 成绩数据（学生/课程/成绩/学期） |
| GET | `/api/attendance` | 最近考勤记录 |
| GET | `/api/announcements` | 公告列表 |
| POST | `/api/todos` | 新增个人待办 |

> 需要更细粒度接口时，可在 `app/api.py` 中扩展。

## Excel 导入导出
- **学生导入**：模板包含 `student_number,name,gender,date_of_birth,class_name,email,phone,address`
- **学生导出**：`/students/export` 直接生成 `students.xlsx`
- **成绩导出**：`/grades/export` 生成成绩报表
- 使用 `openpyxl` 读写，支持 UTF-8 中文内容

## 权限与日志
- 角色/权限初始化逻辑位于 `models.create_default_roles()`，可按需扩展 `default_permissions()`
- 关键操作统一通过 `utils.log_operation()` 写入 `operation_logs` 表，便于审计
- 需要新增权限时：
  1. 在 `default_permissions()` 增加定义
  2. 为角色配置对应权限
  3. 在视图或模板中使用 `permission_required`/`current_user.has_permission`

## 配置说明
`config.Config` 中可调参数：
- `SECRET_KEY`：会话密钥
- `DATABASE_URL`：MySQL 连接串
- `UPLOAD_FOLDER`：上传文件持久目录（默认 `app/static/uploads`）
- `MAX_CONTENT_LENGTH`：上传大小限制（默认 16 MB）
- `REMEMBER_COOKIE_DURATION`：记住登录有效期（秒）

## 扩展建议
- 引入 `Flask-Migrate` 管理结构迁移
- 接入短信/邮件服务完成真实的密码重置通知
- 拆分前端，使用 Vue/React + REST API 形成前后端分离模式
- 增加更多图表（ECharts、AntV 等）与 BI 分析
- 接入 Redis 做缓存及异步任务（批量导入、报表生成）
- 结合 Celery/APS 实现通知推送、定时备份
