# OpenSpec Workflow Template

这是一个面向中文协作的 OpenSpec 工作流模板，用于在项目中统一需求规划、评审、实施、验收和归档流程。

模板不预设后端、前端、数据库或部署平台。接入项目时，应以目标项目已有的技术栈、构建方式和工程规则为准。

## 目录说明

- `AGENTS.md`：项目级协作规则、OpenSpec 入口和模板维护约定。
- `.agents/skills/`：七个 OpenSpec 工作流技能入口。
- `.agents/shared/openspec/`：风险等级、工作流、评审和验收证据等共享规则。
- `openspec/config.yaml`：OpenSpec schema、上下文和产物规则配置。
- `openspec/changes/`：进行中的变更规划和实施记录。
- `openspec/specs/`：项目正式规范。
- `.gitignore`：默认忽略无关文件，仅保留模板入口和 README。

## 推荐流程

根据当前工作阶段选择入口：

1. 需求不清楚、需要比较方案时，使用 `openspec-explore`。
2. 开始一个明确的新需求时，使用 `openspec-new-change` 创建变更骨架。
3. 继续生成或修订规划时，使用 `openspec-continue-change`。
4. 规划齐备、准备实施前，使用 `openspec-review-change`。
5. 获得明确实施授权后，使用 `openspec-apply-change` 编码、测试并记录证据。
6. 实现完成后，使用 `openspec-verify-change` 核验实现和真实验证结果。
7. 验收通过并获得归档授权后，使用 `openspec-archive-change` 同步规范并归档。

默认流程只推进当前明确授权的阶段，不会因为规划完成而自动编码、提交、推送或发布。

## 风险等级

| 等级 | 适用范围 |
| --- | --- |
| `fast` | 低风险、可回滚的局部调整，不改变安全、数据模型或公共契约。 |
| `standard` | 常规单域功能或内部行为调整。 |
| `strict` | 安全、权限、持久化迁移、不可逆操作、公共破坏性契约或发布级风险。 |

三个等级默认都使用 `spec-driven`，仍需按实际依赖维护 proposal、specs、design 和 tasks 等必需产物；等级只改变规划深度和验收门槛。

## 接入项目

1. 将本模板的 `AGENTS.md`、`.agents/` 和 `openspec/` 合并到目标项目根目录。
2. 保留目标项目已有的 `openspec/config.yaml`、规范和变更，先检查差异再合并。
3. 阅读 `AGENTS.md` 和 `.agents/shared/openspec/workflow-policy.md`。
4. 根据实际风险选择 `fast`、`standard` 或 `strict`，再进入对应工作流入口。

模板自身不包含业务代码。临时文件、日志和验证缓存应放在项目 `.codex/` 目录中，不应纳入模板分发内容。
