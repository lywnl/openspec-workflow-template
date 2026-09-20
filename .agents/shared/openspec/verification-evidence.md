# 实现验收与证据

## 证据原则

任务完成必须对应真实实现与适用验证。单元测试可使用替身；真实数据库、HTTP、模型、上传或运行环境的必需验收不能用 mock、skip、仅收集测试或旧版本报告代替。

每份运行证据记录命令、工作目录、退出码、时间、代码状态、测试范围及相关环境标识。代码状态覆盖相关已提交、未提交和未跟踪文件，不只写 Git HEAD。敏感环境仅记录脱敏标识和必要配置摘要，禁止把凭据写入报告。

原始日志、JUnit 和截图保存在项目 `.codex/<变更名>/`；正式索引保存在变更的 `reports/`。仍被验收或归档记录引用的原始证据不能作为普通临时文件清理，缺失不能视为有效。归档不表示证据已纳入 Git，克隆后也不必然可复核；需要跨机器交付时先明确证据保存与授权范围，不擅自移动文件或改写原记录。

## 核验方式

在首次规划评审时选择并在报告中登记 `machine` 或 `manual`，后续 review、apply、verify、archive 沿用同一规则：

- machine：Python 3.9+，输入位于同一授权根内且无符号链接；任务为非空 UTF-8 Markdown checkbox 清单。内置 spec-driven 使用该任务格式，其他 schema 必须先核对实际格式，不能仅凭名称判断兼容。
- manual：运行时不可用，或项目采用多根目录、符号链接、非 Markdown 任务等不受助手支持的结构时，执行下列人工步骤。无需为使用模板额外安装 Python、改造目录或制造一份假任务清单。
- 项目明确要求机器门禁时，manual 不能替代它；需补足运行时或经项目认可的适配工具。机器校验因内容变化、证据缺失或读取失败而报错时，先处理原因，不能切换模式绕过失败。

人工核验步骤：

1. 列出授权根及稳定代号、相关输入目录、排除项与理由。使用项目可用的文件遍历和 SHA-256 工具，逐根生成排序清单，登记 `根代号 + 相对路径 + 文件类型 + 内容哈希 + 可执行位`；目录也登记，以便重新枚举时发现新增、删除。Git 状态只能辅助发现范围，不能替代未跟踪文件的清单。
2. 对符号链接登记链接文本与解析目标；目标在授权范围内才读取，并纳入目标内容清单。检测循环、失效链接和重复目标，不静默跳过。目标未获授权时保留阻塞；业务依赖 ACL、扩展属性等时另外登记并验证这些属性。
3. 规划清单分别登记 metadata、实际规划、持续约束及报告，以及允许实施修改的参考代码。首次获准实施前比较两类清单，在现有规划记录内注明实施开始；之后持续约束仍须匹配，参考代码的正常修改交给当前验收。只有任务完成字段可按 schema 语义归一化。JSON/YAML 用相应解析器；非 checkbox 任务按真实完成条件核验，不适用项不能当作已完成。
4. 人工文件指纹分别保存为 `reviews/planning-inputs.md`、`reports/verification-inputs.md`，或项目已有的等价格式，并明确标注 manual。验收指纹额外覆盖规划清单与报告、原始任务状态、实现、测试、相关依赖配置、需求映射、原始证据和独立评审。`reports/verification-manifest.json` 专用于下文结构化需求映射，不能拿文件哈希清单覆盖它；standard/strict 在 manual 下也须维护需求映射。生成指纹时排除自身及其输出临时文件，不能排除业务输入；清单按当前文件实际生成，不手填猜测哈希。
5. 复用及交接时按当前阶段重新枚举适用范围并比较：实施开始前包含参考代码，开始后规划仅比较持续约束，验收及归档比较最终实现和证据。核对任务、环境及报告结论，记录执行者、时间、工具、差异、范围限制和 manual；不同根由总索引关联，不以复制件代替原始根核验。

人工核验无需执行 `record-plan/check-plan/record-verify/check-verify`，不得生成冒充助手结果的 JSON。核验模式变化须记录原因并重新建立对应清单，strict 的独立评审与必需真实验收要求不变。

## 验收范围

