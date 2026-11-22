# 11 月 25 日提交材料包

本目录按赛事材料表整理，状态截至 2026-11-22。

| 材料 | 文件 | 状态 |
|---|---|---|
| 模型配置 | `model_config.txt` | 已生成（Qwen/Qwen3.8-27B，待提交页绑定确认） |
| Harness 镜像 | `harness.tar` | 已构建并验证，40.2 MB，sha256 见 `evidence/image_manifest.txt` |
| 云端实验记录 | `evidence/cloud_experiment_record.txt` | 仅本地公开数据基线记录；PyTRiO/平台记录待试运行 |
| 系统运行说明 | `docs/system_run_instructions.pdf` | 已生成 |
| 项目说明书 | `docs/project_description.pdf` | 已生成 |
| 答辩 PPT | `slides/智训引擎答辩.pptx` | 已生成，10 页，PowerPoint 可打开 |
| 项目源码 | `project_source.zip` | 已生成，23.5 MB，含 Harness、SDK、三套基线、文档与 PPT |

## 尚未完成

- 平台提交版本尚未创建，镜像尚未在平台确认“可用”。
- 平台试运行 0/10，正式评测 0/2；PyTRiO 模型调用与 Token 消耗均为 0。
- 现有 SwanLab 三条记录是本地 CPU 公开数据续训，不是 PyTRiO 微调或平台正式评测。

平台提交需要队长登录并输入 PyTRiO Key；Key 不在本目录、镜像、源码或 Git 中。
