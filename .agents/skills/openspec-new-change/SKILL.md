---
name: openspec-new-change
description: 为明确的新需求建立变更骨架、确定范围与风险等级；逐步规划时在骨架处停止，明确要求完整规划时交接 continue-change 连续生成，不修改业务代码。
---

# 创建变更骨架

读取 [工作流规则](../../shared/openspec/workflow-policy.md)、[来源规则](../../shared/openspec/sources.md) 及本次必要的 [项目上下文](../../shared/openspec/project-context.md)。已读取且未变化的内容直接复用。

## 执行

1. 确定当前项目、规划根、目标和非目标。按 [探索与规划交接](../../shared/openspec/workflow-policy.md#探索与规划交接) 承接对话或已保存的探索结论，核对相关项目现状；没有探索记录时直接以明确需求为起点，不要求补做 explore。需求跨多个可独立交付能力时建议拆分，未经明确要求不批量创建变更。
2. 使用有含义的 kebab-case 名称。已存在同名变更时读取状态并澄清继续还是另建，不覆盖原目录。
3. 按实际风险选择等级：新建 fast 显式用 fast-change，standard/strict 用 spec-driven。按共享规则保留已有或用户显式 schema 选择并核对兼容性；不能因改动小而把业务行为变化列为 fast。用 `openspec schema which "<已选 schema>" --json` 核对可解析性与来源；失败停止创建，不自动降级或 init。
4. 用已核实的 schema 创建一次，不额外创建第二个变更：

   ```bash
   openspec new change "<变更名>" --schema "<已选 schema>"
   ```

5. 根据返回路径读取 `.openspec.yaml`，按共享的 [元数据兼容规则](../../shared/openspec/workflow-policy.md#元数据读取与兼容) 登记 `x-workflow_profile`，fast-change 同时写 `skip_specs: true`。保留其他合法字段，未知负责人不填写。冲突必须报告实际值，不靠更换参数降低等级。
6. standard/strict 在 `sources/user-request.md` 保存必要用户原文及已确认补充决定，登记稳定编号、采纳范围及替代关系。fast 简单输入交给 proposal 的 Source Inputs，不为了保存来源提前生成 proposal。
7. 运行 `openspec status --change "<变更名>" --json`，获取依赖和下一份就绪产物。只建立骨架时，不宣称 proposal 或规划已完成。

## 交接

输出变更名称、实际路径、范围摘要、风险等级及原因、下一份产物。下一步是 `openspec-continue-change`。

默认创建骨架后停止，不顺手生成 proposal。用户明确要求完成全部规划时，可以交接 continue-change 按依赖生成，不重复询问同一授权；规划授权不自动包含评审或实施。

按共享入口规则区分“逐步推进”和“完成全部规划”。已有 propose 产物时复用现有变更，补足元数据后提示 continue-change 或 review-change，仅按明确授权执行；不能为切换入口再次创建变更。向 continue-change 交接已确认范围、实际来源和未决问题；候选建议不得自动纳入变更范围，缺少阻塞性信息时先针对性澄清，不重启完整访谈。
