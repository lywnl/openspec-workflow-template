# OpenSpec Workflow Template

面向中文协作的通用 OpenSpec 流程模板，将用户需求、规划、评审、实施证据和归档连接起来。技术栈、工程命令和环境以接入项目的实际约定为准。

## 入口与使用顺序

| 当前阶段 | 技能 | 本阶段产物及停止位置 |
| --- | --- | --- |
| 随时调查问题、讨论方案（可选） | openspec-explore | 理解、候选方案或未决问题，无强制产物；获准时保存探索笔记或交接规划 |
| 创建变更 | openspec-new-change | 骨架、等级元数据；standard/strict 保存必要用户来源，尚无 proposal |
| 继续规划 | openspec-continue-change | 默认下一份就绪产物；“完成全部规划”才连续生成 |
| 规划评审 | openspec-review-change | reviews/change-review.md；真实 PASS 后登记规划基线 |
| 实施 | openspec-apply-change | 当前任务的实现、验证及证据，及时更新任务状态 |
| 实现验收 | openspec-verify-change | reports/verification.md；满足条件才记录验收通过 |
| 同步规范、归档 | openspec-archive-change | reports/archive-record.md；需要同步时使用归档检查点 |

聊天中选择 `$openspec-<名称>`，终端运行 `openspec ...`。首次使用核对目标项目中的实际技能文件，避免误用其他项目的同名技能。按阶段及已有授权推进；规划齐备不自动授权评审或编码，完整实施授权涵盖必要实现与验收，不包含提交、推送、发布或归档。

