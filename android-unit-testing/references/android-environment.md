# 本地测试环境处置

只检查本地源码、构建脚本、现有 JAR、SDK、缓存和日志；以下处置均服从已获批范围。缺失资源时报告阻塞，不自动联网下载。

## 选择运行环境

- 纯业务行为使用 JVM 和可控的依赖替身。需要框架行为时先检查已有 Robolectric 与资源配置；只有所需能力和离线依赖都可用时才采用。
- 必须依赖真实系统服务、厂商平台或设备的行为，说明本地测试的覆盖边界；设备测试超出本 Skill 范围。
- 缺少可用 JDK、SDK、Gradle 分发或依赖时，列出具体缺项、受阻任务和仍可完成的工作。`JAVA_HOME` 为空不等于没有 JDK，须检查项目配置和实际可执行文件。

## `Method ... not mocked`

记录具体框架调用、所在路径、被测断言是否依赖其返回值或副作用，并核对相关配置是否在本次修改前已存在。

优先复用现有可注入依赖或项目可用的 Robolectric。新增包装层涉及生产代码时，须已在用户授权范围内。不要默认复制同包名 `android.*` 类，也不要用 `returnDefaultValues` 掩盖被测行为。

确需例外时，在计划中写明具体配置、影响模块、为何现有方案不可用、哪些行为无法验证以及授权依据；已有同范围授权不重复询问。交付摘要保留例外说明。`returnDefaultValues` 影响该配置下的框架调用，不能仅凭“只为日志”注释就认为影响只限于日志。

## `NoClassDefFoundError` / `ClassNotFoundException`

先查完整异常链，区分缺类、版本冲突和静态初始化失败。仅凭异常名不能认定为 `compileOnly` 问题。

确认缺类时，对照编译与测试运行 classpath、本地 JAR 内容和 Gradle 声明，检查是否只有 `compileOnly` 依赖。若本地存在版本兼容、可在 JVM 执行的实现，可在获批范围内补测试运行依赖；不能把 Android stub JAR 当作真实平台实现。

例如 `android.os.SystemProperties` 或厂商 `android.car.*` 还可能依赖隐藏 API、原生方法或系统服务。没有可用运行环境时，记录“环境阻塞”和缺失能力，给出隔离依赖、缩小已协商范围或另行设备验证的后续动作；保留原始失败计数。根因与环境未变时，不以重复运行代替处置。

## 只编译、不运行用例

按模块与变体检查本地任务定义和依赖关系。常见候选为 `:<module>:compile<Variant>UnitTestJavaWithJavac`，Kotlin 项目还可能需要 `:<module>:compile<Variant>UnitTestKotlin`；具体名称以项目为准，不把 Java 编译完成视为已检查所有 Kotlin 测试。

确认 Gradle Wrapper 的分发已缓存后，可用 `--offline --dry-run` 检查候选任务图，再运行获批编译任务。不能只凭任务名保证安全；`test`、`test<Variant>UnitTest` 会执行用例。记录实际命令、任务图/日志及是否运行测试。
