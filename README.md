# OpenSpec Workflow Template

面向中文协作的通用 OpenSpec 流程模板，将用户需求、规划、评审、实施证据和归档连接起来。技术栈、工程命令和环境以接入项目的实际约定为准。

模板提供 7 个阶段技能、共享流程规则、`fast-change` 轻量 schema，以及基于 Python 标准库的证据和归档工具。

## 快速开始

首次使用先按 [接入已有项目](#接入已有项目) 合并模板，再在目标项目的聊天中选择技能。将下列 `<需求>`、`<问题>` 替换为实际描述，`<变更名>` 替换为已有变更的名称。

| 目的 | 聊天示例 |
| --- | --- |
| 调查现状、讨论方案 | `$openspec-explore <问题>` |
| 逐步形成规划 | `$openspec-new-change <需求>`；骨架创建后用 `$openspec-continue-change <变更名>` 生成下一份规划 |
| 一次完成规划和评审 | `$openspec-new-change <需求>，请完成全部规划并评审。` |
| 完成实施和验收 | `$openspec-apply-change <变更名>，请完成实施和验收。` |
| 归档已通过验收的变更 | `$openspec-archive-change <变更名>` |

以上是独立使用场景。聊天中的 `$openspec-<名称>` 是技能入口，终端执行的是 `openspec ...` CLI 命令。首次使用核对目标项目中的实际技能文件，避免误用其他项目的同名技能。

## 入口与使用顺序

| 当前阶段 | 技能 | 本阶段产物及停止位置 |
| --- | --- | --- |
| 随时调查问题、讨论方案（可选） | [openspec-explore](.agents/skills/openspec-explore/SKILL.md) | 理解、候选方案或未决问题，无强制产物；获准时保存探索笔记或交接规划 |
| 创建变更 | [openspec-new-change](.agents/skills/openspec-new-change/SKILL.md) | 骨架、等级元数据；standard/strict 保存必要用户来源，尚无 proposal |
| 继续规划 | [openspec-continue-change](.agents/skills/openspec-continue-change/SKILL.md) | 默认下一份就绪产物；“完成全部规划”才连续生成 |
| 规划评审 | [openspec-review-change](.agents/skills/openspec-review-change/SKILL.md) | reviews/change-review.md；真实 PASS 后登记规划基线 |
| 实施 | [openspec-apply-change](.agents/skills/openspec-apply-change/SKILL.md) | 当前任务的实现、验证及证据，及时更新任务状态 |
| 实现验收 | [openspec-verify-change](.agents/skills/openspec-verify-change/SKILL.md) | reports/verification.md；满足条件才记录验收通过 |
| 同步规范、归档 | [openspec-archive-change](.agents/skills/openspec-archive-change/SKILL.md) | reports/archive-record.md；有规范同步或必要导航更新时使用归档检查点 |

按阶段及已有授权推进；规划齐备不自动授权评审或编码，完整实施授权涵盖必要实现与验收，不包含提交、推送、发布或归档。

explore 可以在变更前或变更过程中使用，不要求每次都形成方案或进入规划。[官方定位](https://github.com/Fission-AI/OpenSpec/blob/main/docs/explore.md)允许在明确授权后保存指定规划产物；本模板由 new-change／continue-change 承接这类写入，复用风险、来源和 schema 规则，已有授权无需重复确认。官方流程及可选入口见 [Workflows](https://github.com/Fission-AI/OpenSpec/blob/main/docs/workflows.md)。

## 风险等级与 Schema

| 等级 | 适用范围 | 新建时的规划 |
| --- | --- | --- |
| fast | 不改变规范约定的低风险修复、行为保持重构、文案或工具调整 | fast-change：proposal → tasks |
| standard | 普通功能或业务行为调整 | spec-driven：proposal、specs、design、tasks，按 CLI 依赖生成 |
| strict | 权限、隔离、持久化迁移、破坏性契约等高风险边界 | 完整四件套，加独立规划评审、独立代码质量评审及适用真实环境验证 |

根配置默认 spec-driven。new-change 显式选择 schema；fast-change 必须声明 `skip_specs: true`，表示没有规范级行为变化，不是通用跳过开关。已有变更按实际 schema，不因标记 fast 删除其他产物；风险升级时在同一变更补齐规划并复评。

新等级使用 `x-workflow_profile`。旧 `workflow_profile` 兼容读取；并存冲突停止推进，缺失按实际范围登记。规范化旧字段需已有修改授权；不批量改写历史或修改 JSON 假装旧指纹有效。完整定义见 [工作流规则](.agents/shared/openspec/workflow-policy.md)。

## 模板目录

```text
.
├── README.md                         # 使用和接入说明
├── AGENTS.md                         # 项目协作与模板维护规则
├── .gitignore                        # 模板仓库专用的分发范围
├── .agents/
│   ├── skills/                       # 7 个阶段技能
│   └── shared/openspec/
│       ├── *.md                      # 风险、来源、评审、验收和归档规则
│       └── scripts/                  # 4 个工具模块、5 个测试文件
├── openspec/
│   ├── config.yaml                   # 默认 spec-driven 及中文产物规则
│   ├── schemas/fast-change/          # 轻量 schema 与 proposal/tasks 模板
│   ├── specs/                        # 正式规范
│   └── changes/                      # 活动变更及归档
└── .codex/                           # 本地计划、演练、日志和缓存，不分发
```

模板仓库中的 `openspec/specs/` 和 `openspec/changes/` 初始仅保留 `.gitkeep`，实际需求与规范在接入项目后按需创建。本地维护产生的 `.codex/` 被忽略，取得模板副本后不一定存在。

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
    └── archive-checkpoint/journal.json # 有规范同步或导航更新的机器归档
```

JSON 指纹适用于 machine；manual 使用明确标注的人工输入清单，不伪造机器记录。正常归档后整个变更移动到 `openspec/changes/archive/YYYY-MM-DD-<变更名>/`，保留原评审、验收报告与记录字节，正式规范合并到 `openspec/specs/`。README、来源等普通文档的必要链接地址更新纳入检查点；受保护历史文件中的旧链接由归档记录提供当前入口，具体范围见 [归档导航规则](.agents/shared/openspec/archive-workflow.md#归档导航与原始证据)。

新建 fast 默认只有 proposal/tasks 两份规划，简单来源保存在 proposal 的 Source Inputs，仍分别保存规划评审和实现验收两份短报告；不创建空 specs、design，也不默认增加独立专题评审报告。无规范增量且无导航更新时不创建归档检查点；仅有导航更新时使用导航检查点，无需补造规格增量。已有 fast 变更若实际包含增量规格，仍按实际内容同步。

tasks 正文描述任务、依赖和完成条件，状态由 checkbox 和证据表达，当前阶段及下一步提示放在会话回复中。

`sources/` 保存真实需求和补充决定；主报告的 “Change Source Coverage 检查结果” 检查这些有效要求如何进入规划，同时反查是否增加了未经确认的要求。没有 sources 目录仍须检查对话来源。

standard/strict 固定使用 [主报告格式](.agents/shared/openspec/review-checklist.md#主报告格式)。同范围复审更新同一 change-review.md，来源检查默认并入主报告；strict 独立评审直接交付该文件。已有辅助报告可沿用原路径，通过可重复的 `--review-evidence` 绑定，不默认复制评审文件。

## 共享规则与脚本

| 路径（位于 .agents/shared/openspec/） | 职责 |
| --- | --- |
| [workflow-policy.md](.agents/shared/openspec/workflow-policy.md) | 风险、元数据、授权与阶段转换 |
| [project-context.md](.agents/shared/openspec/project-context.md) | 项目事实、工程入口及读取边界 |
| [sources.md](.agents/shared/openspec/sources.md) | 来源保存、编号、采纳与替代关系 |
| [review-checklist.md](.agents/shared/openspec/review-checklist.md) | 规划评审、主报告、辅助报告及规划基线 |
| [verification-evidence.md](.agents/shared/openspec/verification-evidence.md) | 实施证据、验收映射、独立代码评审及验收记录 |
| [manual-verification.md](.agents/shared/openspec/manual-verification.md) | 核验模式选择及人工、多根、链接处理 |
| [archive-workflow.md](.agents/shared/openspec/archive-workflow.md) | 规范同步、归档检查点、恢复和取消 |
| [scripts/evidence.py](.agents/shared/openspec/scripts/evidence.py) | 文件基线、任务状态及辅助报告绑定 |
| [scripts/evidence_manifest.py](.agents/shared/openspec/scripts/evidence_manifest.py) | 已登记验收条目的结构与引用检查 |
| [scripts/archive_checkpoint.py](.agents/shared/openspec/scripts/archive_checkpoint.py) | 规范与导航更新基线、真实 CLI 核验与归档恢复 |
| [scripts/archive_links.py](.agents/shared/openspec/scripts/archive_links.py) | 常见 Markdown 相对文件链接的识别与归档地址计算 |

规划指纹归一化任务勾选；正文或持续约束变化会使其失效。实施前核验参考代码并登记开始，实施后的正常代码修改由最终验收负责，不反复触发整套规划评审。助手不证明报告语义、评审身份或真实业务验证；JSON v1 与既有命令保持兼容。

## 接入已有项目

1. 比较目标项目与模板，将 AGENTS.md、.agents/ 和 openspec/ 中的规则、技能、配置及 fast-change schema 合并到原目录。
2. 保留已有 specs、changes、显式 schema、自定义元数据与用户修改，不整目录覆盖。
3. 保留共享目录相对结构；单独复制 SKILL.md 不构成完整安装。CLI 内置 spec-driven 无需复制。
4. 如新项目确需 CLI 初始化，在合并定制模板前完成；不要用 init/update --force 刷新真实模板中的定制技能。
5. 不复制本仓库 .gitignore 覆盖业务项目的忽略配置，也不分发 .codex/ 中的计划、演练项目、缓存和日志。

机器核验需要 Python 3.9+，适用于同一授权根内的普通文件和非空 UTF-8 Markdown checkbox 任务清单，输入不能包含符号链接。业务项目不必采用 Python；运行时不可用，或采用多根目录、符号链接及其他任务格式时，按 [核验方式](.agents/shared/openspec/manual-verification.md#核验方式) 选择适配路径。项目自身强制的机器门禁仍须满足，不能通过切换为人工核验绕过已有机器检查失败。

## 模板验证

测试源码位于 `.agents/shared/openspec/scripts/test_*.py`，覆盖证据基线、验收清单、归档链接、检查点恢复和真实 CLI 流程。运行时样例及日志保存在本项目 `.codex/validation/`。

本地维护记录包含以下两轮回归：

| 验证范围 | 当次结果 | 原始日志（不随模板分发） |
| --- | --- | --- |
| 模板重构回归 | 61 项通过 | `.codex/validation/logs/regression.txt` |
| 归档导航补充回归 | 84 项通过 | `.codex/validation/logs/archive-navigation-regression.log` |

表中数量分别为各轮运行的总数。这些是历史结果；`.codex/validation/summary.md` 记载的是前一轮 61 项回归。已有验证记录使用 OpenSpec CLI 1.14.3，当前通过数、失败数和跳过项以重新运行的实际输出为准。

在模板根目录执行：

```bash
OPENSPEC_TELEMETRY=0 python3 -B -m unittest discover -s .agents/shared/openspec/scripts -p 'test_*.py' -v
git diff --check
```

标准库测试不依赖业务框架；CLI 集成测试需要已安装的 OpenSpec，CLI 不可用时会明确跳过，不能算作通过。运行验证时记录实际版本、命令、退出码与真实输出。

七个技能还需用 skill-creator 的 quick_validate.py 检查结构，并在隔离项目演练实际行为；该校验器所需 PyYAML 放在隔离工具环境，不加入模板或业务运行依赖。
