# Android 单元测试开源资源

整理于 2026-09-28。优先看官方文档和项目 README；依赖版本以各项目当前说明为准。

使用时默认离线，优先本地源码、文档、JAR 与已有缓存。下列链接用于资料溯源，不要求执行技能时访问外网；资源不足时说明阻塞，不自动下载。

首版工作流见 [android-unit-testing/SKILL.md](android-unit-testing/SKILL.md)，验收案例见 [evals/cases.md](evals/cases.md)，[HTML 样例报告](evals/sample-report.html)使用模拟 JUnit XML 生成，未运行 Android 项目。工作流先确认测试意图、提交计划供审查，再按批准范围构建与运行，最终生成 HTML 测试报告。此目录是 Skill 源码；要在 Android 项目中自动发现，可将完整的 `android-unit-testing` 文件夹复制到该项目的 `.agents/skills/`，包括 [Mockito 本地依赖](android-unit-testing/assets/mockito/README.md)。

## 先选测试环境

- `src/test`：本地 JVM 测试，适合业务逻辑、ViewModel、协程、Flow、数据层；需要模拟 Android 框架时可用 Robolectric。
- `src/androidTest`：设备或模拟器测试，适合必须依赖真实 Android 环境的集成与 UI 场景。截图测试也可借助 Paparazzi 或 Roborazzi 在本地 JVM 运行。

参考：[Android 本地单元测试](https://developer.android.com/training/testing/local-tests)、[测试策略](https://developer.android.com/training/testing/fundamentals/strategies)、[测试什么](https://developer.android.com/training/testing/fundamentals/what-to-test)。

## 基础库

| 资源 | 用途 | 何时选用 |
| --- | --- | --- |
| [JUnit 4](https://github.com/junit-team/junit4) | 测试运行、断言、规则 | Android 项目常见基础测试框架；目前处于维护模式 |
| [Truth](https://github.com/google/truth) | 更易读的断言和失败信息 | JUnit 原生断言不够清晰时 |
| [MockK](https://github.com/mockk/mockk) | Kotlin 对象、协程函数模拟 | 需要 Kotlin 风格 mock 时 |
| [Mockito Core](https://github.com/mockito/mockito) | Java/Kotlin 的依赖模拟 | 本 Skill 已打包 JVM 运行依赖，可离线使用 |
| [Mockito-Kotlin](https://github.com/mockito/mockito-kotlin) | Mockito 的 Kotlin 辅助 API | 项目已经使用 Mockito 时 |
| [kotlinx-coroutines-test](https://github.com/Kotlin/kotlinx.coroutines/blob/master/kotlinx-coroutines-test/README.md) | `runTest`、测试调度器、虚拟时间 | 测试挂起函数或协程调度时 |
| [Turbine](https://github.com/cashapp/turbine) | 逐项验证 `Flow` 发射、完成和错误 | 测试 `Flow` 状态序列时 |
| [MockWebServer](https://github.com/square/okhttp#mockwebserver) | 本地 HTTP 测试服务器 | 验证网络客户端请求及响应处理时 |

本 Skill 自带 Mockito Core 及其 JVM 运行依赖，Java/Kotlin 本地测试可避免下载这些 JAR；`mockito-kotlin` 辅助库未打包。能用真实对象或简单 fake 测试时，无须先引入 mock 库；[Now in Android](https://github.com/android/nowinandroid) 就采用测试替身测试数据层与 ViewModel。

## Android 环境与界面

| 资源 | 用途 |
| --- | --- |
| [Robolectric](https://github.com/robolectric/robolectric) | 在 JVM 上模拟 Android 环境，测试依赖框架 API 的逻辑 |
| [AndroidX Test](https://github.com/android/android-test) | Android 测试核心 API、Runner、Espresso 等；UI/设备测试参考 |
| [Paparazzi](https://github.com/cashapp/paparazzi) | 不启动设备或模拟器，做 View/Compose 截图测试 |
| [Roborazzi](https://github.com/takahirom/roborazzi) | 基于 Robolectric 的 JVM 截图测试 |

截图测试关注视觉回归，不代替业务逻辑断言。`AndroidX Test`、Espresso 和设备测试属于扩展范围，不等同于本地单元测试。

## 可直接参考的项目与教程

| 资源 | 看点 |
| --- | --- |
| [Android Architecture Samples](https://github.com/android/architecture-samples) | 小型 TODO 应用；单元、集成、端到端测试和测试替身 |
| [Now in Android](https://github.com/android/nowinandroid) | 较完整应用；ViewModel/数据层测试、fake、截图测试 |
| [Android Testing Samples](https://github.com/android/testing-samples/tree/main/unit) | 官方测试示例的 `unit` 目录；部分示例较旧，借鉴思路时核对依赖与 API |
| [Android 协程测试指南](https://developer.android.com/kotlin/coroutines/test) | `runTest`、`TestDispatcher`、虚拟时间与调度器注入 |
| [Android 测试替身指南](https://developer.android.com/training/testing/fundamentals/test-doubles) | fake、stub、mock 的选择与用法 |

建议阅读顺序：本地单元测试与测试策略，接着看 Architecture Samples 的 ViewModel/数据层测试，再按项目实际需求选协程、Flow、网络或 Android 环境测试工具。

分发时保留完整技能文件夹（包括 `scripts/fixtures/`）。可在任意可写工作目录用 Python 3.9+ 离线运行 `python <技能目录>/scripts/test_render_junit_report.py` 验证报告工具，不依赖本仓库外层的 `evals/`。独立 HTML 报告须与脚本生成的同名 `-artifacts/` 目录一起保存和交付。

[jdqm/AndroidUnitTest](https://github.com/jdqm/AndroidUnitTest) 可参考本地测试与仪器化测试的区分、外部依赖隔离和构造参数注入。其示例包含旧版依赖及测试目录下的同包名 `android.*` 替代实现；不直接作为当前项目的默认版本或修复规则，先核对项目配置与 Android 官方测试指南。
