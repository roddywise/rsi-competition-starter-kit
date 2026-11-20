# RSI Harness（SDK 1.0.4）

此目录提供 A/B/C 共用的 `contest.harness.workspace.v2` Harness。它复用各任务现有 CPU NumPy 训练器，不修改官方训练包；每轮模型调用只能选择代码中白名单的 epoch、学习率和 batch size。

本地离线验收不会调用 PyTRiO，也不需要 API Key。离线验收通过后，队长最多授权 3 次平台试运行；正式评测不在本阶段执行。

## 环境要求

- Python 3.12
- NumPy 1.26.4
- Docker Desktop（仅镜像构建与 `docker save` 需要）

SDK 1.0.4 归档位于 `vendor/contest-harness-sdk-1.0.4.tar.gz`，SHA-256 见 `vendor/SDK_SHA256.txt`。容器从本地已校验的 SDK 源码运行，不把 SDK 包下载交给比赛运行时。
Docker 构建会从包索引安装锁定的 NumPy 1.26.4，因此构建机需要访问 Python 包索引；比赛容器运行时不访问外网。

## 本地测试

在 PowerShell 中从 `starter-kit` 目录运行。先将 SDK 归档解到唯一临时目录，再运行 SDK 自带的离线测试：
先激活 Python 3.12 且已安装 NumPy 1.26.4 的虚拟环境。

```powershell
$SdkArchive = ".\harness\vendor\contest-harness-sdk-1.0.4.tar.gz"
$ExpectedSdkSha256 = "7afd282d6b5fd889d64d0515a67d169806970e36200689b18d2040026167a4af"
$ActualSdkSha256 = (Get-FileHash -Algorithm SHA256 $SdkArchive).Hash.ToLowerInvariant()
if ($ActualSdkSha256 -ne $ExpectedSdkSha256) { throw "SDK checksum mismatch" }
$SdkTemp = Join-Path $env:TEMP ("contest-harness-sdk-1.0.4-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $SdkTemp | Out-Null
tar.exe -xzf $SdkArchive -C $SdkTemp
if ($LASTEXITCODE -ne 0) { throw "SDK archive extraction failed" }

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
Push-Location (Join-Path $SdkTemp "contest-harness-sdk-1.0.4")
python -m unittest tests.test_sdk tests.test_contract_regressions tests.test_transport_regressions -v
$SdkTestExit = $LASTEXITCODE
Pop-Location
if ($SdkTestExit -ne 0) { throw "SDK offline tests failed" }
```

再运行本项目的 A/B/C 离线训练、候选选择和预测测试：

```powershell
python -m unittest discover -s .\harness\tests -v
```

所有测试都通过后，可单独确认 SDK 入口描述。`$SdkTemp` 保持在当前 PowerShell 会话中：

```powershell
$env:PYTHONPATH = "$(Join-Path $SdkTemp 'contest-harness-sdk-1.0.4');$(Resolve-Path .\harness\app)"
python .\harness\app\harness.py describe
```

预期输出的 `protocol` 为 `contest.harness.workspace.v2`，`model_access` 为 `host_gateway_rpc`，`tasks` 为 `classification` 和 `regression`。

Windows 下运行 SDK 自带测试需设置 UTF-8 环境变量，避免测试宿主把中文协议帧按系统代码页编码。测试不包括会调用真实模型的 `tests.test_live`。

## 镜像构建

构建上下文必须是 `starter-kit` 根目录，以便 Dockerfile 从 `tasks/A-gas`、`tasks/B-bearing` 和 `tasks/C-engine` 复制基线代码：

```powershell
docker build --platform linux/amd64 -f .\harness\Dockerfile -t rsi-harness:1.0.4 .
docker save -o harness.tar rsi-harness:1.0.4
```

提交页面只接受 `docker save` 导出的单个 Linux/amd64 未压缩 tar 镜像。不要上传源码 ZIP、项目目录 ZIP、Dockerfile 或 `docker export` 文件。

## 平台运行边界

- 镜像导出前先完成上面的离线测试。此机当前没有 Docker/Podman，因此尚未构建或验证真实镜像。
- 平台试运行会真实调用 PyTRiO，可能产生费用并消耗全队额度。使用前确认本次运行覆盖的任务和轮数；每次试运行完成后查看结果，再决定是否使用下一次，最多 3 次。
- 不启动正式评测。PyTRiO Key 由队长在平台安全输入，不放进镜像、仓库、SwanLab 或聊天。
- 管理员公告与 SDK 1.0.4 对产物上限的说明不一致；首版候选保守限制在 64 MiB，并同时遵守运行时 `rnd.limits`。
