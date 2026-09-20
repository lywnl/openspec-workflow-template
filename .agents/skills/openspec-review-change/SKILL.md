---
name: openspec-review-change
description: 聚合评审 OpenSpec 规划的范围、来源、规格、设计和任务，形成与当前文件绑定的实施结论；适用于编码前或规划变更后的评审，不代替实现验收。
---

# 评审规划

读取 [工作流规则](../../shared/openspec/workflow-policy.md) 和 [评审检查表](../../shared/openspec/review-checklist.md)。不要重复调用同一来源的多套评审技能。

本入口检查“方案是否可实施”，用于编码前或规划、来源发生实质变化后。用户检查已完成的代码和测试是否满足需求时，应进入 verify-change；不要因 review 的英文名称将本入口当作通用代码评审。

## 执行

1. 确认变更，从其 `.openspec.yaml` 读取 workflow_profile，从 CLI 获取 schema、依赖图及实际规划文件；报告和助手 --profile 沿用元数据。缺少必需产物或存在未解决等级冲突时列明缺口，不能评为可实施，fast 也不能省略 spec-driven 的必需规格或设计。
2. 进行当前步骤必要的预检：CLI 与文件是否可读取、规则是否可取得、报告引用是否有效；按 [核验方式](../../shared/openspec/verification-evidence.md#核验方式) 选择并登记 machine 或 manual。规划评审不需要启动业务服务或执行真实模型调用。
3. 检查范围、来源、可观察行为、关键决策、依赖和验收交接，排除“必须先验收通过才能进入验收”的循环任务。CLI 齐备和格式通过不代表语义通过。没有外部材料时按对话/代码事实评审，不伪造外部覆盖结论。
4. 按 profile 使用检查表；strict 取得基于当前规划的独立评审。无法取得时说明阻塞，不暗中降级。standard 不因下层检查而强制另起子代理。
5. 按根因合并发现，输出 PASS、PAUSE 或 BLOCK。规划通过不等于实现通过，也不扩大操作授权。
6. 保存 `reviews/change-review.md`，引用已有需求与设计，fast 可用短格式。只有真实 PASS 后，machine 用 `record-plan` 绑定规划、持续约束和报告，用 `--reference` 单独登记允许实施修改的代码、测试及配置；不把所有读过的文件都列为 `--source`。manual 同样区分两类输入并保存清单；strict 均需独立评审文件。
7. 立即按所选方式复核输入、报告、profile 与记录：machine 执行 `check-plan`，manual 重新枚举并比较清单。失败时查明差异，不能输出“指纹有效”。

## 复用与交接

缓存有效且用户没有要求重新评审时可复用，但应说明是复用。用户要求显式复审时按请求检查，不能只返回缓存命中。

报告注明检查范围、未检查内容、阻塞、警告、评审独立性及实施所需验证。PASS 后可交给 `openspec-apply-change`；PAUSE/BLOCK 回到规划修订或用户决策。

指纹是新鲜度校验，不是评审质量或身份的机器证明。不得手动写一个 PASS 值来代替尚未完成的评审。
