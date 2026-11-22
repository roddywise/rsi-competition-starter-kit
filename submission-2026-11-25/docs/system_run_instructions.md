# 智训引擎 Harness 系统运行说明

**版本：开发验证稿（2026-11-22）**  
**目标协议：`contest.harness.workspace.v2` / contest_harness SDK 1.0.4**  
**重要状态：Python 离线验收、容器 describe/predict/train 冒烟测试、镜像构建与 docker save 已完成；平台镜像已可用，提交版本 v1 校验通过，第 1 次试运行已完成。**

## 1. 运行环境

- 容器目标平台：Linux/amd64。
- 基础环境：Python 3.12，NumPy 1.26.4，CPU 单线程 NumPy MLP。
- 平台沙箱：规则页当前说明 2 核 CPU、4 GiB 内存；`/app`、`/data`、`/previous` 只读，`/workspace` 可写。
- Harness SDK：随项目固定携带 1.0.4 归档，SHA-256 为 `7afd282d6b5fd889d64d0515a67d169806970e36200689b18d2040026167a4af`。
- 模型配置：`../model_config.txt`，当前拟选 `Qwen/Qwen3.8-27B`。平台绑定需由提交版本确认。

## 2. 构建与导出

在 `starter-kit` 目录执行：

```powershell
docker build --platform linux/amd64 -f .\harness\Dockerfile -t rsi-harness:1.0.4 .
docker save -o harness.tar rsi-harness:1.0.4
```

平台只接受 `docker save` 导出的单个 Linux/amd64 未压缩 tar 镜像；不能用源码 ZIP、Dockerfile 或 `docker export` 代替。当前导出文件为 `harness.tar`，40,233,984 字节（约 38.4 MiB），低于 50 MB 门槛，可直接上传。SHA-256：`08441d807fafacff8cd193e1ec5139bd6a751802e58954292b66bfd92c67036f`。

镜像基于 `python:3.12-alpine3.20`，已在本机 Docker Desktop 中完成构建、`describe`、A/B/C 预测和模拟宿主完整训练协议验证。平台提交版本尚未创建，真实宿主兼容性与试运行仍待执行。

## 3. SDK 入口

固定入口为：

```text
python3 /app/harness.py describe
python3 /app/harness.py train
python3 /app/harness.py predict
```

`describe` 声明 `contest.harness.workspace.v2`、`host_gateway_rpc`，并支持 `classification` 与 `regression`。`train(rnd)` 按 A/B/C 数据集代号分流；`predict(sample, model_dir)` 读取平台选中的 checkpoint。

## 4. 每轮训练流程

1. 读取 `rnd.dataset_key`、冻结任务合同、平台公开投影路径及本数据集历史记录。
2. 只对公开训练/验证的 `inputs` 计算 PSI 和标准化均值差，生成候选中的 `drift_report.json`。漂移诊断不读取 `answer`、`id` 或 `meta`，验证集仍不参与梯度更新。
3. 通过 `rnd.model()` 请求一次受限决策。模型只能从程序内白名单选择 `epochs`、`learning_rate`、`batch_size`；无效 JSON 回退为基线学习率/批大小及 1 epoch，不执行模型生成的代码或命令。
4. 通过 `rnd.parent.path()` 校验平台父 checkpoint 摘要，再调用对应的现有 `train_run()` 续训。
5. 候选目录包含 `checkpoint.npz`、`training.json`、`history.jsonl` 和 `drift_report.json`。候选大小保守限制为 64 MiB，并服从 `rnd.limits`。
6. `rnd.submit_candidate()` 返回的平台验证摘要决定选择：A 看 Macro-F1（越高越好），B/C 看 RMSE（越低越好）；严格改善才接受，否则保留父模型。
7. 用 `rnd.finish()` 记录实际读过的历史 ID、本轮模型调用 ID、假设、配置和决策。RPC 结果不明时立即停止，不在同一会话重试。

## 5. 预测协议

SDK 每次把一个 JSONL 样本传给 `predict(sample, model_dir)`。系统用 `CONTEST_ARTIFACT_PATH` 加载被选中的 checkpoint，并校验任务、数据集代号及特征结构。

- 分类：返回六类气体标签和 0–1 分数，唯一最高分。
- 回归：返回有限非负数值；B 单位为分钟，C 单位为循环。

SDK 逐行写出并刷新响应；预测不等待 stdin EOF。隐藏测试标签不进入容器，也不参与输入。

## 6. 本地离线复现

在 Windows PowerShell 中激活 Python 3.12 / NumPy 1.26.4 虚拟环境，按 `harness/README.md` 校验并解压 SDK 归档，然后运行：

```powershell
python -m unittest tests.test_sdk tests.test_contract_regressions tests.test_transport_regressions -v
python -m unittest discover -s .\harness\tests -v
python -m unittest discover -s .\tasks\A-gas\baselines\tests -v
python .\tasks\B-bearing\run_core_tests.py
python -m unittest discover -s .\tasks\C-engine\baselines\tests -v
```

SDK 离线测试在 Windows 需设置 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`。不要运行 SDK 的 `tests.test_live`，也不要把 PyTRiO Key放进本地测试。

## 7. 异常与回滚

- 父 checkpoint 未声明、摘要不匹配、任务类型不匹配：停止当前轮，不训练。
- 模型响应不符合 schema/超出白名单：回退安全超参数，继续受控训练。
- 平台测量没有有效主指标：保留父模型。
- 候选主指标没有严格改善：回滚到父模型。
- `RPC_OUTCOME_UNKNOWN`、超时或中断：停止当前会话，不重发同一请求。
- 公开训练/验证 schema 不一致、文件缺失或文件超出基线读取限制：停止并报告，不访问其他路径。

## 8. 密钥、额度与试运行

API Key 只由队长在平台安全输入；不写入镜像、仓库、日志、SwanLab 或本说明。平台试运行会真实调用模型并可能产生费用；本队授权上限为 3 次，必须逐次检查结果。正式评测不在本阶段启动。当前已完成的 SwanLab 记录是本地公开数据开发参考，不是 PyTrIO 微调记录或平台正式成绩。

平台第 1 次试运行（v1，Qwen/Qwen3.8-27B）已完成：A/B/C 均完成 10/10 轮训练与隐藏测试预测；输入 34,517 Token，输出 7,680 Token，合计 42,197 Token，平台显示已结算。试运行 1/10。v1 已选为正式版本并锁定，第 1 次正式评测已创建并入队，正式评测 1/3。以上试运行指标不是正式成绩。
