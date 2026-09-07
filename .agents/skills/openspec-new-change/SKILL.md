---
name: openspec-new-change
description: 为明确的新需求建立变更骨架、确定范围与风险等级；逐步规划时在骨架处停止，明确要求完整规划时交接 continue-change 连续生成，不修改业务代码。
---

# 创建变更骨架

读取 [工作流规则](../../shared/openspec/workflow-policy.md) 和 [上下文发现](../../shared/openspec/project-context.md)。

## 执行

1. 确定当前项目、规划根、目标和非目标。按 [探索与规划交接](../../shared/openspec/workflow-policy.md#探索与规划交接) 承接对话或已保存的探索结论，核对相关项目现状；没有探索记录时直接以明确需求为起点，不要求补做 explore。需求跨多个可独立交付能力时建议拆分，未经明确要求不批量创建变更。
2. 使用有含义的 kebab-case 名称。已存在同名变更时读取状态并澄清继续还是另建，不覆盖原目录。
3. 按风险选择 fast、standard 或 strict；使用用户明确指定的 schema，否则遵循项目默认值。低风险且项目允许时可用本模板的 fast-change；指定 schema 无法承载必需的高风险规划时说明冲突，不将 strict 塞进轻量流程。提前检查任务格式、目录布局和核验工具是否适配；不受机器助手支持时按共享规则选择人工核验，不改造项目以迎合助手。
4. 选择以下一条当前 CLI 支持的创建命令，不要对同一名称连续执行两条：

   ```bash
   openspec new change "<变更名>"
   # 仅在已选择轻量 schema 时使用：
   openspec new change "<变更名>" --schema fast-change
   ```

5. 根据 CLI 返回的实际路径读取 `.openspec.yaml`，保留既有字段，登记本模板的 `workflow_profile`。owner 只记录已知、获准的信息，不读取无关个人配置来填充。
6. 运行 `openspec status --change "<变更名>" --json`，获取依赖和下一份就绪产物。创建命令只建立骨架时，不宣称 proposal 已存在。

## 交接

输出变更名称、实际路径、范围摘要、风险等级及原因、下一份产物。下一步是 `openspec-continue-change`。

本入口不自动扩展为全部规划或实施；用户已经明确要求完成规划时，可以继续调用对应技能，不重复询问同一授权。

按共享入口规则区分“逐步推进”和“完成全部规划”。已有 propose 产物时复用现有变更，补足元数据后进入 continue-change 或 review-change；不能为切换入口再次创建变更。向 continue-change 交接已确认范围、实际来源和未决问题；候选建议不得自动纳入变更范围，缺少阻塞性信息时先针对性澄清，不重启完整访谈。
