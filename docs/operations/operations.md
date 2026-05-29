# 操作指南

## 项目初始化

### 1. 创建新项目

```bash
python webnovel_cli.py init --name "我的都市异能小说" --genre "都市异能" --character "张三"
```

这将创建以下目录结构：

```
my-novel/
├── .story-system/      # Story System 数据
│   ├── MASTER_SETTING.json
│   ├── volumes/        # 卷合同
│   ├── chapters/       # 章节合同
│   ├── commits/        # 提交记录
│   ├── reviews/        # 审查记录
│   └── events/         # 事件审计
├── .webnovel/          # 网文数据
│   ├── state.json
│   ├── memory_scratchpad.json
│   ├── index.db
│   └── backups/        # 备份
├── 设定集/             # 设定文档
├── 大纲/               # 大纲文档
└── 章节/               # 章节内容
```

### 2. 配置 RAG

创建 `.env` 文件：

```env
EMBED_API_KEY=your_modelscope_api_key
RERANK_API_KEY=your_jina_api_key
JINA_PROXY=http://127.0.0.1:10809
```

## 写作流程

### 标准流程

1. **规划卷** - `plan` 命令
2. **写作章节** - `write` 命令
3. **审查章节** - `review` 命令
4. **提交章节** - `commit` 命令

### 示例：写第一章

```bash
# 1. 规划第1卷
python webnovel_cli.py plan 1

# 2. 获取创作任务书
python webnovel_cli.py task 1

# 3. 写作（手动编写章节内容）

# 4. 审查章节
python webnovel_cli.py review 1

# 5. 提交章节
python webnovel_cli.py commit 1

# 6. 事件提取
python webnovel_cli.py events
```

## 长期记忆管理

### 查看记忆

```bash
# 查看记忆摘要
python webnovel_cli.py memory

# 查看详细
python webnovel_cli.py memory characters
python webnovel_cli.py memory events
python webnovel_cli.py memory hooks
```

### 更新记忆

```bash
# 添加角色
python webnovel_cli.py memory add-char "张三" "主角，拥有火系异能"

# 添加事件
python webnovel_cli.py memory add-event "获得异能" "第1章，张三被闪电击中获得异能"

# 添加钩子
python webnovel_cli.py memory add-hook "神秘声音" "第1章结尾，神秘声音提出交易"
```

## 备份管理

### 创建备份

```bash
# 创建带描述的备份
python webnovel_cli.py backup create -d "完成第10章"

# 创建自动命名的备份
python webnovel_cli.py backup create
```

### 恢复备份

```bash
# 列出可用备份
python webnovel_cli.py backup list

# 恢复备份
python webnovel_cli.py backup restore backup backup_20240101_120000
```

### 归档管理

```bash
# 归档旧备份
python webnovel_cli.py backup archive

# 列出归档
python webnovel_cli.py backup list archive

# 从归档恢复
python webnovel_cli.py backup restore archive archive_20240101
```

## Dashboard 使用

### 启动 Dashboard

```bash
python webnovel_cli.py dashboard --port 5000
```

### 访问

打开浏览器访问：http://127.0.0.1:5000

### 功能

- **项目概览** - 章节数、角色数、事件数统计
- **状态面板** - Story System 健康状态
- **追读力分析** - 钩子和爽点统计
- **提交历史** - 最近的提交记录
- **合同树概览** - 卷、章节、事件统计

## 数据导出/导入

### 导出

```bash
# 导出所有数据
python webnovel_cli.py export --type all -o backup.json

# 仅导出章节
python webnovel_cli.py export --type chapter -o chapters.json

# 仅导出设定
python webnovel_cli.py export --type setting -o settings.json
```

### 导入

```bash
python webnovel_cli.py import backup.json --type all
```

## 健康检查

### 运行检查

```bash
# 文本格式
python webnovel_cli.py preflight

# JSON 格式
python webnovel_cli.py preflight --format json
```

### 检查内容

- Phase 1: 合同种子（主设定文件）
- Phase 2: 运行时合同（卷合同）
- Phase 3: 章节提交链（提交记录）
- Phase 4: 事件审计链（事件记录）
- Phase 5: 真源管理（状态一致性）

## 参考作品学习

### 学习写作风格

```bash
python webnovel_cli.py learn -s reference.txt --type style -o style_report.md
```

### 拆解参考作品

```bash
# 拆解整个文件
python webnovel_cli.py deconstruct reference.txt

# 拆解特定章节
python webnovel_cli.py deconstruct reference.txt -c 5

# 输出为 JSON
python webnovel_cli.py deconstruct reference.txt -f json -o analysis.json
```
