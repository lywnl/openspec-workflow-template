# 实现验收与证据

## 证据原则

任务完成必须对应真实实现与适用验证。单元测试可使用替身；真实数据库、HTTP、模型、上传或运行环境的必需验收不能用 mock、skip、仅收集测试或旧版本报告代替。

每份运行证据记录命令、工作目录、退出码、时间、代码状态、测试范围及相关环境标识。代码状态覆盖相关已提交、未提交和未跟踪文件，不只写 Git HEAD。敏感环境仅记录脱敏标识和必要配置摘要，禁止把凭据写入报告。

原始日志、JUnit 和截图保存在项目 `.codex/<变更名>/`；正式索引保存在变更的 `reports/`。仍被验收或归档记录引用的原始证据不能作为普通临时文件清理，缺失不能视为有效。归档不表示证据已纳入 Git，克隆后也不必然可复核；需要跨机器交付时先明确证据保存与授权范围，不擅自移动文件或改写原记录。

## 核验方式

沿用规划评审登记的 machine/manual；首次选择或布局不受支持时读 [核验方式与人工步骤](manual-verification.md)。machine 使用下文标准库助手，manual 维护等价的输入清单及验收映射；不能因机器基线失败而切换方式绕过。正常验收不需要读取归档恢复算法，准备归档时再读 [归档规则](archive-workflow.md)。

## 验收范围

- fast：检查任务证据、改动范围、聚焦测试、静态检查及风险等级是否仍成立。
- standard：将每项必需需求与场景对应到实现和测试；检查失败路径、兼容性、设计约定及相关工程门禁。
- strict：在上述基础上核验全部声明的权限、租户、持久化、迁移、回退、事务、公共契约及跨域边界；取得当前实现的独立代码质量评审。
- 纯文档、配置或非代码任务使用相应的结构、内容或实际加载验证，不为凑测试数编写无意义测试。
- 测试命令来自项目事实，不固定某个框架。静态检查无法证明真实运行成功。

必要验证受环境或授权阻塞时，写 `ENVIRONMENT_NOTE`，保留任务未完成。区分环境问题、共享基线失败和本次实现缺陷；环境问题不能被改名为通过。

## 独立代码质量评审

strict 在当前实现及相关修复完成后，由未撰写该代码的独立评审者检查正确性、失败路径及适用高风险边界，交付 `reviews/implementation-review.md`。报告注明评审者、独立性、当前实现范围、发现、处置和仍缺少的验证；不能把自查改名为独立评审。修复影响结论时，由独立评审者复核受影响部分。

此报告记录代码审查，不代替真实环境验证；`reports/verification.md` 汇总整个变更的验收结论。standard 只在实际争议或风险需要时增加独立评审，fast 无需创建空附件。已有当前有效评审可以引用原位置；同范围复审更新固定报告，不按轮次复制。

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

machine 使用 [scripts/evidence.py](scripts/evidence.py) 的 `record-verify` / `check-verify`，要求规划中已有 implementation_started；没有开始记录时不能在验收阶段补记来冒充已完成的实施入口核验，应说明缺口并回到真实交接。`--code` 应覆盖 reference 登记的实现、测试及配置，并纳入实际新增模块、依赖清单和锁文件；工具检查范围包含关系，删除文件应登记其仍存在的所属目录。目录快照发现新增/删除，但改动是否符合任务仍须语义检查。manual 执行 [人工核验](manual-verification.md) 的等价步骤；不要扩大到用户目录或不相关证据范围。

```bash
python3 .agents/shared/openspec/scripts/evidence.py record-verify --root . --change openspec/changes/example-change --profile standard --code src/changed-module --code tests/changed-module --evidence .codex/example-change/test-results.xml --report openspec/changes/example-change/reports/verification.md
python3 .agents/shared/openspec/scripts/evidence.py check-verify --root . --change openspec/changes/example-change --profile standard
```

路径是示例，使用实际项目入口。strict 额外传 `--independent` 指向当前实现的 `reviews/implementation-review.md`，既有报告仍可沿用原路径；非代码任务可以用 `--code` 指定实际修改的文档/配置。

采用其他辅助评审材料时，使用可重复 `--review-evidence <路径>`；助手校验根内、非空普通文件及无符号链接后，纳入现有 `inputs/snapshot`，重复路径去重。不传参数保留旧行为；采用的辅助报告变化会使验收基线失效。不要将整个 reviews 目录或本次输出 JSON 作为输入。报告与辅助材料定稿后才记录，不把报告自身生成的指纹写回报告。

record-verify 保留原有职责，不自动读取元数据、执行清单校验或判断报告语义；入口先按 [元数据规则](workflow-policy.md#元数据读取与兼容) 核对等级，再检查清单及真实结论。文件格式继续为 JSON `version: 1`。

助手会检查文件新鲜度、必需参数和任务勾选，不执行测试、不判断测试语义、不自动证明评审独立，也不是不可伪造的签名系统。记录前必须人工/代理核实声明成立，不能借调用 record 命令制造“已验收”。

记录采用 `version: 1` 格式，保存文件类型、SHA-256 与可执行位，目录不可读取时直接失败。助手忽略目录 `.git`、`__pycache__`、`.venv`、`node_modules`，不覆盖 ACL、扩展属性及运行环境动态状态；影响交付时另补针对性验证。复用测试须核对相关输入及环境前提，不能只看时间或命令相同。
