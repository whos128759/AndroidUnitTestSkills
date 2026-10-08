# Mockito 用于本地单元测试

用户指定 Mockito，或获批计划需要隔离外部协作依赖时使用。保留真实的被测对象；只模拟其依赖。优先断言返回值、状态和错误；调用次数或参数属于行为约定时再用 `verify`。不要只验证 mock 调用而不验证目标行为。

## 本地依赖

`assets/mockito/` 已包含 Mockito Core 5.23.0、Byte Buddy 1.17.7、Byte Buddy Agent 1.17.7、Objenesis 3.3 的 JAR。这四个文件构成此版本 `mockito-core` 的 JVM 运行依赖；完整来源、校验值和许可证位置见 [本地依赖清单](../assets/mockito/README.md)。适用于 Java 11+ 的 `src/test`，Java 和 Kotlin 测试都可调用 `org.mockito.Mockito`。使用前从 Skill 目录运行 `python scripts/verify_mockito_bundle.py` 校验文件。

计划获批后，仅在项目需要离线补齐 Mockito 且没有可复用的兼容依赖时，复制四个 JAR 到目标项目根目录的 `test-libs/mockito/`，在被测模块的 Gradle `dependencies` 中加入（Kotlin DSL 和 Groovy DSL 均可）：

```gradle
testImplementation(files(
    rootProject.file("test-libs/mockito/mockito-core-5.23.0.jar"),
    rootProject.file("test-libs/mockito/byte-buddy-1.17.7.jar"),
    rootProject.file("test-libs/mockito/byte-buddy-agent-1.17.7.jar"),
    rootProject.file("test-libs/mockito/objenesis-3.3.jar")
))
```

先检查项目已有 Mockito、MockK、fake、JDK 和依赖版本。若已有 Mockito 可离线使用，沿用现有版本；若与本地 JAR 冲突，先在计划说明处理办法，不混用版本。`mockito-kotlin` 辅助库未打包；离线方案在 Kotlin 中直接使用 Mockito Core API。`mockito-android` 面向设备上的 `androidTest`，不在本 Skill 的本地 JVM 范围。其他 Gradle、JUnit 或 Android 依赖仍须由项目已有缓存或本地仓库提供；这组 JAR 只消除 Mockito 本身的下载需求。

使用已缓存的 Gradle 分发，以 `--offline` 构建并保留命令、日志和 JAR 校验结果；依赖缺失时明确阻塞，不切换到联网重试。`--offline` 约束 Gradle 依赖解析，不能单独证明 Wrapper 或自定义构建脚本没有联网；同时检查这些入口并遵守项目的断网要求。

复制 JAR 前沿用项目的二进制依赖管理规则。若仅供本地临时使用，可建议将 `test-libs/mockito/` 加入本地忽略规则；若构建依赖这些文件，应按项目约定随交付保存，或提供可复现的离线获取方式，不能一律忽略后留下缺失依赖。

## 编写方式

Java 使用 `Mockito.mock`、`Mockito.when(...).thenReturn(...)` 和 `Mockito.verify`。Kotlin 使用 `Mockito.mock(Type::class.java)`、``Mockito.`when`(...)`` 和 `Mockito.verify`；遇到非空返回值的桩设置问题，可用 ``Mockito.doReturn(value).`when`(mock).method()``。每个测试重新创建所需 mock，避免测试间共享状态；只设置当前场景实际调用的行为。协程或 Flow 测试同时遵循[协程与 Flow 测试](coroutines-flow.md)，不要用真实时间等待 mock 回调。

测试目的和预期结果仍来自已审查计划。不要为了让断言通过而模拟被测类本身、过度模拟内部实现，或放宽失败断言。

来源：[Mockito 官方文档及 Android/JVM 依赖说明](https://github.com/mockito/mockito/blob/main/mockito-core/src/main/java/org/mockito/Mockito.java)、[Mockito Core 5.23.0 POM](https://repo.maven.apache.org/maven2/org/mockito/mockito-core/5.23.0/mockito-core-5.23.0.pom)。
