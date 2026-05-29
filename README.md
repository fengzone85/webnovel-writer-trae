# Webnovel Writer - Trae Skill

长篇网文创作系统，基于 Story System 合同驱动架构。

## 功能特性

- 📖 **Story System** - 合同驱动创作流程
- 🤖 **Agent 系统** - Context Agent、Data Agent、Reviewer Agent、Deconstruction Agent
- 🔍 **RAG 向量检索** - ModelScope Embedding + Jina AI Rerank
- 🧠 **长期记忆** - 角色、事件、钩子管理
- ✅ **六维审查** - 爽点、一致性、节奏、OOC、连贯性、追读力
- 📊 **Dashboard** - 可视化项目管理
- 💾 **备份管理** - 自动备份与恢复
- 🔄 **文档同步系统** - 自动定时同步、版本跟踪、兼容性测试
- 📤 **项目复制器** - 一键复制项目结构
- 📱 **多端支持** - 支持微信小程序等跨端部署

## 快速开始

### 1. 安装依赖

```bash
pip install -r scripts/requirements.txt
pip install flask flask-cors
```

### 2. 初始化项目

```bash
python scripts/webnovel_cli.py init --name "我的小说" --genre "都市异能" --character "张三"
```

### 3. 开始写作

```bash
# 规划卷
python scripts/webnovel_cli.py plan 1

# 获取任务书
python scripts/webnovel_cli.py task 1

# 写作（手动编辑章节）

# 审查
python scripts/webnovel_cli.py review 1

# 提交
python scripts/webnovel_cli.py commit 1
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `init` | 初始化项目 |
| `status` | 项目状态 |
| `preflight` | 健康检查 |
| `plan` | 规划大纲 |
| `write` | 写作章节 |
| `review` | 审查章节 |
| `commit` | 提交章节 |
| `backup` | 备份管理 |
| `dashboard` | 可视化面板 |
| `memory` | 记忆管理 |
| `learn` | 学习参考 |
| `deconstruct` | 拆解参考 |
| `sync` | 文档同步 |

完整命令参考：[docs/guides/commands.md](docs/guides/commands.md)

## 项目结构

```
.
├── scripts/
│   ├── webnovel_cli.py      # 主 CLI
│   ├── story_system.py      # Story System
│   ├── backup_manager.py    # 备份管理
│   ├── agents/              # Agent 系统
│   │   ├── context_agent.py
│   │   ├── data_agent.py
│   │   ├── reviewer_agent.py
│   │   └── deconstruction_agent.py
│   ├── rag/                 # RAG 模块
│   │   ├── vector_store.py
│   │   └── chromadb_backend.py
│   ├── data_modules/        # 数据模块
│   │   ├── genre_loader.py
│   │   └── memory_index.py
│   ├── dashboard/           # Dashboard
│   │   └── server.py
│   ├── sync_system/         # 文档同步系统
│   │   ├── sync_scheduler.py
│   │   ├── compatibility_tester.py
│   │   ├── notification.py
│   │   └── config/
│   └── project-replicator/  # 项目复制器
│       └── replicator.py
├── references/
│   └── genres/              # 题材模板（37种）
├── tests/                   # 测试
└── docs/                    # 文档
```

## 文档同步系统

自动同步原项目文档更新，确保版本对齐：

- **定时同步** - 支持每日/每周定时同步
- **增量同步** - 仅获取变更内容
- **版本跟踪** - 与原项目版本号精确匹配
- **兼容性测试** - 自动验证文档格式和链接有效性
- **依赖管理** - 分类标注必选/可选依赖
- **通知系统** - 支持 console/file/webhook/email 多渠道通知

配置文件：`scripts/sync_system/config/sync_config.ini`

```bash
# 手动执行同步
python scripts/sync_system/sync_system.py sync --force

# 查看同步状态
python scripts/sync_system/sync_system.py status

# 配置 Windows 定时任务
powershell -ExecutionPolicy Bypass -File scripts/sync_system/config/windows_task_scheduler.ps1
```

## 文档

- [命令参考](docs/guides/commands.md)
- [操作指南](docs/operations/operations.md)
- [同步系统维护手册](scripts/sync_system/维护手册.md)
- [优先级行动计划](优先级行动计划.md)
- [功能差异分析报告](功能差异分析报告.md)

## 配置

在项目根目录创建 `.env` 文件：

```env
EMBED_API_KEY=your_modelscope_api_key
RERANK_API_KEY=your_jina_api_key
JINA_PROXY=http://127.0.0.1:10809
```

## 状态

当前完成度：**~95%**

### 已完成
- ✅ 核心写作流程
- ✅ Story System Phase 1-5
- ✅ Agent 系统
- ✅ RAG 向量检索
- ✅ 六维审查
- ✅ 追读力系统
- ✅ 备份管理
- ✅ Dashboard 可视化
- ✅ 项目复制器
- ✅ 文档同步系统
- ✅ CLI 工具集
- ✅ 测试覆盖
- ✅ ChromaDB 支持（可选）

### 开发中
- 🟡 文档完善
- 🟡 多端适配

## License

MIT License

## Contributing

欢迎提交 Issue 和 PR！