# 规划评审与实施基线

## 评审对象

检查当前规划是否支撑实施，不要求此时已有业务测试结果。已确认的产品选择无需重新确认；矛盾或实质性新风险只重议受影响项。由 CLI 依赖图确定必需产物及传递依赖，文件存在与格式正确不代表内容正确。

| 检查面 | 核对内容 |
| --- | --- |
| 范围与价值 | 问题、范围、非目标及可独立交付性 |
| 来源 | 按 [sources.md](sources.md) 检查采纳关系、正向覆盖和反向追踪 |
| 可观察行为 | 成功、失败、边界及兼容行为能否验证 |
| 技术决策 | 接口、数据、状态、依赖、取舍及恢复策略是否足够明确 |
| 执行清单 | 依赖、落点、具体验证，必要迁移或兼容任务；排除验收循环前置任务 |
| 风险 | 适用的权限、隔离、并发、事务、迁移、回退及外部影响 |

fast 核对低风险资格、范围、来源及聚焦验证；新建 fast-change 只要求 proposal/tasks，已有变更仍按实际 schema。standard 做一次聚合评审；strict 覆盖全部声明的高风险边界，并由未撰写该规划的独立评审者直接形成主报告。

## 主报告格式

正式主报告固定为 `reviews/change-review.md`。standard/strict 使用以下结构；来源较少可缩短表格，但保留 `Change Source Coverage 检查结果` 小节：

```markdown
# Change Review: <变更名>

- 评审日期：实际日期
- Profile：fast / standard / strict
- Source Coverage：Pass / Warn / Block / N/A，并给出原因
- Pre-Apply Decision：PASS / PAUSE / BLOCK
- Validation Confidence：说明依据是否完整、执行过哪些校验及其局限
- 评审者与独立性：真实人员或执行上下文，普通自查如实注明
- 核验方式：machine / manual
- 机器记录：reviews/planning-review.json（仅真实 PASS 且已记录时生效）

## 评审范围与依据

实际 schema、规划文件、来源及适用工程规则；区分持续约束和允许修改的实现参考。
注明本次检查范围、复用依据和未检查部分，不复制整份材料。

## Blocking findings

按根因记录：编号、位置、问题、影响、修正条件及状态。无则写无。
已关闭的问题保留必要关闭依据，不保留无关逐轮流水。

## Warnings

区分需要决定的实质性警告和不阻塞实施的建议，写清处置依据。

## Change Source Coverage 检查结果

说明检查范围、有效来源、部分替代关系及不采纳依据。

| 来源／有效要求 | proposal | specs | design | tasks | 结论与缺口 |
| --- | --- | --- | --- | --- | --- |
| 实际来源编号及要求 | 章节 | Requirement / Scenario | 决策章节 | 任务编号 | 覆盖或具体遗漏 |

按实际 schema 调整列；不适用项写明原因。
反向追踪：规划中的实质性行为与技术任务是否有来源或必要性依据。
跨产物一致性：是否存在遗漏、擅自增加要求或已被替代要求残留。

## Apply handoff

实施范围、任务依赖与待处理领域；必需验证、环境前提及剩余条件。
给出下一阶段可做事项和仍需决定的内容，不把规划通过写成实现通过。
```

fast 可写成短段落或短表，保留等级及理由、来源覆盖、实施结论、验证依据及局限、评审者、核验方式和交接条件的语义，不强制完整长表。来源已有记录时直接引用。

Source Coverage 的 Pass 表示有效要求覆盖且反向追踪成立；Warn 表示已说明的不阻塞缺口；Block 表示核心遗漏或冲突。N/A 仅用于确实不适用的检查项并说明原因，不能因没有 PRD 或 sources 目录而使用。Pre-Apply Decision 独立判断：PASS 可交给实施；PAUSE 有需解决或明确接受的实质性警告；BLOCK 有必须修正的核心行为、安全或验收缺口，不能靠接受风险跳过。接受警告后保留依据、更新报告并核验，才能记录 PASS。

## 复审与辅助报告