explore 可以在变更前或变更过程中使用，不要求每次都形成方案或进入规划。[官方定位](https://github.com/Fission-AI/OpenSpec/blob/main/docs/explore.md)允许在明确授权后保存指定规划产物；本模板由 new-change／continue-change 承接这类写入，复用风险、来源和 schema 规则，已有授权无需重复确认。官方流程及可选入口见 [Workflows](https://github.com/Fission-AI/OpenSpec/blob/main/docs/workflows.md)。

## 风险等级与 Schema

| 等级 | 适用范围 | 新建时的规划 |
| --- | --- | --- |
| fast | 不改变规范约定的低风险修复、行为保持重构、文案或工具调整 | fast-change：proposal → tasks |
| standard | 普通功能或业务行为调整 | spec-driven：proposal、specs、design、tasks，按 CLI 依赖生成 |
| strict | 权限、隔离、持久化迁移、破坏性契约等高风险边界 | 完整四件套，加独立规划评审、独立代码质量评审及适用真实环境验证 |

根配置默认 spec-driven。new-change 显式选择 schema；fast-change 必须声明 `skip_specs: true`，表示没有规范级行为变化，不是通用跳过开关。已有变更按实际 schema，不因标记 fast 删除其他产物；风险升级时在同一变更补齐规划并复评。

新等级使用 `x-workflow_profile`。旧 `workflow_profile` 兼容读取；并存冲突停止推进，缺失按实际范围登记。规范化旧字段需已有修改授权；不批量改写历史或修改 JSON 假装旧指纹有效。完整定义见 [工作流规则](.agents/shared/openspec/workflow-policy.md)。

## 产物目录

以下是 standard/strict 按阶段逐步形成的目录，不在创建骨架时一次建齐：

```text
openspec/changes/<变更名>/
├── .openspec.yaml
├── sources/
│   └── user-request.md
├── proposal.md
├── specs/<能力>/spec.md
├── design.md
├── tasks.md
├── reviews/
│   ├── change-review.md
│   ├── planning-review.json
│   ├── implementation-review.md       # strict 独立代码质量评审
│   └── <专题>-planning-review.md       # 确有独立专题才增加
└── reports/
    ├── verification.md
    ├── verification-manifest.json     # standard/strict 必需，fast 可选
    ├── verification.json
    ├── archive-record.md
    └── archive-checkpoint/journal.json # 有规范同步的机器归档
```

JSON 指纹适用于 machine；manual 使用明确标注的人工输入清单，不伪造机器记录。正常归档后整个变更移动到 `openspec/changes/archive/YYYY-MM-DD-<变更名>/`，保留原报告与记录字节，正式规范合并到 `openspec/specs/`。

fast 默认只有 proposal/tasks 两份规划，简单来源保存在 proposal 的 Source Inputs，评审与验收用短报告；不创建空 specs、design、独立报告或同步检查点。

`sources/` 保存真实需求和补充决定；主报告的 “Change Source Coverage 检查结果” 检查这些有效要求如何进入规划，同时反查是否增加了未经确认的要求。没有 sources 目录仍须检查对话来源。

standard/strict 固定使用 [主报告格式](.agents/shared/openspec/review-checklist.md#主报告格式)。同范围复审更新同一 change-review.md，来源检查默认并入主报告；strict 独立评审直接交付该文件。已有辅助报告可沿用原路径，通过可重复的 `--review-evidence` 绑定，不默认复制评审文件。

## 共享规则与脚本

| 路径（位于 .agents/shared/openspec/） | 职责 |
| --- | --- |
| workflow-policy.md | 风险、元数据、授权与阶段转换 |
| project-context.md | 项目事实、工程入口及读取边界 |
| sources.md | 来源保存、编号、采纳与替代关系 |
| review-checklist.md | 规划评审、主报告、辅助报告及规划基线 |
| verification-evidence.md | 实施证据、验收映射、独立代码评审及验收记录 |
| manual-verification.md | 核验模式选择及人工、多根、链接处理 |
| archive-workflow.md | 规范同步、归档检查点、恢复和取消 |
| scripts/evidence.py | 文件基线、任务状态及辅助报告绑定 |
| scripts/evidence_manifest.py | 已登记验收条目的结构与引用检查 |
| scripts/archive_checkpoint.py | 同步前后基线、真实 CLI 核验与归档恢复 |

规划指纹归一化任务勾选；正文或持续约束变化会使其失效。实施前核验参考代码并登记开始，实施后的正常代码修改由最终验收负责，不反复触发整套规划评审。助手不证明报告语义、评审身份或真实业务验证；JSON v1 与既有命令保持兼容。

## 接入已有项目

1. 比较目标项目与模板，将 AGENTS.md、.agents/ 和 openspec/ 中的规则、技能、配置及 fast-change schema 合并到原目录。
2. 保留已有 specs、changes、显式 schema、自定义元数据与用户修改，不整目录覆盖。
3. 保留共享目录相对结构；单独复制 SKILL.md 不构成完整安装。CLI 内置 spec-driven 无需复制。
4. 如新项目确需 CLI 初始化，在合并定制模板前完成；不要用 init/update --force 刷新真实模板中的定制技能。
5. 不复制本仓库 .gitignore 覆盖业务项目的忽略配置，也不分发 .codex/ 中的计划、演练项目、缓存和日志。

机器助手需要 Python 3.9+，业务项目不必采用 Python；没有运行时或布局不受支持时按人工核验规则处理。项目自身强制的机器门禁仍须满足。

## 模板验证

测试源码位于 `.agents/shared/openspec/scripts/test_*.py`，运行时样例及日志保存在本项目 `.codex/validation/`。标准库测试不依赖业务框架；CLI 集成测试需要已安装的 OpenSpec，并记录版本、命令、退出码与真实输出。本次验证目标版本为 1.14.3。

```bash
OPENSPEC_TELEMETRY=0 python3 -B -m unittest discover -s .agents/shared/openspec/scripts -p 'test_*.py' -v
git diff --check
```

CLI 不可用时集成测试会明确跳过，不能算作通过。七个技能还需用 skill-creator 的 quick_validate.py 检查结构，并在隔离项目演练实际行为；该校验器所需 PyYAML 放在隔离工具环境，不加入模板或业务运行依赖。