- fast：检查任务证据、改动范围、聚焦测试、静态检查及风险等级是否仍成立。
- standard：将每项必需需求与场景对应到实现和测试；检查失败路径、兼容性、设计约定及相关工程门禁。
- strict：在上述基础上核验全部声明的权限、租户、持久化、迁移、回退、事务、公共契约及跨域边界；取得当前实现的独立代码质量评审。
- 纯文档、配置或非代码任务使用相应的结构、内容或实际加载验证，不为凑测试数编写无意义测试。
- 测试命令来自项目事实，不固定某个框架。静态检查无法证明真实运行成功。

必要验证受环境或授权阻塞时，写 `ENVIRONMENT_NOTE`，保留任务未完成。区分环境问题、共享基线失败和本次实现缺陷；环境问题不能被改名为通过。

## 验收报告

`reports/verification.md` 至少写明：

1. 风险等级、规划基线和当前代码/配置范围。
2. 引用结构化清单中的需求/场景/任务 → 实现 → 测试 → 本次证据映射；无结构化清单的 fast 在报告内用短表记录，不重复维护两份同内容映射。
3. 实际执行的命令与结果，以及失败、未运行、跳过项。
4. 独立评审结果、阻塞处置、剩余限制和交付/回退要求。
5. 结论：`Ready for Archive`、`Needs Work` 或 `Not Ready`。

fast 用短格式即可：一行等级与基线、任务到实现和真实证据的对应表、一行结论与剩余限制。命令详情可引用已保留的原始日志，不重复复制。没有独立评审要求时如实注明普通自查，不创建空独立评审报告。

只有必需行为、任务和验证全部满足，且不存在未解决阻塞，才能给出 `Ready for Archive`。非阻塞建议可以保留；不得把“几乎完成”作为正常完成归档的通过状态。

## 验收指纹与助手

### 结构化验收清单

除了文件指纹，standard/strict 必须保存 `reports/verification-manifest.json`；fast 可选同样格式，或仅在短报告内维护映射，项目额外机器门禁仍须满足。这是详细映射的统一维护位置，可在 apply 中逐步整理；未完成内容不能标为 verified。每个必需需求、场景及任务用稳定名称/编号关联实现、测试和证据，报告引用清单，不重复抄写。

machine 有清单时使用 `.agents/shared/openspec/scripts/evidence_manifest.py` 检查已登记条目的唯一 `id`、`implementation`、`tests`、`evidence`、`status: verified`，以及命令的 command、根内 cwd、整数 exit_code（不接受布尔值）和原始 evidence。manual 人工核对同样内容；多根引用使用已登记根代号并按授权逐根核实，不强行交给单根助手。`tests` 保存存在的文件或目录路径，具体测试节点通过命令及原始证据定位，不能把 `文件::节点` 当成文件路径传入。助手只校验已登记条目的结构、路径和字段，不自动发现整条需求遗漏，不解释日志或截图语义；verify 必须核对完整覆盖和真实结论，说明故障注入、替身及模拟环境。非零退出码如实保留，由报告说明是预期故障验证还是未解决失败；结构合法不代表验收通过。

```bash
python3 .agents/shared/openspec/scripts/evidence_manifest.py --root . --manifest openspec/changes/example-change/reports/verification-manifest.json
```

验收记录绑定：有效规划记录、任务原始内容、实现及测试文件、依赖/构建/相关配置、验收报告、原始证据和独立评审。输入中任一项改变，都需重评对应验证，并重新形成当前基线的报告。

machine 使用 [scripts/evidence.py](scripts/evidence.py) 的 `record-verify` / `check-verify`，要求规划中已有 implementation_started；没有开始记录时不能在验收阶段补记来冒充已完成的实施入口核验，应说明缺口并回到真实交接。`--code` 应覆盖 reference 登记的实现、测试及配置，并纳入实际新增模块、依赖清单和锁文件；工具检查范围包含关系，删除文件应登记其仍存在的所属目录。目录快照发现新增/删除，但改动是否符合任务仍须语义检查。manual 执行上文等价步骤；不要扩大到用户目录或不相关证据范围。

```bash
python3 .agents/shared/openspec/scripts/evidence.py record-verify --root . --change openspec/changes/example-change --profile standard --code src/changed-module --code tests/changed-module --evidence .codex/example-change/test-results.xml --report openspec/changes/example-change/reports/verification.md
python3 .agents/shared/openspec/scripts/evidence.py check-verify --root . --change openspec/changes/example-change --profile standard
```

