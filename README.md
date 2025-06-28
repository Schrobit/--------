# EI Power反馈管理系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于Flask的团队反馈收集和管理系统，专为10人小组设计，支持每日反馈提交、自动邮件提醒和管理员处理功能。

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [预置账户](#预置账户)
- [使用说明](#使用说明)
- [项目结构](#项目结构)
- [数据库设计](#数据库设计)
- [API文档](#api文档)

## ✨ 功能特性

### 🔧 核心功能
- **👥 用户管理**：预置10个固定成员账户，支持管理员和普通用户角色
- **📝 反馈提交**：每人每天必须提交3个问题反馈，带有强制数量校验
- **📧 邮件提醒**：每日16:00自动检查并提醒未完成提交的成员
- **🔐 权限控制**：普通用户只能查看/编辑自己的反馈，管理员可处理所有反馈
- **📊 数据统计**：实时显示团队提交状态和处理进度
- **🔍 搜索功能**：支持反馈内容搜索和状态筛选

### 🎨 用户界面
- **🔑 登录页面**：简洁美观的用户认证界面
- **📈 用户仪表盘**：显示当日提交状态和最近反馈记录
- **📋 反馈表单**：支持单个提交，带有实时字符计数和提交指南
- **📚 历史记录**：个人反馈历史查看，支持搜索和详情查看
- **⚙️ 管理员面板**：全局用户状态监控和反馈处理台
- **📱 响应式设计**：支持桌面端和移动端访问

## 🛠️ 技术栈

### 后端技术
- **🐍 Python 3.8+**：主要开发语言
- **🌶️ Flask 2.3.3**：轻量级Web框架
- **🔐 Flask-Login**：用户会话管理
- **🛡️ Werkzeug**：密码哈希和安全工具
- **⏰ APScheduler**：定时任务调度

### 数据存储
- **🗄️ SQLite**：轻量级关系型数据库
- **📊 数据库设计**：用户表、反馈表、日志表

### 前端技术
- **🎨 Bootstrap 5**：响应式UI框架
- **⚡ JavaScript**：交互功能实现
- **🎭 Jinja2**：模板引擎
- **🎯 Bootstrap Icons**：图标库

### 通信服务
- **📧 SMTP**：邮件发送服务
- **📮 企业邮箱**：支持QQ邮箱、企业邮箱等

### 开发工具
- **🔧 Flask-WTF**：表单处理和CSRF保护
- **✅ Email-validator**：邮箱格式验证

## 🚀 快速开始

### 📋 系统要求

- **Python**: 3.8+
- **操作系统**: Windows / macOS / Linux

### 1️⃣ 安装依赖

```bash
# 进入项目目录
cd 团队反馈管理系统

# 安装依赖
pip install -r requirements.txt
```

### 2️⃣ 初始化数据库

```bash
# 初始化数据库和预置用户
python database.py
```

### 3️⃣ 配置邮件（可选）

编辑 `email_service.py` 文件：

```python
# 邮件配置
SMTP_SERVER = 'smtp.exmail.qq.com'
SMTP_PORT = 465
SENDER_EMAIL = 'your_email@domain.com'
SENDER_PASSWORD = 'your_app_password'
```

### 4️⃣ 启动应用

```bash
# 启动系统
python app.py
```

访问 `http://localhost:5001` 开始使用！

## 👥 预置账户

系统预置了10个用户账户，用户名为邮箱格式，统一密码为 `@ei-power.tech`：

### 🔑 管理员账户
| 姓名 | 用户名(邮箱) | 角色 | 密码 | 权限 |
|------|--------------|------|------|------|
| 童佳豪 | tongjiahao@ei-power.tech | 管理员 | @ei-power.tech | 全部功能 |

### 👤 普通用户账户
| 姓名 | 用户名(邮箱) | 角色 | 密码 | 权限 |
|------|--------------|------|------|------|
| 吴俊豪 | misa@ei-power.tech | 普通用户 | @ei-power.tech | 提交反馈 |
| 曹彩月 | yuanshanzhang@ei-power.tech | 普通用户 | @ei-power.tech | 提交反馈 |
| 叶邱静怡 | noname@ei-power.tech | 普通用户 | @ei-power.tech | 提交反馈 |
| 陈佳欣 | iiio@ei-power.tech | 普通用户 | @ei-power.tech | 提交反馈 |
| 张彤 | wuyigexiaolingcheng@ei-power.tech | 普通用户 | @ei-power.tech | 提交反馈 |
| 王星月 | xiaoyuaishuijiao@ei-power.tech | 普通用户 | @ei-power.tech | 提交反馈 |
| 倪杨钊 | chuaner@ei-power.tech | 普通用户 | @ei-power.tech | 提交反馈 |
| 徐茹雯 | sandishousibushousi@ei-power.tech | 普通用户 | @ei-power.tech | 提交反馈 |
| 姜赐雪 | xiaoxue@ei-power.tech | 普通用户 | @ei-power.tech | 提交反馈 |

### 🔒 安全提醒

> ⚠️ **重要**：生产环境部署时请修改默认密码！
> 
> 🛡️ **建议**：
> - 使用强密码（至少8位，包含字母、数字、特殊字符）
> - 定期更换密码
> - 为每个用户设置不同的密码

## 📖 使用说明

### 👤 普通用户操作

#### 1️⃣ 登录系统
- 🔐 使用预置账户或管理员分配的账户登录
- 📊 登录后可查看个人信息和今日提交状态
- 🏠 主页显示个人统计信息

#### 2️⃣ 提交反馈
- ✍️ 点击"提交反馈"按钮
- 📝 填写反馈内容（必填，不能为空）
- 🔢 系统自动生成唯一反馈编号
- ⏰ 每日限制提交1次（防止重复提交）
- ✅ 提交成功后显示确认信息

#### 3️⃣ 查看历史
- 📚 在"历史记录"页面查看个人提交的所有反馈
- 🏷️ 查看反馈状态：
  - 🟡 **待处理**：刚提交，等待管理员处理
  - 🟢 **已处理**：管理员已查看并处理
- 📅 按时间倒序显示，最新的在前

### 👨‍💼 管理员操作

#### 1️⃣ 管理员面板
- 📈 查看所有用户今日提交状态
- 📋 查看待处理的反馈列表
- 📊 统计数据一目了然：
  - 今日提交总数
  - 待处理反馈数量
  - 用户提交状态概览

#### 2️⃣ 处理反馈
- 👀 在管理员面板中查看待处理反馈详情
- ✅ 点击"标记为已处理"更新反馈状态
- ⏰ 系统自动记录处理时间
- 📝 可查看反馈的完整内容和提交时间

### 反馈字段说明

每个反馈包含以下字段：

- **编号**：自动生成，格式为 `日期-用户名-序号`（如：20250628-tjh-2）
- **提议时间**：提交时的时间戳
- **提议人**：当前登录用户
- **提案内容**：用户提交的反馈内容
- **状态**：新提案/处理中/已解决
- **修正提案**：管理员提供的修正建议
- **处理意见**：管理员的处理说明
- **处理人**：处理该反馈的管理员

## 邮件提醒机制

系统每日16:00自动执行以下操作：

1. 检查所有用户的当日提交状态
2. 识别未完成3个反馈的用户
3. 发送提醒邮件，格式如下：

```
主题：[行动要求] 今日反馈未提交

亲爱的 {姓名}，

您好！

系统检测到您今日还需要提交 {数量} 个问题反馈。

请及时登录系统完成提交：
{系统访问地址}

提交截止时间：今日24:00

如有疑问，请联系管理员。

此邮件为系统自动发送，请勿回复。

团队反馈管理系统
```

## 📁 项目结构

```
团队反馈管理系统/
├── 📄 app.py                    # Flask主应用程序
├── 🗄️ database.py               # 数据库操作和初始化
├── 📧 email_service.py          # 邮件发送服务
├── 📋 requirements.txt          # Python依赖包列表
├── 📖 README.md                # 项目文档说明
├── 📁 templates/               # Jinja2 HTML模板目录
│   ├── 🏗️ base.html            # 基础布局模板
│   ├── 🔐 login.html           # 用户登录页面
│   ├── 📊 dashboard.html       # 用户仪表盘
│   ├── ✍️ submit_feedback.html # 反馈提交页面
│   ├── 📚 history.html         # 历史记录页面
│   └── 👨‍💼 admin.html           # 管理员控制面板
├── 📁 static/                  # 静态资源目录
│   ├── 🎨 css/                # CSS样式文件
│   │   └── style.css          # 主样式表
│   └── ⚡ js/                 # JavaScript脚本
│       └── main.js            # 主脚本文件
└── 🗃️ feedback_system.db       # SQLite数据库文件（运行后自动生成）
```

### 📂 目录说明

- **📄 核心文件**：包含应用主逻辑、数据库操作和邮件服务
- **📁 templates/**：存放所有HTML模板，使用Jinja2模板引擎
- **📁 static/**：存放CSS、JavaScript等静态资源
- **🗃️ feedback_system.db**：SQLite数据库文件，首次运行时自动创建

## 🗄️ 数据库设计

### 📊 数据库概览

系统使用 **SQLite** 轻量级数据库，包含3个核心表：
- 👥 **users**: 用户信息管理
- 📝 **feedback**: 反馈内容存储
- 📧 **reminder_logs**: 邮件发送记录

### 📋 表结构详情

#### 👥 users 表（用户信息）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 用户唯一标识 |
| username | TEXT | UNIQUE, NOT NULL | 用户名（邮箱格式） |
| password_hash | TEXT | NOT NULL | 密码哈希值（Werkzeug加密） |
| name | TEXT | NOT NULL | 用户真实姓名 |
| is_admin | INTEGER | DEFAULT 0 | 管理员权限（0=普通用户，1=管理员） |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 账户创建时间 |

#### 📝 feedback 表（反馈记录）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 反馈唯一标识 |
| user_id | INTEGER | FOREIGN KEY | 关联用户ID |
| feedback_number | TEXT | UNIQUE, NOT NULL | 反馈编号（格式：FB-YYYYMMDD-XXXX） |
| content | TEXT | NOT NULL | 反馈具体内容 |
| status | TEXT | DEFAULT '待处理' | 处理状态（待处理/已处理） |
| submitted_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 反馈提交时间 |
| processed_at | TIMESTAMP | NULL | 管理员处理时间 |

#### 📧 reminder_logs 表（邮件记录）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 记录唯一标识 |
| user_id | INTEGER | FOREIGN KEY | 关联用户ID |
| sent_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 邮件发送时间 |
| email_status | TEXT | NOT NULL | 发送状态（成功/失败） |

### 🔗 表关系说明

```
users (1) ←→ (N) feedback
  ↓
  └── (1) ←→ (N) reminder_logs
```

- 一个用户可以提交多条反馈
- 一个用户可以有多条邮件发送记录
- 通过 `user_id` 外键建立关联关系

## 开发说明

### 自定义配置

1. **修改邮件模板**：编辑 `email_service.py` 中的邮件内容
2. **调整提醒时间**：修改 `app.py` 中的定时任务时间
3. **更改用户列表**：编辑 `database.py` 中的 `users_data`
4. **自定义样式**：在 `static/css/` 目录添加CSS文件

### 扩展功能

- 添加文件上传功能
- 集成更多通知方式（短信、微信等）
- 增加数据统计和报表功能
- 支持反馈分类和标签
- 添加评论和讨论功能

## 🔌 API文档

### 🌐 RESTful API 接口

#### 用户认证

```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password123
```

#### 反馈管理

```http
# 提交反馈
POST /submit_feedback
Content-Type: application/x-www-form-urlencoded

content=这是我的反馈内容

# 获取今日状态
GET /api/today_status
Response: {"submitted": true, "feedback_count": 1}

# 更新反馈状态（管理员）
POST /update_feedback
Content-Type: application/x-www-form-urlencoded

feedback_id=123&status=已处理
```

#### 页面路由

| 路由 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/` | GET | 用户仪表盘 | 登录用户 |
| `/login` | GET/POST | 登录页面 | 公开 |
| `/logout` | GET | 退出登录 | 登录用户 |
| `/submit_feedback` | GET/POST | 提交反馈 | 登录用户 |
| `/history` | GET | 历史记录 | 登录用户 |
| `/admin` | GET | 管理员面板 | 管理员 |
| `/api/today_status` | GET | 今日状态API | 登录用户 |

---

**© 2024 EI-Power Technology. 简单高效的团队反馈管理系统**