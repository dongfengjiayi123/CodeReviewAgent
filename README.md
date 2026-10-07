# CodeReviewAgent · 智能代码审查助手

基于 HelloAgents 的 Python 代码审查项目。提供本地 AST 分析、基础风格检查和兼容 OpenAI 协议的 AI 审查，输出 Markdown 报告。

本项目改编自 [jjyaoao 的 CodeReviewAgent](https://github.com/datawhalechina/Hello-Agents/tree/main/Co-creation-projects/jjyaoao-CodeReviewAgent)，修改范围与来源见 [NOTICE.md](NOTICE.md)。

## 功能

- 结构分析：统计类、同步和异步函数、代码行数。
- 基础风格检查：检查超过 79 字符的行、缩进制表符和行尾空白。
- AI 审查：使用 HelloAgents SimpleAgent 和两个自定义工具，分析潜在 bug、性能与改进建议。
- 离线运行：`--static-only` 无需密钥，不发送代码。
- 报告保护：拒绝覆盖源文件，完整报告通过临时文件替换，失败保留旧报告。
- GitHub Actions：在 Windows/Linux、Python 3.12/3.13 上执行离线测试。

基础风格检查未覆盖全部 PEP 8 规则。AI 建议需要开发者复核。当前支持单个 UTF-8 Python 文件，大小不超过 100 KB；不执行待审查代码。

## 快速开始

需要 **Python 3.12 或 3.13**（与固定的 HelloAgents 1.0.1 版本一致）。先进入包含 `review.py` 的项目目录。

### Git Bash（Windows）

```bash
python -m venv .venv
./.venv/Scripts/python.exe -m ensurepip --upgrade
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe review.py --static-only
```

### PowerShell（Windows）

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m ensurepip --upgrade
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe review.py --static-only
```

### Linux / macOS

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python review.py --static-only
```

以上命令默认审查 `data/sample_code.py`，生成 `outputs/review_report.md`。本地静态报告示例见 [examples/static_report.md](examples/static_report.md)。

## 配置 AI 审查

Git Bash / Linux / macOS：

```bash
cp -n .env.example .env
```

PowerShell（仅在不存在时复制）：

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

编辑 `.env`，填写模型、密钥和对应接口地址。也可以设置同名环境变量，环境变量优先于 `.env`。

```dotenv
LLM_MODEL_ID=your_model_id
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://your-provider.example/v1
LLM_TIMEOUT=60
```

`.env.example` 中的地址与模型仅供参考，需按自己的服务配置修改。完整 AI 审查会将源码发送至所配置的服务，并消耗该服务的 API 额度。

在 Git Bash 中运行：

```bash
./.venv/Scripts/python.exe review.py
```

审查自己的文件（把路径替换成真实文件）：

```bash
./.venv/Scripts/python.exe review.py ./your_code.py --output outputs/custom_report.md
```

使用其他配置文件：

```bash
./.venv/Scripts/python.exe review.py --env-file ./local.env
```

失败返回非零退出码。语法错误会在本地发现，不继续调用 AI。相对输入与输出路径相对于当前工作目录；默认示例和默认配置从项目目录读取。

## Notebook

Notebook 是可选的学习入口；命令行无需安装 Jupyter。

```bash
./.venv/Scripts/python.exe -m pip install -r requirements-notebook.txt
./.venv/Scripts/python.exe -m jupyterlab main.ipynb
```

Linux/macOS 将 `.venv/Scripts/python.exe` 替换为 `.venv/bin/python`。打开后选择项目虚拟环境的 Python 内核并运行单元格。Notebook 与命令行共用配置和工具。

## 测试

```bash
./.venv/Scripts/python.exe -m unittest discover -s tests -v
```

测试覆盖真实工具注册表调用、异步函数统计、无密钥静态运行、配置优先级、源文件保护、失败保留旧报告和错误信息中的密钥脱敏。AI 流程测试使用模拟客户端，不调用外部 API；真实模型的行为需在配置服务后验证。

## 项目结构

```text
CodeReviewAgent/
├── review.py                  # 命令行入口、配置与工具
├── export_repo.py             # 独立上传包导出
├── main.ipynb                 # 学习演示
├── requirements.txt           # 核心依赖
├── requirements-notebook.txt  # 可选 Notebook 依赖
├── .env.example               # 不包含真实密钥
├── .github/workflows/ci.yml   # 自动检查
├── tests/test_review.py       # 离线测试
├── data/sample_code.py        # 待审查示例
├── examples/static_report.md  # 本地运行结果示例
├── outputs/                   # 本地生成报告
├── NOTICE.md                  # 来源与修改说明
└── LICENSE.txt                # 上游许可证
```

## 许可证与来源

随项目保留上游仓库的 CC BY-NC-SA 4.0 许可证；详见 [LICENSE.txt](LICENSE.txt) 与 [NOTICE.md](NOTICE.md)。原作者与来源保留在 NOTICE 中。
