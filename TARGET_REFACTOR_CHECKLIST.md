# Target Refactor Checklist

## 目的

把 `mtb-evo` 当前顶层 target 的语义和实际分层对齐，减少后续维护时的理解成本。

当前目标分层应明确为：

- Layer A: `foundation`
- Layer B: `core`
- Layer C: `downstream inputs`
- Layer D: `reports`

## 当前已确认的问题

### 1. `core_only` 命名和实际行为不一致

当前 [Snakefile](/data/projects/nmx/mtb-evo/Snakefile:17) 中：

- `core_only`
  - 依赖 `foundation_prepare_outputs`
  - 依赖 `run_core`

所以它实际跑的是 `Layer A + Layer B`，不是纯 `Layer B`。

这会造成两个问题：

- 用户以为只跑 core，实际还会启动 foundation
- `fastp` 会在 `core_only` 里出现，和分层直觉不一致

### 2. 缺少单独的 `foundation_only`

当前没有单独入口只跑 Layer A。

这导致：

- 想只准备 `fastp_qc` / foundation 结果时，没有清晰 target
- foundation 只能通过 `core_only` 或更上层 target 间接触发

## 建议的目标结构

### 保留并明确的 target

1. `foundation_only`
- 只跑 Layer A
- 输入：
  - `rules.foundation_prepare_outputs.output.done`

2. `core_only`
- 只跑 Layer B
- 输入：
  - `rules.run_core.output.done`

3. `downstream_only`
- 只跑 Layer C
- 输入：
  - `rules.prepare_downstream_inputs.output.done`

4. `reports_only`
- 只跑 Layer D
- 输入：
  - `rules.build_reports.output.done`

5. `all`
- 全流程入口
- 输入：
  - `rules.build_reports.output.done`

## 设计原则

### A. 不拆 D1 / D2

当前不建议把 `lineage` 和 `figure/table` 再拆成两个独立 target。

原因：

- 如果 Layer C 已经准备好了报告层全部输入
- 那么 `reports_only` 统一代表 Layer D 更简单
- 现阶段拆 D1 / D2 会增加 target 数量和维护负担

### B. 保持 `downstream_only` 语义不变

`downstream_only` 依赖 Layer A + B 是合理的。

因为 Layer C 本来就是建立在：

- foundation 已完成
- core 已完成

之上的桥接输入层。

### C. 不在本轮同时改动算法逻辑

本轮只调整：

- target 命名
- target 依赖
- 顶层 `Snakefile` 入口语义

不修改：

- `core` 算法流程
- `foundation` 处理逻辑
- `downstream` 生成逻辑
- `reports` 构建逻辑

## 最小改动实施方案

### Step 1

在 [Snakefile](/data/projects/nmx/mtb-evo/Snakefile:1) 中新增：

- `foundation_only`

目标输入：

- `rules.foundation_prepare_outputs.output.done`

### Step 2

修改 [Snakefile](/data/projects/nmx/mtb-evo/Snakefile:17) 中的 `core_only`：

从：

- `foundation_prepare_outputs`
- `run_core`

改为只保留：

- `run_core`

### Step 3

保留：

- `downstream_only`
- `reports_only`
- `all`

不改变其功能边界。

### Step 4

同步更新文档中对 target 的说明，至少包括：

- `README.md`
- 任何提到 `core_only` 含义的本地运行文档

## 暂不执行的改动

以下内容本轮不做：

1. 拆分 `reports_only` 为 `lineage_only + reports_only`
2. 把 `foundation_prepare_outputs` 改名
3. 把 `alignment_variant.smk` 的占位结构重构为实际规则
4. 调整 Layer C / Layer D 的底层实现方式

## 修改后预期效果

修改完成后，顶层 target 语义应变为：

- `foundation_only` = Layer A
- `core_only` = Layer B
- `downstream_only` = Layer C
- `reports_only` = Layer D
- `all` = Layer A + B + C + D

这样可以确保：

- target 名字和实际行为一致
- `fastp` 不再出现在 `core_only` 的预期里
- 后续维护时更容易判断每层该改哪里
