# 规范同步、归档与恢复

在获准归档或恢复中断归档时读取。风险等级沿用 [元数据规则](workflow-policy.md#元数据读取与兼容)，核验方式沿用现有记录；manual 的清单细节见 [人工核验](manual-verification.md)。

## 正常完成归档

需要规范同步或导航更新的机器路径为：核对验收结论及授权 → 准备完整同步内容、确定导航范围 → prepare → 写入前 check → 更新登记目标 → synced → 移动前 check → 整体移动 → archived。恢复路径先核对现有检查点，仅执行剩余步骤；异常路径保留文件及证据并说明具体阻塞，不混入正常流程。

AI 负责需求合并语义、真实报告结论与授权。工具负责内容、哈希、目录状态及命令结果；prepare 内的验收检查不在外部重复执行，synced 前不额外补同等检查，archived 已自检最终落盘内容，成功后不再重复 cmp、shasum、check 或相同 CLI 命令。写入和移动前的 check 仍保留，不能用时间短或上轮成功代替当前边界核验。

标准 spec-driven 主规范用 `## Requirements`，自定义 schema 按其真实规则合并；规则或需求冲突尚未解决时不覆盖。machine 的 synced/archived 生成并更新 `reports/archive-record.md`，原规划和验收报告及 JSON 不改写。已获归档授权时连续执行，只有明确要求分段测试才在 prepared 等阶段暂停。

无增量规范明确记录“不需要同步”，先检查导航；如有必要地址更新或需保留历史链接映射，使用下述非空导航检查点，不虚构规格。两者均没有时不创建检查点：machine 执行 check-verify，manual 比较当前清单，记录原规划及验收记录的哈希和活动、目标路径，完成 CLI 支持的适用校验后整体移动。fast-change 的 `skip_specs: true` 仅豁免不存在的规格增量，仍需核验实际任务完成及验收；已有 fast 变更若实际包含增量规格，仍走同步路径。移动后核对源目录消失、目标存在、原记录字节未变化、登记范围的本地文件链接可达及活动列表不再包含变更，将真实结果补入归档记录，失败则说明“已移动，核验未完成”。有尚未同步的规范时不能跳过同步。归档不等于 Git 提交、合并或发布。

附带记录使用项目相对路径；移动变更后旧活跃路径不再适用。归档前校验原记录，并在归档记录中保存这一结果；不要移动后重新生成一个假装重新测试过的记录。

## 归档导航与原始证据

归档增加一层目录，既可能使 README 等入口指向旧活动路径，也可能使 sources 中指向项目规则的相对链接失效。移动前确定范围并计算最终地址，移动后从实际文件位置核对可访问性；不能只确认目录移动成功。

- 默认检查整个变更内的 Markdown 和根 README.md；先用 `rg --hidden -l -F '<变更名>' -g '*.md' -g '!.git/**' -g '!.codex/**' -g '!node_modules/**' -g '!openspec/changes/archive/**' .` 查找其他可能入口，核对后以可重复的 `--link-file <文件>` 加入同一次 links/prepare。检索结果只是候选，不盲目修改全部命中文档，也不批量重写已有历史归档。
- `links --root . --change <活动路径> --archive <最终路径>` 只读预检查，输出扫描文件、必要更新和需保留的历史链接；有待创建/删除的规范目标时同时传入 `--sync-plan`。prepare 使用相同范围自动登记导航前后原文和哈希，普通规划、来源及项目说明只允许修改因本次移动失效的链接地址，保留正文、标签、任务状态、查询/片段和可执行位。不要手工编造 expected。
- 原评审/验收报告、通过记录、验收清单和原始证据均保留原字节；其中需要重定位的 Markdown 链接不直接改写，而由 archive-record 的“归档导航”给出文件、行号和可访问目标，并明确历史链接仍保留。JSON 内路径继续按活动→归档前缀解释，不重写旧记录使其看起来重新通过。导航检查点保存被更新普通文档的完整原字节，供复核归档前依据。
- 助手支持常见内联链接、图片、引用定义、尖括号及转义/成对括号目标，按 UTF-8 处理；只校验根内相对文件/目录是否存在，不校验远程 URL、站点绝对路径和章节锚点。代码块、代码跨度及注释中的路径保留原意。HTML href/src、不受支持的语法、跨根或符号链接应明确报告并停止自动导航处理，不能跳过文件后宣称检查完整；已有 machine 基线不得通过改写 JSON 或临时切为 manual 绕过失败。
- 原来已失效或指向待删除规范的链接须先处理真实问题；只有已预登记的新规范可以在 prepare 时尚不存在。同步正式规范本身若需要导航调整，应纳入其完整 after 内容，不把同一文件同时登记为规范和导航目标。成功结论必须说明检查范围、已更新地址及受保护历史引用，不宣称所有旧链接已直接修复。

manual 采用相同边界：保存导航文件完整前后内容与哈希，逐项证明仅地址变化并核对实际目标，原报告和证据不动；不生成冒充机器的记录。首次选择方式仍按人工核验规则，不能因机器检查失败而降级。

### 同步检查点与中断恢复

machine 使用 `.agents/shared/openspec/scripts/archive_checkpoint.py`，记录格式仍为 `version: 1`。工具复用 evidence.py 文件快照语义，实际执行固定的只读 OpenSpec 校验；不执行目标写入、目录移动、迁移、提交或推送。保留 prepare、check、synced、archived 四个命令，增加只读 links 预检查；实际规范同步或导航更新才建立检查点。

先在 `.codex/<变更名>/` 准备合并后的完整 UTF-8 文件，再创建 JSON 同步计划，例如：

```json
{
  "targets": [
    {"path": "openspec/specs/example/spec.md", "after": ".codex/example-change/sync/example.md"},
    {"path": "openspec/specs/obsolete/spec.md", "after": null}
  ]
}
```

`path` 是正式规范文件，`after` 是已准备好的目标内容文件；新增和修改由目标现状判定，删除显式使用 null，重命名表示旧文件删除和新文件新增。这里只删除登记的文件，保留其空父目录。不能把没有完整内容的草稿登记为预期版本。只有导航更新时省略 --sync-plan，不能构造空 targets 数组。

```bash
python3 .agents/shared/openspec/scripts/archive_checkpoint.py prepare --root . --change openspec/changes/example-change --profile standard --mode machine --archive openspec/changes/archive/2026-01-01-example-change --sync-plan .codex/example-change/sync/plan.json
python3 .agents/shared/openspec/scripts/archive_checkpoint.py check --root . --change openspec/changes/example-change
# 按 pending_targets 写入 targets 或 navigation.targets 中对应的 expected 内容，然后：
python3 .agents/shared/openspec/scripts/archive_checkpoint.py synced --root . --change openspec/changes/example-change
python3 .agents/shared/openspec/scripts/archive_checkpoint.py check --root . --change openspec/changes/example-change
# 移动活动目录后，以归档目录作为 --change：
python3 .agents/shared/openspec/scripts/archive_checkpoint.py archived --root . --change openspec/changes/archive/2026-01-01-example-change
```

- prepare 核对当前验收基线，自动继承规划持续约束、评审报告、最终验收输入、清单引用的证据、原记录、整个变更、正式规范根及导航文件；参考代码在这里冻结的是验收后的状态，不与实施前内容比较。standard/strict 要求验收清单，fast 可不具备；结构助手不证明需求覆盖或测试语义，归档前仍须核对报告真实结论。
- 检查点原子写入 `reports/archive-checkpoint/journal.json`，包括活动和归档路径、等级、原记录 SHA-256、全部输入基线及逐个规范的前后内容；可选 navigation 保存扫描范围、普通文档前后内容、目标映射及受保护历史引用。UTF-8 原文以 Base64 无损存入 JSON，内容与哈希一并校验；不存在的规范文件显式登记 missing。该编码只用于无损保存，不是加密。
- prepared 阶段只接受旧状态或预登记新状态，check 返回规范及导航尚未更新的 pending_targets。写每个目标前先 check，仅写入该目标登记的完整 expected 内容，保持记录中的可执行位；已符合预期的目标不重复操作。导航地址按最终归档位置计算，写入后到移动前可能暂不可点击，故获准后连续完成；中断后按原检查点恢复，不能根据当前文件重新定义 expected。
- synced 和 archived 阶段都要求登记目标的内容及可执行位等于预期。synced 将最终链接目标映射回尚未移动的实际文件核对，archived 按归档后的实际文件核对。检查中重新枚举其他输入；代码、规划、任务、报告、原始证据的额外变化、缺失和新增文件均拒绝。只排除工具管理的检查点目录和 archive-record.md；不要手工往这两个位置写其他资料。
- synced 实际执行 `openspec context --json` 核对 CLI 根；有规范同步时执行 `openspec validate --specs --strict --no-interactive`，仅导航时校验当前活动变更。archived 执行归档严格校验及 `openspec list --json`，有规范同步时仍核对正式规范，确认活动变更消失。命令、工作目录、退出码、时间、stdout/stderr 保存在 commands，不接受手填通过结果。校验前后核对基线，落盘后读取并复核检查点、命令与最终报告；任一步失败都不能返回成功。
- 已同步阶段可重试 synced；已移动且阶段为 synced/archived 时可重试 archived。原目录必须不存在，当前路径必须是登记的归档路径；源目标并存时停止。失败或中断后，check 不复用之前的成功结论；重试对应命令重新校验。归档报告丢失或状态过期时同样通过重试生成，原验收报告与 JSON 不改写。
- 完成阶段必须包含对应的成功校验尝试、完整命令记录及相符的校验结果；仅有 synced/archived 状态文字不能通过 check。

归档报告由工具根据阶段生成，包含 active_change_path、archived_change_path、原规划/验收记录哈希、检查点引用和最终状态。归档后旧活动路径保留历史含义，工具读取时只映射该前缀，不生成新的验收通过记录。

不含 navigation 的旧 v1 检查点继续按原范围与原报告格式核验，不自动补字段、改 expected 或改写旧报告。旧检查点未登记的导航问题应明确报告，另行维护时建立真实依据，不能声称旧记录已证明新导航有效。

适用范围：单根普通文件、现有 evidence.py 机器记录，以及支持 context、规范/归档 validate、list JSON 的 CLI。正式规范根不同可用已核实的 `--spec-root`；不能用该参数绕过实际 schema 的同步语义。校验覆盖当前根全部正式规范及归档，其他既有无效规范也会阻止通过，需报告具体原因。不支持并发归档同一变更；执行期间不要同时修改相关文件。指纹不是防篡改签名，也不覆盖运行环境动态状态。

manual 不调用本机器工具。无运行时、多根、链接或不支持的 CLI 布局按人工核验清单记录相同的阶段、原记录哈希、前后内容、非同步输入及真实校验结果；不能生成冒充 machine 的 JSON，也不能用 manual 绕过已有机器校验失败。

恢复时正式规范或普通文档导航的预期变化可能导致普通 `check-verify` 报告来源失效。这时按上述逐项比较记录“归档恢复核验通过”，保留原记录，不伪称 `check-verify` 通过、不重写规划 PASS，也不为消除指纹差异机械重跑业务验收。只有预先登记的变化可走此路径，其他变化仍需重新评估。

## 取消或放弃

仅在用户明确要求取消、放弃或替代该变更时使用。记录原因、已实现与未完成内容、残留代码/环境状态以及后续责任，不同步未完成增量为正式规范。以 `Cancelled` 或 `Superseded` 标记，归档保留历史，不宣称完成验收。残留代码的删除或回滚需要符合用户授权，不能因取消规划就自动清理。
