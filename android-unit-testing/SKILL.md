---
name: android-unit-testing
description: Plan, write, run, and report local Android Kotlin or Java unit tests for user-selected modules and behaviors, including Mockito when requested or appropriate. Use for src/test business logic, ViewModel, Repository, coroutine, and Flow tests; exclude device UI automation and screenshot tests.
---

# Android 单元测试

按用户指定的模块和行为工作。保留两个决策点：用户审查测试计划后决定是否编写；用户审查已构建的测试后决定是否运行。用户先前已明确授权同一阶段时，不重复索取授权。

默认只使用本地源码、文档、JAR、SDK 和已有缓存，不访问外网或自动下载工具与依赖。Gradle 命令使用 `--offline`；先确认 Wrapper 对应的 Gradle 分发已在本机可用，避免 Wrapper 自行下载。缺少资源时列出缺项和阻塞范围；确需联网须有用户的明确授权。

## 1. 确认意图并提出计划

确认目标模块、功能、预期行为、重点风险和排除范围。已给出的信息不重复询问；缺少影响预期结果的事实时，先询问，不臆测业务规则。此阶段只读检查项目约束、Gradle 配置、目标实现、调用方、现有测试和运行环境，并记录初始工作区差异。纯业务逻辑优先使用本地 JVM；涉及 Android 框架、平台缺类、编译任务选择或环境缺失时，阅读[本地测试环境处置](references/android-environment.md)。

给用户一份可审查的计划，写明：

- 目标模块、被测类和行为；每个用例的针对功能、测试目的、场景、输入、预期结果及优先级。
- 预期新增或修改的文件；沿用的测试框架、断言库、fake 或 mock；若使用 Mockito，列出被模拟的依赖、原因，以及是否采用本 Skill 自带的离线 JAR 与版本兼容性。
- 拟用的编译任务、限定范围的测试任务、JUnit XML 输入位置、HTML 报告输出位置；说明如何识别测试任务实际执行或命中缓存。
- 环境前提、排除范围、成功标准和无法验证时的处理。

计划获用户批准前，不创建或修改测试代码。计划实质变更（范围、依赖、生产代码、执行方式）时，更新计划供用户审查。

计划交付时附一行阶段证据：本阶段实际执行的只读命令，以及相对初始工作区的文件变化。构建交付时列出实际构建命令和测试任务是否执行；保留已有用户改动，不能用单次 `git status` 代替前后对比。非 Git 项目用目标文件清单或哈希对比。

## 2. 构建测试

按获批计划写最少必要用例。预期结果来自需求和可核实的行为约定，不照抄被测实现。覆盖主要行为、关键失败路径和约定的边界；回归用例尽可能确认缺陷存在时会失败。让用例独立运行；清理测试产生的临时文件和外部副作用，恢复静态状态、调度器与时钟替换，保留测试源码、构建配置和运行产物。沿用项目已有库；可用真实对象或简单 fake 时，无须新增 mock 库。用户指定 Mockito 或获批计划需要 Mockito 时，阅读 [Mockito 使用](references/mockito.md)；优先复用项目已有的兼容依赖，仅在需要离线补齐时从 `assets/mockito/` 复制完整 JVM 依赖。涉及协程或 Flow 时，阅读 [协程与 Flow 测试](references/coroutines-flow.md)。

同步准备 JSON 用例说明，键使用最终测试类与方法的 `TestClass#method` 全名，值填写经审查的 `module`（Gradle 模块）、`target_class`（被测类）、`feature`（针对功能）和 `purpose`（该用例验证什么）。格式见 [用例说明样例](references/case-metadata.json)；样例值不能直接用于真实项目。参数化测试的实际用例名需与 JUnit XML 一致；不可由测试方法名猜测测试目的。

仅执行编译或静态检查任务，确认所选任务不会运行测试用例。不要把编译成功写成测试通过。发现业务代码缺陷时说明证据；除非用户授权修复生产代码，否则保持变更在计划范围内。

向用户展示实际文件改动、用例清单、编译结果及待运行的精确命令。尚未获得运行授权时，到此停止，询问是否运行。运行授权应说明是否包含原计划范围内的失败修正与重跑；未说明时按单次运行处理。

## 3. 运行并交付 HTML 报告

仅运行已获授权范围内的测试。每次使用独立运行目录，保留实际命令、退出状态、日志和获批计划；把复跑所需的测试源码及已改构建配置按项目相对路径保存在该目录的 `source/` 下，并记录被测代码版本或工作区差异。失败后先区分业务缺陷、测试缺陷、环境问题；不要删除用例、放宽断言或把跳过记为通过。若授权仅覆盖单次运行，诊断后报告结果，等待后续指示。

运行测试命令前记录 Unix 时间戳；运行后记录退出码、实际耗时及目标测试任务状态。`UP-TO-DATE`、`FROM-CACHE`、`SKIPPED`、`NO-SOURCE` 均表示本次未执行测试；可引用既有原生报告，但不能宣称本次测试通过。目标测试任务实际执行（Gradle 输出无状态标签，脚本记为 `EXECUTED`；或输出 `FAILED`）且产生本次 JUnit XML 时，使用 [JUnit XML 转 HTML 脚本](scripts/render_junit_report.py) 生成独立 HTML 报告。`--xml-root` 只传一个获批任务的精确 XML 目录或文件，不传整个 `build/test-results`；多个任务分别核对状态、说明和 XML，分别输出报告。不要倒推或修改起始时间来使旧 XML 看似本次产物。示例：

```text
python <技能目录>/scripts/render_junit_report.py --xml-root <单个任务的JUnit-XML目录> --case-metadata <用例说明JSON> --output <本次运行目录>/report.html --scope <获批范围> --command <实际命令> --environment <实际环境> --started-at <运行前Unix时间戳> --exit-code <实际退出码> --duration-seconds <实际耗时秒数> --task-outcome <EXECUTED或FAILED>
```

脚本只用 Python 3.9+ 标准库，按起始时间筛选 XML 并交叉校验套件声明计数与用例节点。说明缺失时一次列出所有问题：计划外键先核对目录和范围；计划内字段缺失再补齐已审查事实，不为混入的用例追加说明。

传 `--run-log` 保留实际日志；已有原生 HTML 报告时传 `--native-report <index.html>`，实际采集覆盖率后可传 `--coverage-report`。脚本把 XML、用例说明及上述文件复制到报告旁的 `<报告名>-artifacts/`，原生报告与覆盖率报告连同其目录中的资源一起归档，并生成相对链接；输出须位于原生报告和覆盖率报告的源目录之外。报告与该目录一起交付，已有输出或归档不会被覆盖。没有有效 JUnit XML 时不生成通过报告，明确写“未验证”并附命令和原因。

最终回复给出简短摘要：总数、通过、失败、跳过、耗时、主要失败原因、HTML 报告与归档路径，以及未验证范围。环境阻塞与经批准的框架替代例外须列明，原始失败仍计入结果。截图不是普通单元测试的必需产物；用户明确要求截图时，从实际报告或测试产物截取。
