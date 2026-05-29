# CLI 命令参考

## 快速开始

```bash
# 进入项目目录
cd your-novel-project

# 初始化新项目
python webnovel_cli.py init --name "我的小说" --genre "都市异能" --character "张三"

# 查看项目状态
python webnovel_cli.py status

# 健康检查
python webnovel_cli.py preflight
```

## 命令列表

### 项目管理

| 命令 | 说明 |
|------|------|
| `init` | 初始化新项目 |
| `status` | 查看项目状态 |
| `preflight` | Story System 健康检查 |

### 写作流程

| 命令 | 说明 |
|------|------|
| `plan <volume>` | 规划卷级大纲 |
| `write <chapter>` | 写作章节 |
| `review <chapter>` | 审查章节 |
| `commit <chapter>` | 提交章节（Phase 3） |
| `events` | 事件审计（Phase 4） |
| `task <chapter>` | 获取创作任务书 |

### 数据管理

| 命令 | 说明 |
|------|------|
| `backup` | 备份管理 |
| `db` | 数据库管理 |
| `export` | 导出数据 |
| `import` | 导入数据 |

### 学习参考

| 命令 | 说明 |
|------|------|
| `learn` | 学习参考作品 |
| `deconstruct` | 拆解参考作品 |

### 系统工具

| 命令 | 说明 |
|------|------|
| `dashboard` | 启动可视化面板 |
| `query` | 查询信息 |
| `reader-pull` | 追读力分析 |
| `memory` | 长期记忆管理 |

## 详细命令

### init - 初始化项目

```bash
python webnovel_cli.py init --name "小说名" --genre "都市异能" --character "主角名"
```

参数：
- `--name, -n`: 项目名称
- `--genre, -g`: 题材类型
- `--character, -c`: 主角名字
- `--finger, -f`: 金手指类型（可选）

### status - 项目状态

```bash
python webnovel_cli.py status
```

显示：
- 目录结构
- 章节统计
- 备份状态
- 记忆状态
- RAG 索引状态

### preflight - 健康检查

```bash
python webnovel_cli.py preflight [--format json]
```

检查 Phase 1-5 的数据一致性。

### plan - 规划大纲

```bash
python webnovel_cli.py plan 1           # 规划第1卷
python webnovel_cli.py plan 1 -e 3     # 规划第1-3卷
```

### write - 写作章节

```bash
python webnovel_cli.py write 1         # 写第1章
```

### review - 审查章节

```bash
python webnovel_cli.py review 1         # 审查第1章
```

六维审查：
1. High-point Checker - 爽点密度
2. Consistency Checker - 设定一致性
3. Pacing Checker - 节奏检查
4. OOC Checker - 人物行为
5. Continuity Checker - 连贯性
6. Reader-pull Checker - 追读力

### commit - 提交章节

```bash
python webnovel_cli.py commit 1         # 提交第1章
```

### backup - 备份管理

```bash
# 创建备份
python webnovel_cli.py backup create -d "章节完成"

# 列出备份
python webnovel_cli.py backup list

# 恢复备份
python webnovel_cli.py backup restore backup backup_20240101

# 查看统计
python webnovel_cli.py backup stats

# 归档旧备份
python webnovel_cli.py backup archive
```

### dashboard - 可视化面板

```bash
python webnovel_cli.py dashboard [--port 5000]
```

访问 http://127.0.0.1:5000 查看 Dashboard。

### export/import - 数据导入导出

```bash
# 导出所有数据
python webnovel_cli.py export --type all -o export.json

# 导出章节
python webnovel_cli.py export --type chapter -o chapters.json

# 导入数据
python webnovel_cli.py import data.json --type all
```

### learn - 学习参考

```bash
python webnovel_cli.py learn -s reference.txt --type all
```

学习类型：
- `style` - 写作风格
- `plot` - 情节结构
- `setting` - 设定元素
- `all` - 全部

### deconstruct - 拆解参考

```bash
python webnovel_cli.py deconstruct reference.txt -c 1
```

## 环境变量

在 `.env` 文件中配置：

```env
# RAG 配置
EMBED_API_KEY=your_api_key
EMBED_MODEL=Qwen/Qwen3-Embedding-8B
RERANK_API_KEY=your_rerank_key
JINA_PROXY=http://127.0.0.1:10809
```
