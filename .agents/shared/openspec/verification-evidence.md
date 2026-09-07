# 实现验收与证据

## 证据原则

任务完成必须对应真实实现与适用验证。单元测试可使用替身；真实数据库、HTTP、模型、上传或运行环境的必需验收不能用 mock、skip、仅收集测试或旧版本报告代替。

每份运行证据记录命令、工作目录、退出码、时间、代码状态、测试范围及相关环境标识。代码状态覆盖相关已提交、未提交和未跟踪文件，不只写 Git HEAD。敏感环境仅记录脱敏标识和必要配置摘要，禁止把凭据写入报告。

临时原始日志、JUnit 和截图保存在项目 `.codex/<变更名>/`；正式索引保存在变更的 `reports/`。索引指向的原始证据必须保留到其验收用途结束，缺失不能视为有效。

## 核验方式

在首次规划评审时选择并在报告中登记 `machine` 或 `manual`，后续 review、apply、verify、archive 沿用同一规则：

- machine：Python 3.9+，输入位于同一授权根内且无符号链接；任务为非空 UTF-8 Markdown checkbox 清单。内置 spec-driven 和本模板 fast-change 满足任务格式要求。其他 schema 必须先核对实际任务格式，不能仅凭名称判断兼容。
- manual：运行时不可用，或项目采用多根目录、符号链接、非 Markdown 任务等不受助手支持的结构时，执行下列人工步骤。无需为使用模板额外安装 Python、改造目录或制造一份假任务清单。
- 项目明确要求机器门禁时，manual 不能替代它；需补足运行时或经项目认可的适配工具。机器校验因内容变化、证据缺失或读取失败而报错时，先处理原因，不能切换模式绕过失败。

人工核验步骤：

1. 列出授权根及稳定代号、相关输入目录、排除项与理由。使用项目可用的文件遍历和 SHA-256 工具，逐根生成排序清单，登记 `根代号 + 相对路径 + 文件类型 + 内容哈希 + 可执行位`；目录也登记，以便重新枚举时发现新增、删除。Git 状态只能辅助发现范围，不能替代未跟踪文件的清单。
2. 对符号链接登记链接文本与解析目标；目标在授权范围内才读取，并纳入目标内容清单。检测循环、失效链接和重复目标，不静默跳过。目标未获授权时保留阻塞；业务依赖 ACL、扩展属性等时另外登记并验证这些属性。
3. 规划清单覆盖 metadata、实际规划、来源、约束及评审报告；只有任务完成字段可以按 schema 语义归一化，并写明规则。JSON/YAML 用相应解析器；非 checkbox 任务按真实状态字段或 schema 的完成条件逐项核验。可选项与不适用项单独说明，不能当作已完成。
4. 验收清单额外覆盖规划清单与报告、原始任务状态、实现、测试、相关依赖配置、原始证据和独立评审。分别保存为 `reviews/planning-manifest.json`、`reports/verification-manifest.json`，或项目已有的等价格式。生成清单时排除自身及其输出临时文件，不能排除业务输入；清单按当前文件实际生成，不手填猜测哈希。
5. 复用、实施交接和归档前重新枚举所有已登记范围、重新计算哈希并比较，再核对任务状态、环境前提与报告结论。记录执行者、时间、工具/命令、差异、范围限制和 `manual`。不同根的清单由总索引关联；不可用复制件代替对原始根的重新检查。

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
2. 需求或任务 → 实现路径 → 测试节点 → 本次证据的对应关系。
3. 实际执行的命令与结果，以及失败、未运行、跳过项。
4. 独立评审结果、阻塞处置、剩余限制和交付/回退要求。
5. 结论：`Ready for Archive`、`Needs Work` 或 `Not Ready`。

fast 用短格式即可：一行等级与基线、任务到实现和真实证据的对应表、一行结论与剩余限制。命令详情可引用已保留的原始日志，不重复复制。没有独立评审要求时如实注明普通自查，不创建空独立评审报告。

