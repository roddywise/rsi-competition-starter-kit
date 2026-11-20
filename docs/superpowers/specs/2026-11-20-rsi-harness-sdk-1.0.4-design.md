# RSI Harness SDK 1.0.4 接入设计

- 日期：2026-11-20
- 状态：队长已批准，按规格实施
- 范围：本地离线 Harness 适配；平台试运行仅作为离线验收后的后续阶段

## 目标

为 A 气体分类、B 轴承分钟级 RUL、C 发动机循环级 RUL 构建一个统一的竞赛 Harness 镜像，接入智训引擎当前发布的 `contest_harness` SDK 1.0.4（协议 `contest.harness.workspace.v2`）。

首版须能通过 SDK `describe`、离线训练协议、候选产物和预测验证。训练算法继续使用现有官方 CPU NumPy 基线；模型调用仅能选择经校验的超参数，不生成或执行任意代码。

## 已确认的平台约束

- 规则页显示正式评测已开放；当前队伍提交版本为 0，试运行 0/10，正式评测 0/2。首次正式评测可由队伍启动，第二次需管理员审批。
- 每个数据集最多 10 轮优化；试运行按队伍累计，执行真实模型调用，可能产生费用。
- 提交页列出两种模型类型：持久化 Sampler 微调权重；以及需二次确认的官方基础模型。基础模型白名单为 `Qwen/Qwen3.5-4B` 与 `Qwen/Qwen3.8-27B`。
- 新 SDK 的固定入口为 `python3 /app/harness.py describe|train|predict`；选手模块提供 `train(rnd)` 与 `predict(sample, model_dir)`。
- 当前平台 CPU 配额为 2 核、内存 4 GiB。平台数据和父产物只读；候选写入 `/workspace`。
- 续训必须使用 `rnd.parent.path()` 读取并校验本轮平台父检查点。模型调用由 `rnd.model()` 通过宿主完成，API Key 不进入镜像、仓库或训练记录。
- SDK 1.0.4 压缩包 SHA-256 已校验为 `7afd282d6b5fd889d64d0515a67d169806970e36200689b18d2040026167a4af`。
- 管理员公告写产物总量不超过 64 MiB；SDK 1.0.4 文档描述更大的分块上传上限。此材料存在不一致，首版候选额外限制在 64 MiB 内，并服从运行时 `rnd.limits`。
- 当前机器未安装 Docker 或 Podman。可以完成 Python 离线验证，但不能在此机生成 `docker save` 镜像归档或发起平台试运行。

## 方案

使用一个薄适配层复用三份任务训练器，不改官方训练包：

```text
starter-kit/
  harness/
    Dockerfile
    vendor/contest-harness-sdk-1.0.4.tar.gz
    app/
      harness.py
      contest_submission.py
      task_a/__init__.py
      task_b/__init__.py
      task_c/__init__.py
    tests/
  tasks/
    A-gas/baselines/...
    B-bearing/baselines/...
    C-engine/baselines/...
```

Docker 构建上下文使用 `starter-kit`，从现有任务目录将 `baselines` 复制到对应的 Python 命名空间。官方文件保持原样，不在运行时动态改写源码。镜像使用 Python 3.12 与 NumPy 1.26.4，以非 root 用户运行；SDK 从已校验的本地归档解压并加入 `PYTHONPATH`。NumPy 从包索引安装时需要构建环境联网；若构建环境不允许联网，应在后续实现阶段提供经过校验的本地 wheel。首版直接调用 `rnd.model()`，不需要额外的 PyTrIO 客户端或 API Key。

## 训练流程

1. `describe` 声明协议 `contest.harness.workspace.v2`，并声明 `classification` 与 `regression` 两类任务。
2. `train(rnd)` 根据 `rnd.dataset_key` 选择 A、B 或 C 训练模块；同时校验 `rnd.task` 中的任务类型、主指标和方向。
3. 从 `rnd.data` / `rnd.task["public_projection"]` 读取平台提供的公开训练与验证路径。梯度训练只使用训练集；验证集只作模型选择；不使用隐藏数据，也不把 `id` 或 `meta` 拼入特征。
4. 读取 `rnd.history()`，只把历史中的主指标和白名单超参数发送给 `rnd.model()`；不把历史中的自由文本原因或代码送进提示。宿主已附加官方提示，选手消息不得重复粘贴官方提示。
5. 模型只可从以下白名单选取 `epochs`、`learning_rate`、`batch_size`；首版不接受代码补丁、Shell 命令或路径：
   - A：epochs `{1, 2, 3}`；learning rate `{0.001, 0.003, 0.005}`；batch size `{64, 128, 256}`。
   - B：epochs `{1, 2, 3}`；learning rate `{0.001, 0.003, 0.005}`；batch size `{64, 128, 256}`。
   - C：epochs `{1, 2, 3}`；learning rate `{0.001, 0.002, 0.003}`；batch size `{128, 256, 512}`。
