# 协程与 Flow 测试

仅当目标代码使用挂起函数、调度器、`StateFlow` 或 `Flow` 时读取。先沿用项目现有的 `kotlinx-coroutines-test`、Turbine 和调度器注入方式，不锁定版本。

- 用 `runTest` 执行挂起测试；涉及并发、延迟或启动新协程时，用共享同一个 `TestCoroutineScheduler` 的测试调度器控制执行。测试依赖 `Dispatchers.Main` 时，按项目现有规则替换并恢复它。
- 用 `advanceUntilIdle`、`runCurrent` 或 `advanceTimeBy` 控制虚拟时间；不要用 `Thread.sleep` 或真实时间等待同步结果。
- 用 Turbine 验证 Flow 的发射顺序、完成、错误和无额外事件。持续运行的 Flow 应取消收集，不等待永远不会到来的完成事件。
- 若项目未引入 Turbine，简单 Flow 可用现有协程测试工具验证；只有真实场景需要逐项等待与断言时才建议增加依赖，并在计划中说明。

参考：[Android 协程测试指南](https://developer.android.com/kotlin/coroutines/test)、[kotlinx-coroutines-test](https://github.com/Kotlin/kotlinx.coroutines/blob/master/kotlinx-coroutines-test/README.md)、[Turbine](https://github.com/cashapp/turbine)。