只有必需行为、任务和验证全部满足，且不存在未解决阻塞，才能给出 `Ready for Archive`。非阻塞建议可以保留；不得把“几乎完成”作为正常完成归档的通过状态。

## 验收指纹与助手

### 结构化验收清单

除了文件指纹，standard/strict 应保存 `reports/verification-manifest.json`（fast 可使用同样格式的短清单）。使用 `.agents/shared/openspec/scripts/evidence_manifest.py` 校验结构。每个必需需求或任务至少登记 `id`、`implementation`、`tests`、`evidence` 和 `status: verified`；每个命令登记 `command`、根内 `cwd`、整数 `exit_code` 和原始 `evidence` 文件。该校验只检查覆盖关系、路径和字段，不解析 JUnit、日志、截图的业务语义；真实结论仍由 verify 报告负责。

```bash
python3 .agents/shared/openspec/scripts/evidence_manifest.py --root . --manifest openspec/changes/example-change/reports/verification-manifest.json
```

验收记录绑定：有效规划记录、任务原始内容、实现及测试文件、依赖/构建/相关配置、验收报告、原始证据和独立评审。输入中任一项改变，都需重评对应验证，并重新形成当前基线的报告。

machine 使用 [scripts/evidence.py](scripts/evidence.py) 的 `record-verify` / `check-verify`；manual 执行上文等价步骤。`--code` 应覆盖实际相关模块及测试目录，并登记相关依赖清单、锁文件和构建配置；目录快照发现新增/删除文件。记录前对照实际改动及 CLI 产物核对输入范围，不能只列几个文件就声称覆盖新增文件。不要扫描整个用户目录，也不要把 `.codex/` 中不相关产物纳入代码范围。

```bash
python3 .agents/shared/openspec/scripts/evidence.py record-verify --root . --change openspec/changes/example-change --profile standard --code src/changed-module --code tests/changed-module --evidence .codex/example-change/test-results.xml --report openspec/changes/example-change/reports/verification.md
python3 .agents/shared/openspec/scripts/evidence.py check-verify --root . --change openspec/changes/example-change --profile standard
```

路径是示例，使用实际项目入口。strict 额外传 `--independent` 指向当前实现的独立评审报告；非代码任务可以用 `--code` 指定实际修改的文档/配置。

助手会检查文件新鲜度、必需参数和任务勾选，不执行测试、不判断测试语义、不自动证明评审独立，也不是不可伪造的签名系统。记录前必须人工/代理核实声明成立，不能借调用 record 命令制造“已验收”。

版本 2 快照保存文件类型、SHA-256 与可执行位，目录不可读取时直接失败。版本 1 记录需重新核验后生成，不能手改版本号；是否重跑测试取决于实际输入和环境差异。助手忽略目录 `.git`、`__pycache__`、`.venv`、`node_modules`，不覆盖 ACL、扩展属性及运行环境的动态状态；这些内容影响交付时应另补针对性验证。

## 正常完成归档

1. 首次归档按选定方式核对最新验收、任务及基线；已有同步检查点时先进入下文恢复流程。确认归档目标不存在，并在同步前确认目标、差异、授权与当前 schema 的规范规则。
2. 有增量规范时先生成下文检查点，再逐项同步。标准 spec-driven 的主规范用 `## Requirements`，自定义 schema 按其真实同步规则处理；没有可确定的同步语义时保留阻塞，不套用默认格式覆盖。
3. 执行当前 CLI 支持的规范校验，逐项比较预期结果，成功后记录同步完成。失败时保留检查点和当前差异，不移动变更，也不自动回滚用户已有修改。
4. 复核非同步输入未变化、目标规范与预期一致，并再次确认归档目标不存在。保存 `reports/archive-record.md` 中的核验方式、检查点引用、校验结果与归档决定，再整体移动变更目录。
5. 核验目标、源目录及正式规范；在归档位置补记最终路径和完成状态。归档不等于 Git 提交、合并或发布。

