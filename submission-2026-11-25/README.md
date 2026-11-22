# 11 月 25 日提交材料包

本目录按赛事材料表整理，状态截至 2026-11-22。

| 材料 | 文件 | 状态 |
|---|---|---|
| 模型配置 | `model_config.txt` | 已生成（Qwen/Qwen3.8-27B） |
| Harness 镜像 | `harness.tar` | 已构建并验证，38.4 MiB，sha256 见 `evidence/image_manifest.txt`；平台显示“镜像可用” |
| 云端实验记录 | `evidence/cloud_experiment_record.txt` | 含本地 SwanLab 记录；平台试运行报告见 `evidence/platform_trial_1_report.txt` |
| 系统运行说明 | `docs/system_run_instructions.pdf` | 已生成 |
| 项目说明书 | `docs/project_description.pdf` | 已生成 |
| 答辩 PPT | `slides/智训引擎答辩.pptx` | 已生成，10 页，PowerPoint 可打开 |
| 项目源码 | `project_source.zip` | 已生成，约 23.5 MB |
| 作品文档 | `docs/project_documents.pdf` | 运行说明 + 项目说明合并版，已上传平台 |

## 平台进展

- 提交版本 v1 已保存并通过校验。
- 第 1 次试运行已完成（1/10），A/B/C 均完成 10 轮训练与隐藏测试预测。
- A：Accuracy 0.869014，Macro F1 0.864182。
- B：MAE 503.608618 分钟，RMSE 691.66097 分钟。
- C：MAE 41.505914 循环，RMSE 56.220512 循环，NASA 分数 48,596,667,177.96487。
- Token：输入 34,517，输出 7,680，合计 42,197，已结算。
- 正式评测 0/3，尚未启动。

## 尚未完成

- 尚未点“选为正式版本”，也尚未启动正式评测。
- 源码仓库与 SwanLab 项目目前为私有，评委访问权限需队内决定。
- 试运行指标不是正式成绩；正式成绩以主办方公布为准。
