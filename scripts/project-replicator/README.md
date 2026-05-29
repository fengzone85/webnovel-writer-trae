# Project Replicator - 项目复制系统

全面的项目复制工具，支持完整复制项目的源代码、配置文件、依赖、数据库和部署设置。

## 功能特性

### 核心功能
- **文件系统复制**：完整复制目录结构，支持过滤规则和符号链接处理
- **配置同步**：同步 package.json、requirements.txt、.env 等配置文件
- **依赖管理**：自动检测并安装 npm、pip、Poetry 依赖
- **数据库复制**：支持 SQLite、JSON 数据文件和数据目录复制
- **版本控制集成**：自动初始化 Git 仓库，创建提交历史和标签
- **验证检查**：多维度验证复制结果的完整性和正确性

### 验证检查项
| 检查项 | 描述 |
|--------|------|
| 文件结构 | 验证必要目录是否存在 |
| 配置文件 | 检查配置文件完整性 |
| 依赖可用性 | 检查 npm、pip、git 等工具 |
| 校验和验证 | 验证文件内容一致性 |
| 构建测试 | 执行 npm run build |
| 安全扫描 | 检查敏感文件 |
| 性能检查 | 检查构建产物大小 |

## 安装

```bash
# 克隆项目
git clone <repository-url>

# 进入目录
cd project-replicator

# 安装依赖（可选）
pip install -r requirements.txt
```

## 快速开始

### 基础用法

```bash
# 基本复制
python replicator.py /path/to/source /path/to/target

# 覆盖已存在的目标目录
python replicator.py /path/to/source /path/to/target --overwrite

# 跳过数据库复制
python replicator.py /path/to/source /path/to/target --skip-db

# 跳过版本控制设置
python replicator.py /path/to/source /path/to/target --skip-vc

# 使用配置文件
python replicator.py /path/to/source /path/to/target --config config.json
```

### 使用 Python API

```python
from replicator import ProjectReplicator

# 配置
config = {
    'source_path': '/path/to/source',
    'target_path': '/path/to/target',
    'overwrite_existing': True,
    'include_database': True,
    'version_control': True
}

# 创建复制器
replicator = ProjectReplicator(config)

# 执行复制
result = replicator.replicate()

# 检查结果
if result['status'] == 'completed':
    print("复制成功！")
else:
    print(f"复制失败: {result.get('errors', [])}")
```

## 配置文件

```json
{
  "source_path": "/path/to/source/project",
  "target_path": "/path/to/target/project",
  "replication_id": "",
  "history_path": ".replication-history",
  
  "overwrite_existing": false,
  "include_database": true,
  "version_control": true,
  "verbose": true,
  
  "exclude_patterns": [
    "*.log",
    "node_modules/",
    "venv/"
  ],
  
  "include_patterns": []
}
```

### 配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| source_path | string | - | 源项目路径 |
| target_path | string | - | 目标路径 |
| overwrite_existing | bool | false | 是否覆盖已存在的目标目录 |
| include_database | bool | true | 是否复制数据库 |
| version_control | bool | true | 是否设置版本控制 |
| verbose | bool | false | 是否详细输出 |
| exclude_patterns | array | [] | 排除的文件/目录模式 |
| include_patterns | array | [] | 包含的文件/目录模式（优先） |

## 目录结构

```
project-replicator/
├── replicator.py          # 主入口
├── file_replicator.py     # 文件复制模块
├── config_synchronizer.py # 配置同步模块
├── dependency_manager.py  # 依赖管理模块
├── database_replicator.py # 数据库复制模块
├── validation_checker.py  # 验证检查模块
├── version_control.py     # 版本控制模块
├── utils.py               # 工具函数
├── config.example.json    # 示例配置
└── README.md              # 使用说明
```

## 复制流程

```
1. 验证源项目
   └→ 检查源路径是否存在

2. 准备目标目录
   └→ 创建/清理目标目录

3. 复制文件系统
   └→ 递归复制，应用过滤规则

4. 同步配置文件
   └→ 合并 package.json、.env 等

5. 安装依赖
   └→ npm install / pip install

6. 复制数据库
   └→ SQLite / JSON / 数据目录

7. 验证复制结果
   └→ 多维度检查

8. 设置版本控制
   └→ Git init / commit / tag

9. 保存复制历史
   └→ 记录到 .replication-history
```

## 复制历史

每次复制完成后，系统会自动保存复制历史：

```
.replication-history/
├── index.json                    # 复制记录索引
├── repl_20240101120000_abc123.json  # 详细复制记录
└── repl_20240102140000_def456.json  # 详细复制记录
```

## 支持的技术栈

### 语言/框架
- Python 3.8+
- Node.js / npm / yarn
- Poetry

### 数据库
- SQLite（.db 文件）
- JSON 数据文件
- 数据目录

### 版本控制
- Git

## 输出示例

```
============================================================
开始项目复制 - ID: repl_20240101120000_abc123
源路径: /home/user/projects/my-project
目标路径: /home/user/projects/my-project-copy
============================================================
验证源项目...
准备目标目录...
开始文件系统复制...
开始配置文件同步...
开始依赖管理...
安装 npm 依赖...
npm 依赖安装成功，共 25 个包
开始数据库复制...
开始验证检查...
  文件结构完整性: 通过
  配置文件存在性: 通过
  依赖可用性: 通过
  文件校验和验证: 通过
开始版本控制...
============================================================
复制结果: COMPLETED
复制ID: repl_20240101120000_abc123
源路径: /home/user/projects/my-project
目标路径: /home/user/projects/my-project-copy

✅ 验证结果: completed
  ✓ 文件结构完整性: 文件结构完整
  ✓ 配置文件存在性: 所有配置文件齐全
  ✓ 依赖可用性: 所有依赖已安装
  ✓ 文件校验和验证: 校验和验证通过
============================================================
```

## 许可证

MIT License