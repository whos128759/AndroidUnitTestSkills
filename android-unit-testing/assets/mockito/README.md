# Mockito 本地依赖

用于 Android 项目 `src/test` 的 JVM 单元测试。四个 JAR 均来自 Maven Central，版本对应 [Mockito Core 5.23.0 POM](https://repo.maven.apache.org/maven2/org/mockito/mockito-core/5.23.0/mockito-core-5.23.0.pom)。将整个目录随 Skill 一起复制；使用方式见 [Mockito 使用](../../references/mockito.md)。

| 文件 | 来源 | SHA-256 | 许可证位置 |
| --- | --- | --- | --- |
| `mockito-core-5.23.0.jar` | [Maven Central](https://repo.maven.apache.org/maven2/org/mockito/mockito-core/5.23.0/mockito-core-5.23.0.jar) | `ae295bebd5d11fab97ab297815dc7617188b86003cbce3dfd5c0d5c3a6cc4a0c` | JAR 内 `LICENSE`（MIT） |
| `byte-buddy-1.17.7.jar` | [Maven Central](https://repo.maven.apache.org/maven2/net/bytebuddy/byte-buddy/1.17.7/byte-buddy-1.17.7.jar) | `3575dcb8a98faf943d3c1595c47a16047c4fce8a83ebbb26262f1a2f67546357` | JAR 内 `META-INF/NOTICE`、`META-INF/LICENSE` 和 `META-INF/licenses/ASM` |
| `byte-buddy-agent-1.17.7.jar` | [Maven Central](https://repo.maven.apache.org/maven2/net/bytebuddy/byte-buddy-agent/1.17.7/byte-buddy-agent-1.17.7.jar) | `a9ba887dca252ad61b7d5153294f34e6f3bdf4b2736b04373d13615a695fc0ff` | JAR 内 `META-INF/LICENSE`、`META-INF/NOTICE`（Apache-2.0） |
| `objenesis-3.3.jar` | [Maven Central](https://repo.maven.apache.org/maven2/org/objenesis/objenesis/3.3/objenesis-3.3.jar) | `02dfd0b0439a5591e35b708ed2f5474eb0948f53abf74637e959b8e4ef69bfeb` | JAR 内 `META-INF/LICENSE`、`META-INF/NOTICE`（Apache-2.0） |

同名 `.sha1` 文件是 Maven Central 发布的校验值。运行 `python scripts/verify_mockito_bundle.py` 可核对固定 SHA-256、上游 SHA-1 和 JAR 完整性。本目录只覆盖 Mockito Core 的运行依赖，不包含 JUnit、Android Gradle Plugin 或 `mockito-kotlin`。