6. 严格解析模型返回的 JSON。缺字段、字段超出白名单或响应无效时，改用任务配置中的基准学习率和 batch size，并执行 1 epoch；记录该回退，不执行响应中的任何代码或命令。
7. 从本轮 `rnd.parent.descriptor["checkpoint_paths"]` 中读取唯一声明的检查点，经 `rnd.parent.path()` 校验摘要后，调用对应的 `train_run()` 续训。候选写入全新 `/workspace/candidate`，包含 `checkpoint.npz`、`training.json` 和 `history.jsonl`。优化器状态已保存在 checkpoint 中，首版不单独写 `/state`。
8. 用 `rnd.submit_candidate()` 提交候选，并按 SDK/运行时限制检查文件数、摘要和字节数。只声明实际存在的 checkpoint；预测入口为 `["python3", "/app/harness.py", "predict"]`。
9. 使用平台返回的验证摘要作为正式候选分数：A 的 Macro-F1 越高越好，B/C 的 RMSE 越低越好。相较父模型有严格改善时选择候选；未改善或候选摘要无效时选择父模型。首轮若平台没有提供父模型指标，但候选指标有效，则可选择该候选作为第一个已测量产物，并记录“无可比父指标”，不得宣称取得提升；若候选指标无效则选择父模型。`rnd.finish()` 引用实际读取的历史 ID 和本轮真实模型调用 ID。
10. RPC 超时、中断或 `RPC_OUTCOME_UNKNOWN` 时立即停止本轮，不在同一会话重试，也不重复提交。

## 预测流程

- 通过 `sample.dataset_key` / 平台预测上下文确定任务；再用检查点的 profile 与任务类型交叉校验。若上下文缺少数据集代号，可从受信任的已校验 checkpoint 元数据识别 B 与 C，不根据输入特征猜测任务。
- 使用 `CONTEST_ARTIFACT_PATH` 加载被选中的 `checkpoint.npz`，只读取 `sample.inputs`。
- 分类返回六种气体的标签和概率；回归返回有限、非负的分钟或循环值。SDK 入口负责逐行写出、刷新并校验协议形状。

## 离线验收

运行 SDK 自带离线测试，不运行 `tests.test_live`：

```sh
python3 -m unittest tests.test_sdk tests.test_contract_regressions tests.test_transport_regressions -v
```

另加本项目测试，使用模拟宿主和模拟模型回执，不发出真实 PyTrIO 调用：

- `describe` 协议、版本和任务声明符合 SDK 1.0.4。
- A/B/C 各完成一次模拟训练：正确分流、使用公开数据和已校验父检查点、写入三个候选文件，并引用真实模拟的 model call ID 与 history ID。
- 模型无效 JSON/超出白名单时确定性回退；父检查点摘要或任务不匹配时安全失败。
- 平台摘要改善时选择候选；不改善或缺少有效指标时选择父检查点。
- 首轮父模型没有可用指标时，只能记录为第一个已测量候选，不得记成“优于基线”。
- A/B/C 预测输出符合分类/回归协议；特征、类别或任务不匹配时拒绝预测。
- 候选大小不超过 64 MiB；测试中不包含真实 API Key，也不连接 PyTrio。

本地 Python 验收通过不代表镜像已构建或平台兼容性已确认。

## 试运行边界

- 队长已授权离线验收通过后最多进行 3 次平台试运行；这是上限，不要求用满。
- 试运行逐次执行：上传/选择镜像并保存版本；运行一次；检查完整状态和结果后，才决定是否使用下一次。
- 若失败，先区分协议兼容、镜像格式、资源、网络或平台服务问题；不盲目重试。正式评测次数保持 0，不点击正式评测。
- 第一次试运行前确认“一次试运行”实际覆盖的任务/轮数及潜在模型调用量。当前尚未在平台运行，不预设每次调用数或费用。
- 试运行需要 Docker/Podman 可用的构建环境和由队长在平台安全输入的 PyTrIO Key。助手不请求、不记录、不提交该 Key。

## 文档维护

更新 `starter-kit/START_HERE.txt` 与 `starter-kit/prompts/TEAM_LEAD.txt` 中过时的平台状态，指向 SDK 1.0.4 与离线测试流程；保留 B 包打包测试缺失模块的说明，不伪造 `scripts/package_baselines.py`。不改官方 A/B/C 训练文件、公开数据、checkpoint 或原始压缩包。

## 明确不做

- 不调用真实 PyTrIO 或消耗平台试运行额度，直到全部离线测试通过且 Docker 构建环境就绪。
- 不上传镜像、不保存提交版本、不启动正式评测，除非后续明确到达已授权的试运行阶段。
- 不让模型生成/执行任意代码、Shell、网络请求或文件路径。
- 不访问隐藏样本/标签，不把 API Key 写入代码、镜像、仓库、SwanLab 配置或实验记录。
- 不把本地 `training.json` 指标冒充平台正式评分。