- 同一范围复审更新同一主报告，不默认另建 current、v2、final 或逐轮文件；主报告反映当前结论，不逐任务追加实施流水。
- strict 的独立评审者直接交付 `change-review.md`。主执行者可保存和整理排版，不擅自改变结论或隐去发现；结论修订由独立评审者复核受影响内容。无需默认再复制独立规划报告。
- 来源检查默认在主报告完成。已有独立来源报告，或确需保存单独详细材料时，可引用 `change-source-review.md`；确有独立专题时用 `<专题>-planning-review.md`，同专题复审更新固定文件。
- 既有有效独立报告按原记录引用，不因新约定删除、重命名或自动转换历史缓存。
- 独立代码质量评审是实施阶段的 `reviews/implementation-review.md`；最终验收是 `reports/verification.md`，职责及生成时机见 [验收规则](verification-evidence.md#独立代码质量评审)。
- 主报告及采用的辅助材料全部定稿后再记录指纹。报告只引用机器记录路径，不把计算出的自身指纹回写报告，否则新记录会立即失效。

## 规划指纹

按用途登记实际输入：`--plan` 为实际规划文件及规格目录，任务与 `.openspec.yaml` 由助手同时纳入；`--source` 为已确认来源和持续约束；`--reference` 为允许按任务修改的实现、测试与配置。没有现有实现可以不传 reference；目录快照发现增删，两类范围不能重叠。来源的分类与采纳只在 [sources.md](sources.md) 定义。

任务 checkbox 的 `[ ]` / `[x]` / `[X]` 仅在规划指纹中归一化；正文、验收标准及其他持续约束变化使基线失效。验收阶段按任务原文检查。

按 [核验方式](manual-verification.md#核验方式) 选择 machine 或 manual。machine 使用 [evidence.py](scripts/evidence.py)，示例名称与路径替换成实际存在的输入：

```bash
python3 .agents/shared/openspec/scripts/evidence.py record-plan --root . --change openspec/changes/example-change --profile standard --tasks openspec/changes/example-change/tasks.md --plan openspec/changes/example-change/proposal.md --plan openspec/changes/example-change/specs --plan openspec/changes/example-change/design.md --source openspec/changes/example-change/sources --source AGENTS.md --reference src/changed-module --report openspec/changes/example-change/reviews/change-review.md
python3 .agents/shared/openspec/scripts/evidence.py check-plan --root . --change openspec/changes/example-change --profile standard
# 已获实施授权且具备可推进任务，在首次修改前：
python3 .agents/shared/openspec/scripts/evidence.py start-apply --root . --change openspec/changes/example-change --profile standard
```

fast-change 仅传 proposal 和实际 tasks，不制造空 specs/design。strict 的 `--report` 与 `--independent` 默认都指向真实独立评审者交付的 `reviews/change-review.md`，助手按路径去重。已有独立报告可以继续传其原位置。

被正式结论采用的辅助报告通过可重复 `--review-evidence <路径>` 绑定，进入现有 `reports/report_snapshot`；不传则保留旧行为。路径须为根内非空普通文件、无符号链接，重复路径只记录一次。不要登记整个 reviews 目录或把输出 JSON 作为输入。任一采用的辅助报告变化都使对应规划记录失效；不采用的材料无需凑数登记。

仅真实 PASS 后运行 record-plan，然后 check-plan；其他结论保存在报告，不生成新的通过记录。manual 按共享步骤保存并比较人工清单，不生成冒充机器结果的 JSON。`version: 1` 不变，不自动转换其他项目的旧缓存。

规划 JSON 保存 reference_inputs、reference_snapshot、implementation_started。开始前 check-plan/start-apply 同时比较规划、报告及参考代码；start-apply 成功后原子登记时间，不改评审正文。开始后只持续检查规划与报告，正常实现修改交给验收；重复 start-apply 不刷新参考快照或时间。规划实质变化时实际复评、重新登记，之后再次核对实施入口。不要并发操作同一变更。

助手证明文件基线新鲜度，不证明评审身份、报告语义或真实业务验证；不能只保存一个 PASS 指纹来替代评审。
