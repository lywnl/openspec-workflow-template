---
name: openspec-new-change
description: 为明确的新需求建立变更骨架、确定范围与风险等级；逐步规划时在骨架处停止，明确要求完整规划时交接 continue-change 连续生成，不修改业务代码。
---

# 创建变更骨架

读取 [工作流规则](../../shared/openspec/workflow-policy.md) 和 [上下文发现](../../shared/openspec/project-context.md)。

## 执行

1. 确定当前项目、规划根、目标和非目标。按 [探索与规划交接](../../shared/openspec/workflow-policy.md#探索与规划交接) 承接对话或已保存的探索结论，核对相关项目现状；没有探索记录时直接以明确需求为起点，不要求补做 explore。需求跨多个可独立交付能力时建议拆分，未经明确要求不批量创建变更。
2. 使用有含义的 kebab-case 名称。已存在同名变更时读取状态并澄清继续还是另建，不覆盖原目录。
3. 按风险选择 fast、standard 或 strict，默认均使用 spec-driven。通过 `openspec schema which "<已选 schema>" --json` 核对可解析性与来源，不凭本地目录是否存在判断内置 schema。用户明确指定或已有项目采用其他 schema 时先核对产物、风险要求、任务格式与核验工具是否兼容；冲突先说明并确认，不覆盖已有选择，不把流程修复塞进实施任务。解析失败停止创建，不自动降级或重新初始化；布局不受机器助手支持时按共享规则选择人工核验。
4. 按已核实的 schema 创建一次；默认命令如下。用户或项目明确选择其他兼容 schema 时使用其真实名称替换参数，不运行第二条创建命令：

   ```bash
   openspec new change "<变更名>" --schema spec-driven
   ```

5. 根据 CLI 返回的实际路径读取变更 `.openspec.yaml`，保留既有字段，登记本模板的 `workflow_profile`；后续报告和助手 `--profile` 沿用该值，不能将 CLI 的 --strict 当作风险登记。已有等级冲突先说明，不擅自覆盖。owner 只记录已知、获准的信息，不读取无关个人配置来填充。
6. 运行 `openspec status --change "<变更名>" --json`，获取依赖和下一份就绪产物。创建命令只建立骨架时，不宣称 proposal 已存在。

## 交接

输出变更名称、实际路径、范围摘要、风险等级及原因、下一份产物。下一步是 `openspec-continue-change`。

默认创建骨架后停止，不顺手生成 proposal。用户明确要求完成全部规划时，可以交接 continue-change 按依赖生成，不重复询问同一授权；规划授权不自动包含评审或实施。

按共享入口规则区分“逐步推进”和“完成全部规划”。已有 propose 产物时复用现有变更，补足元数据后提示 continue-change 或 review-change，仅按明确授权执行；不能为切换入口再次创建变更。向 continue-change 交接已确认范围、实际来源和未决问题；候选建议不得自动纳入变更范围，缺少阻塞性信息时先针对性澄清，不重启完整访谈。
