---
name: openspec-review-change
description: 聚合评审 OpenSpec 规划的范围、来源、规格、设计和任务，形成与当前文件绑定的实施结论；适用于编码前或规划变更后的评审，不代替实现验收。
---

# 评审规划

读取 [工作流规则](../../shared/openspec/workflow-policy.md)、[来源规则](../../shared/openspec/sources.md) 和 [评审检查表](../../shared/openspec/review-checklist.md)，复用已读取且未变化的内容。来源检查在本次聚合评审中完成，不自动再启动一套平行来源评审。

本入口检查“方案是否可实施”，用于编码前或规划、来源发生实质变化后。用户检查已完成的代码和测试是否满足需求时，应进入 verify-change；不要因 review 的英文名称将本入口当作通用代码评审。

## 执行

1. 确认变更，按共享元数据兼容规则解析等级，从 CLI 获取实际 schema、依赖及规划文件；报告和助手 --profile 一致。fast-change 只要求两份规划，其他 schema 按实际依赖；缺少必需产物或等级冲突时列明缺口，不能评为可实施。
2. 核对 CLI、文件、规则及报告引用可用；按 [核验方式](../../shared/openspec/manual-verification.md#核验方式) 选择 machine/manual。规划齐备时执行当前 CLI 的变更校验；本轮已取得且输入未变化的结果可复用，不启动业务服务或真实模型调用。
3. 按检查表核对范围、行为、方案、依赖及验收安排。从有效来源采纳关系出发检查正向覆盖、反向追踪和跨产物一致性，排除循环验收任务。没有 sources 目录或 PRD 不免除检查；材料不可读、冲突未解决时明确缺口，不补造结论。
4. strict 由独立评审者直接交付 `reviews/change-review.md`，无需默认复制一份独立规划报告；保留其真实发现与结论，结论修订需独立复核。无法取得独立评审时说明阻塞，不暗中降级。standard 默认在当前上下文聚合检查。
5. 按根因合并发现，输出 PASS、PAUSE 或 BLOCK。规划通过不等于实现通过，也不扩大操作授权。
6. 按共享主报告格式保存 `reviews/change-review.md`，standard/strict 保留 `Change Source Coverage 检查结果`；fast 可简写。同范围复审更新固定报告。报告及采用的辅助材料定稿且真实 PASS 后，machine 用 `record-plan` 绑定规划、持续约束和报告，用 `--reference` 登记允许修改的实现参考；strict 默认 `--report` 与 `--independent` 同路径，辅助报告用 `--review-evidence` 逐个绑定。manual 保存等价清单，不能以指纹替代实际评审。
7. 立即按所选方式复核输入、报告、profile 与记录：machine 执行 `check-plan`，manual 重新枚举并比较清单。失败时查明差异，不能输出“指纹有效”。

## 复用与交接

缓存有效且用户没有要求重新评审时可复用，但应说明是复用。用户要求显式复审时按请求检查，不能只返回缓存命中。

报告注明检查范围、未检查内容、阻塞、警告、评审独立性及实施所需验证。PASS 后可交给 `openspec-apply-change`；PAUSE/BLOCK 回到规划修订或用户决策。

指纹是新鲜度校验，不是评审质量或身份的机器证明。不得手动写一个 PASS 值来代替尚未完成的评审。