无增量规范的 schema 可以明确记录“不需要同步”。有尚未同步的规范时不能以“跳过同步”完成正常归档。

附带记录使用项目相对路径；移动变更后旧活跃路径不再适用。归档前校验原记录，并在归档记录中保存这一结果；不要移动后重新生成一个假装重新测试过的记录。

### 同步检查点与中断恢复

使用 `.agents/shared/openspec/scripts/archive_checkpoint.py` 管理检查点；它只记录和核对，不执行规范同步、迁移、提交、推送或目录移动。只在实际同步主规范时建立 `reports/archive-checkpoint/`，避免给无增量的 fast 变更增加文件。

```bash
python3 .agents/shared/openspec/scripts/archive_checkpoint.py prepare --root . --change openspec/changes/example-change --profile standard --mode machine --archive openspec/changes/archive/2026-01-01-example-change --target openspec/specs/example/spec.md --frozen src --frozen tests
python3 .agents/shared/openspec/scripts/archive_checkpoint.py check --root . --change openspec/changes/example-change
python3 .agents/shared/openspec/scripts/archive_checkpoint.py synced --root . --change openspec/changes/example-change --validation-command 'openspec validate --specs --strict --no-interactive'
# 移动活动目录后，以归档目录作为 --change：
python3 .agents/shared/openspec/scripts/archive_checkpoint.py archived --root . --change openspec/changes/archive/2026-01-01-example-change --validation-command 'openspec list --json'
```

- 写入前使用 `prepare` 保存 `journal.json`：变更及目标归档路径、风险等级、核验方式、同步前验收检查结果、规划/验收记录的哈希、原记录全部输入的同步前清单，以及逐个目标路径的新增/修改/删除操作与预期同步后清单。清单包含文件类型、内容哈希、可执行位及必要目录；不存在的目标显式标记不存在。同步前版本与准备好的完整目标内容保存在检查点内，并与清单绑定，不能在恢复时凭现状补造同步前证据。
- 先完整写入检查点，再将阶段记为 `prepared`；尚未 prepared 不写主规范。每个目标必须仍符合登记的旧状态才能写入；已经等于预期新状态就不重复操作。校验通过且全部目标符合预期时记为 `synced`，保存命令与结果。
- 恢复时先检查阶段、授权、检查点内容和原规划/验收记录是否一致，并复核环境前提与独立评审有效性。重新枚举原记录覆盖的全部输入；只允许检查点列明的主规范目标及其必要目录发生预期变化，代码、增量规划、任务、报告、原始证据等其余输入仍须匹配原基线。
- 在 prepared 阶段，每个目标只能是登记的旧状态或预期新状态；只继续尚未同步的目标，并重新执行规范校验。出现第三种内容、文件缺失不符合登记操作、其他输入变化或检查点不完整时停止恢复，说明具体差异，交回规划/实现/验收流程处理，不能覆盖当前内容。
- 在 synced 阶段，目标必须全部等于预期新状态；复核非同步输入后重跑规范校验，再继续移动。若已移动完成但未记完成状态，只在源目录不存在、目标包含同一检查点且内容一致时补记；源和目标同时存在时停止，不合并或覆盖。

恢复时正式规范的预期变化可能导致普通 `check-verify` 报告来源失效。这时按上述逐项比较记录“同步恢复核验通过”，保留原记录，不伪称 `check-verify` 通过、不重写规划 PASS，也不为消除指纹差异机械重跑业务验收。只有预先登记的同步变化可走此路径，其他变化仍需重新评估。

## 取消或放弃

仅在用户明确要求取消、放弃或替代该变更时使用。记录原因、已实现与未完成内容、残留代码/环境状态以及后续责任，不同步未完成增量为正式规范。以 `Cancelled` 或 `Superseded` 标记，归档保留历史，不宣称完成验收。残留代码的删除或回滚需要符合用户授权，不能因取消规划就自动清理。