路径是示例，使用实际项目入口。strict 额外传 `--independent` 指向当前实现的独立评审报告；非代码任务可以用 `--code` 指定实际修改的文档/配置。

助手会检查文件新鲜度、必需参数和任务勾选，不执行测试、不判断测试语义、不自动证明评审独立，也不是不可伪造的签名系统。记录前必须人工/代理核实声明成立，不能借调用 record 命令制造“已验收”。

记录采用 `version: 1` 格式，保存文件类型、SHA-256 与可执行位，目录不可读取时直接失败。助手忽略目录 `.git`、`__pycache__`、`.venv`、`node_modules`，不覆盖 ACL、扩展属性及运行环境动态状态；影响交付时另补针对性验证。复用测试须核对相关输入及环境前提，不能只看时间或命令相同。

## 正常完成归档

正常机器路径固定为：核对验收结论及授权 → 准备完整同步内容 → prepare → 写入前 check → 同步 → synced → 移动前 check → 整体移动 → archived。恢复路径先核对现有检查点，仅执行剩余步骤；异常路径保留文件及证据并说明具体阻塞，不混入正常流程。

AI 负责需求合并语义、真实报告结论与授权。工具负责内容、哈希、目录状态及命令结果；prepare 内的验收检查不在外部重复执行，synced 前不额外补同等检查，archived 已自检最终落盘内容，成功后不再重复 cmp、shasum、check 或相同 CLI 命令。写入和移动前的 check 仍保留，不能用时间短或上轮成功代替当前边界核验。

标准 spec-driven 主规范用 `## Requirements`，自定义 schema 按其真实规则合并；规则或需求冲突尚未解决时不覆盖。machine 的 synced/archived 生成并更新 `reports/archive-record.md`，原规划和验收报告及 JSON 不改写。已获归档授权时连续执行，只有明确要求分段测试才在 prepared 等阶段暂停。

无增量规范明确记录“不需要同步”，不创建空检查点；machine 执行 check-verify，manual 比较当前清单，记录原规划及验收记录的哈希和活动、目标路径，完成 CLI 支持的适用校验后整体移动。移动后核对源目录消失、目标存在、原记录字节未变化及活动列表不再包含变更，将真实结果补入归档记录，失败则说明“已移动，核验未完成”。有尚未同步的规范时不能跳过同步。归档不等于 Git 提交、合并或发布。

附带记录使用项目相对路径；移动变更后旧活跃路径不再适用。归档前校验原记录，并在归档记录中保存这一结果；不要移动后重新生成一个假装重新测试过的记录。

### 同步检查点与中断恢复

machine 使用 `.agents/shared/openspec/scripts/archive_checkpoint.py`，记录格式为 `version: 1`。工具复用 evidence.py 文件快照语义，实际执行固定的只读 OpenSpec 校验；不执行规范写入、目录移动、迁移、提交或推送。四个命令为 prepare、check、synced、archived；仅在实际同步规范时建立检查点。

先在 `.codex/<变更名>/` 准备合并后的完整 UTF-8 文件，再创建 JSON 同步计划，例如：

```json
{
  "targets": [
    {"path": "openspec/specs/example/spec.md", "after": ".codex/example-change/sync/example.md"},
    {"path": "openspec/specs/obsolete/spec.md", "after": null}
  ]
}
```

`path` 是正式规范文件，`after` 是已准备好的目标内容文件；新增和修改由目标现状判定，删除显式使用 null，重命名表示旧文件删除和新文件新增。这里只删除登记的文件，保留其空父目录。不能把没有完整内容的草稿登记为预期版本。

```bash
python3 .agents/shared/openspec/scripts/archive_checkpoint.py prepare --root . --change openspec/changes/example-change --profile standard --mode machine --archive openspec/changes/archive/2026-01-01-example-change --sync-plan .codex/example-change/sync/plan.json
python3 .agents/shared/openspec/scripts/archive_checkpoint.py check --root . --change openspec/changes/example-change
# 按 pending_targets 写入预登记内容，然后：
python3 .agents/shared/openspec/scripts/archive_checkpoint.py synced --root . --change openspec/changes/example-change
python3 .agents/shared/openspec/scripts/archive_checkpoint.py check --root . --change openspec/changes/example-change
# 移动活动目录后，以归档目录作为 --change：
python3 .agents/shared/openspec/scripts/archive_checkpoint.py archived --root . --change openspec/changes/archive/2026-01-01-example-change
```

