# 飞书英雄数据分析 - Python 作业

从飞书多维表格读取英雄技能数据，统计分析后写回结果表，支持定时自动执行。

## 功能

- 从飞书多维表格读取英雄数据（821 条记录）
- 统计总英雄数、职业分布、技能类型分布
- 将分析结果写回汇总结果表（有则更新，无则新增）
- APScheduler 每 2 分钟自动执行一次
- 日志同时输出到屏幕和 `task.log` 文件

## 项目结构

```
python hw4/
├── project2/               # 主程序（作业 B）
│   ├── main.py             # 主流程 + 定时调度
│   ├── config.py           # 配置区（从 .env 读取敏感信息）
│   ├── feishu_api.py       # 飞书 API 封装
│   ├── requirements.txt    # 依赖列表
│   ├── Dockerfile          # 容器构建文件
│   ├── docker-compose.yml  # 容器编排文件
│   └── .env                # 敏感配置（不提交，本地维护）
└── project/                # 作业 A（只读取分析，不写回）
```

## 快速开始

### 本地运行

```bash
# 1. 安装依赖
pip install -r project2/requirements.txt

# 2. 配置 .env（复制模板后填入真实值）
cp project2/.env.example project2/.env

# 3. 运行
cd project2
python main.py
```

### Docker 运行

```bash
cd project2

# 确保 .env 文件已配置
docker-compose up --build -d

# 查看日志
docker logs -f hero-sync
```

## 环境变量（.env）

| 变量名 | 说明 |
|--------|------|
| `FEISHU_APP_ID` | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret |
| `FEISHU_SOURCE_WIKI_NODE_TOKEN` | 来源表 Wiki 节点 Token |
| `FEISHU_SOURCE_TABLE_ID` | 来源表 Table ID |
| `FEISHU_RESULT_WIKI_NODE_TOKEN` | 结果表 Wiki 节点 Token |
| `FEISHU_RESULT_TABLE_ID` | 结果表 Table ID |
| `STUDENT_NAME` | 学生姓名（防重复提交） |

> `.env` 文件包含敏感信息，已加入 `.gitignore`，不提交到 git。

## 部署说明

本地修改代码后，用 `git push` 推送到 GitHub（`.env` 不上传）。服务器执行 `git pull` 拉取最新代码，再运行 `docker-compose up --build -d` 重新构建并启动容器。容器通过 `env_file: .env` 读取敏感配置，`.env` 由运维人员手动放置在服务器上。日志通过 volumes 挂载到宿主机 `task.log`，容器重启后不丢失。