- prepare 核对当前验收基线，自动继承规划持续约束、评审报告、最终验收输入、清单引用的证据、原记录、整个变更和正式规范根；参考代码在这里冻结的是验收后的状态，不与实施前内容比较。standard/strict 要求验收清单，fast 可不具备；结构助手不证明需求覆盖或测试语义，归档前仍须核对报告真实结论。
- 检查点原子写入 `reports/archive-checkpoint/journal.json`，包括活动和归档路径、等级、原记录 SHA-256、全部输入基线及逐个规范的前后内容。UTF-8 原文以 Base64 无损存入 JSON，内容与哈希一并校验；不存在的文件显式登记 missing。该编码只用于无损保存，不是加密。
- prepared 阶段只接受旧状态或预登记新状态，check 返回尚未同步的 pending_targets。写每个目标前先 check，已符合预期的目标不重复操作；同步中断后可以按原检查点继续，不能根据当前文件重新定义 expected。
- synced 和 archived 阶段都要求规范内容及可执行位等于预期。检查中重新枚举非同步输入；代码、规划、任务、报告、原始证据的额外变化、缺失和新增文件均拒绝。只排除工具管理的检查点目录和 archive-record.md；不要手工往这两个位置写其他资料。
- synced 实际执行 `openspec context --json` 核对 CLI 根，再执行 `openspec validate --specs --strict --no-interactive`。archived 还执行归档严格校验及 `openspec list --json`，确认活动变更消失。命令、工作目录、退出码、时间、stdout/stderr 保存在 commands，不接受手填通过结果。校验前后核对基线，落盘后读取并复核检查点、命令与最终报告；任一步失败都不能返回成功。
- 已同步阶段可重试 synced；已移动且阶段为 synced/archived 时可重试 archived。原目录必须不存在，当前路径必须是登记的归档路径；源目标并存时停止。失败或中断后，check 不复用之前的成功结论；重试对应命令重新校验。归档报告丢失或状态过期时同样通过重试生成，原验收报告与 JSON 不改写。
- 完成阶段必须包含对应的成功校验尝试、完整命令记录及相符的校验结果；仅有 synced/archived 状态文字不能通过 check。

归档报告由工具根据阶段生成，包含 active_change_path、archived_change_path、原规划/验收记录哈希、检查点引用和最终状态。归档后旧活动路径保留历史含义，工具读取时只映射该前缀，不生成新的验收通过记录。

适用范围：单根普通文件、现有 evidence.py 机器记录，以及支持 context、规范/归档 validate、list JSON 的 CLI。正式规范根不同可用已核实的 `--spec-root`；不能用该参数绕过实际 schema 的同步语义。校验覆盖当前根全部正式规范及归档，其他既有无效规范也会阻止通过，需报告具体原因。不支持并发归档同一变更；执行期间不要同时修改相关文件。指纹不是防篡改签名，也不覆盖运行环境动态状态。

manual 不调用本机器工具。无运行时、多根、链接或不支持的 CLI 布局按人工核验清单记录相同的阶段、原记录哈希、前后内容、非同步输入及真实校验结果；不能生成冒充 machine 的 JSON，也不能用 manual 绕过已有机器校验失败。

恢复时正式规范的预期变化可能导致普通 `check-verify` 报告来源失效。这时按上述逐项比较记录“同步恢复核验通过”，保留原记录，不伪称 `check-verify` 通过、不重写规划 PASS，也不为消除指纹差异机械重跑业务验收。只有预先登记的同步变化可走此路径，其他变化仍需重新评估。

## 取消或放弃

仅在用户明确要求取消、放弃或替代该变更时使用。记录原因、已实现与未完成内容、残留代码/环境状态以及后续责任，不同步未完成增量为正式规范。以 `Cancelled` 或 `Superseded` 标记，归档保留历史，不宣称完成验收。残留代码的删除或回滚需要符合用户授权，不能因取消规划就自动清理。
