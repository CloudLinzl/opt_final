# 项目说明

本项目围绕迷宫竞赛机器人的路径规划问题展开，目标是在统一地图、统一接口和统一评判标准下，对多种路径规划算法进行比较与分析。

当前计划采用的算法主线为：

1. `BFS`：静态无权最短路基准算法
2. `A*`：启发式搜索效率优化
3. `改进 A* / 带权 A*`：引入转弯、风险与狭窄区域代价
4. `LPA*`：动态环境下的增量式重规划
5. `D* Lite`：面向在线修正的动态路径规划

当前代码主流程已经预留 `BFS`、`A*`、`改进 A* / 带权 A*`、`LPA*` 的统一接入位置，动态算法中已完成 `D* Lite` 第一版。

## 目录结构

- [计划书.md](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/计划书.md)
  项目背景、研究目标、算法递进关系与分工安排。
- [接口规范.md](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/接口规范.md)
  地图输入格式、算法输出格式、主流程约定、计时方法、总代价公式与评判标准。
- [maps](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/maps)
  下载的 Micromouse 文本迷宫。
- [scripts/convert_micromouse_maps.py](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/scripts/convert_micromouse_maps.py)
  将原始 Micromouse 文本地图批量转换为项目 JSON 格式。
- [scripts/load_map.py](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/scripts/load_map.py)
  读取 JSON 地图或原始文本地图，并提供基础访问函数。
- [src](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/src)
  项目主流程和算法模块目录。
- [src/main.py](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/src/main.py)
  单张地图主流程入口，负责静态图读取、动态图生成、算法调度、结果保存和可视化占位。
- [src/algorithm_registry.py](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/src/algorithm_registry.py)
  统一算法注册和占位结果逻辑。
- [src/dynamic_map_builder.py](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/src/dynamic_map_builder.py)
  将“静态图 -> 动态事件 -> 动态图文件落盘”封装为主流程可调用函数。
- [src/visualization.py](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/src/visualization.py)
  统一可视化接口，当前支持文本模式和图片模式占位。
- [src/dlite](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/src/dlite)
  `D* Lite` 相关模块目录。
- [src/dlite/dstar_lite.py](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/src/dlite/dstar_lite.py)
  当前已实现的 `D* Lite` 核心模块。

## 文件架构

```text
opt_final/
├── README.md
├── 计划书.md
├── 接口规范.md
├── maps/
│   ├── *.txt
│   ├── json/
│   └── dynamic_json/
├── scripts/
│   ├── convert_micromouse_maps.py
│   ├── generate_dynamic_maps.py
│   └── load_map.py
├── outputs/
│   └── .gitkeep
└── src/
    ├── __init__.py
    ├── main.py
    ├── algorithm_registry.py
    ├── placeholders.py
    ├── bfs/
    │   ├── __init__.py
    │   └── runner.py
    ├── a_star/
    │   ├── __init__.py
    │   └── runner.py
    ├── weighted_a_star/
    │   ├── __init__.py
    │   └── runner.py
    ├── lpa/
    │   ├── __init__.py
    │   └── runner.py
    ├── dynamic_map_builder.py
    ├── visualization.py
    └── dlite/
        ├── __init__.py
        └── dstar_lite.py
```

整理原则：

1. 原始处理脚本统一放在 `scripts/`
2. 主流程和通用调度模块统一放在 `src/`
3. 各算法分别保留独立子目录，便于组员并行开发
4. `D* Lite` 相关实现统一收拢到 `src/dlite/`
5. 所有运行产物统一写入 `outputs/`

## 地图数据

项目当前使用的地图来自公开的 Micromouse 迷宫库，主要是 `16x16` 标准迷宫，适合做静态最短路、带权路径优化和动态重规划实验。

当前已准备多张测试地图，位于 [maps](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/maps) 目录下。  
地图来源和用途说明见 [maps/README.md](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/maps/README.md)。

## 当前脚本用法

### 1. 批量转换地图

```bash
python3 'scripts/convert_micromouse_maps.py'
```

执行后会在 `maps/json/` 下生成对应的 JSON 地图文件和 `manifest.json`。

### 2. 读取地图

```bash
python3 'scripts/load_map.py'
```

该脚本默认会读取一张示例地图并输出概要信息。

也可以在其他 Python 文件中这样使用：

```python
from pathlib import Path
from scripts.load_map import load_map, get_neighbors

maze = load_map(Path("maps/json/apec2024.json"))
print(maze["start"], maze["goal"])
print(get_neighbors(maze, maze["start"][0], maze["start"][1]))
```

### 3. 运行主流程

```bash
python3 'src/main.py' --output-dir 'outputs/demo_run'
```

默认主流程会：

1. 读取一张静态 JSON 地图
2. 生成一份动态图并落盘
3. 调用已注册算法
4. 对未实现算法写入占位结果
5. 调用已注册的动态算法，包括 `LPA*` 和 `D* Lite`
6. 保存完整结果、摘要结果和可视化产物

常用参数：

```bash
python3 'src/main.py' \
  --static-map 'maps/json/apec2024.json' \
  --output-dir 'outputs/apec2024_run' \
  --variant-index 1 \
  --seed 42 \
  --visualize-mode text
```

### 4. `D* Lite` 模块调用

后续如果单独调试 `D* Lite`，可直接调用：

```python
from pathlib import Path
from src.dlite import run_dstar_lite

result = run_dstar_lite(
    Path("maps/dynamic_json/apec2024_dynamic_1.json")
)
print(result["success"], result["path_length"])
```

## 当前状态

目前已经完成：

1. 计划书与接口规范整理
2. 公开迷宫地图下载
3. 文本地图到 JSON 接口格式的转换脚本
4. 地图读取脚本
5. `D* Lite` 第一版模块
6. 主流程 `main`、算法注册表、动态图构造器与可视化占位接口
7. `BFS`、`A*`、`改进 A* / 带权 A*`、`LPA*` 的目录级预留骨架

当前主流程状态：

1. `BFS`、`A*`、`改进 A* / 带权 A*`、`LPA*` 已有可导入的占位包和统一入口函数
2. `D* Lite` 已能接收主流程生成的 `dynamic_updates`
3. 可视化接口当前支持文本输出，图片模式仍为占位实现

后续建议优先完成：

1. `BFS` 基准算法实现并替换占位 `runner.py`
2. `A*`、改进 `A*` 与 `LPA*` 按统一函数签名替换对应占位实现
3. 将文本可视化升级为路径图像输出
4. 根据统一结果 JSON 编写后续分析脚本

## 新算法接入步骤

后续组员接入 `BFS`、`A*`、`改进 A* / 带权 A*` 或 `LPA*` 时，建议按下面的最小步骤完成。

### 1. 新建算法文件

在 [src](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/src) 目录下新增对应模块，例如：

1. `src/bfs/runner.py`
2. `src/a_star/runner.py`
3. `src/weighted_a_star/runner.py`
4. `src/lpa/runner.py`

### 2. 暴露统一入口函数

每个模块至少提供一个统一入口函数：

```python
def run_bfs(map_input, **kwargs) -> dict:
    ...
```

```python
def run_a_star(map_input, **kwargs) -> dict:
    ...
```

```python
def run_weighted_a_star(map_input, **kwargs) -> dict:
    ...
```

其中：

1. `map_input` 可以直接接收地图路径，也可以接收已经加载好的 `map_data`
2. 推荐在函数内部先调用 `scripts.load_map.load_map(...)` 做兼容
3. 返回值必须是字典，并对齐 [接口规范.md](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/接口规范.md) 中的统一字段

### 3. 至少返回这些字段

静态算法建议至少返回：

```python
{
    "maze_id": "...",
    "algorithm": "BFS",
    "success": True,
    "path": [[x0, y0], [x1, y1]],
    "path_length": 0,
    "turn_count": 0,
    "risk_cost": 0,
    "narrow_cost": 0,
    "explored_nodes": 0,
    "runtime_ms": 0.0,
    "total_cost": 0.0,
    "replan_count": 0,
    "replan_time_ms": 0.0,
    "updated_nodes": 0,
    "replanned_path_length": 0
}
```

说明：

1. 静态算法没有动态重规划时，动态字段统一填 `0`
2. `algorithm` 字段建议分别写成 `BFS`、`A*`、`Weighted A*`
3. `path` 要保留完整坐标序列，方便主流程可视化

### 4. 不需要手动改主流程

当前 [src/algorithm_registry.py](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/src/algorithm_registry.py) 已经预留了这三个算法的注册信息：

1. `src.bfs -> run_bfs`
2. `src.a_star -> run_a_star`
3. `src.weighted_a_star -> run_weighted_a_star`
4. `src.lpa -> run_lpa`

只要文件名和函数名按这个约定实现，`main.py` 就会自动尝试调用，不需要再改主流程。

### 5. 本地自测方式

算法模块写好后，可以先直接运行主流程测试：

```bash
python3 'src/main.py' \
  --static-map 'maps/json/apec2024.json' \
  --output-dir 'outputs/test_run' \
  --seed 42 \
  --visualize-mode text
```

然后重点检查：

1. `outputs/test_run/results/run_result.json` 中对应算法是否从 `not_implemented` 变成真实结果
2. `path`、`path_length`、`runtime_ms` 等字段是否存在
3. `outputs/test_run/visualizations/` 下是否生成了对应算法的文本可视化结果

### 6. 推荐实现顺序

为了尽快让全组主流程跑通，建议按下面顺序接入：

1. 先实现 `BFS`，确认统一输入输出和可视化链路没有问题
2. 再实现 `A*`，和 `BFS` 做基础静态对比
3. 然后实现 `改进 A* / 带权 A*`，补充风险区、狭窄区和综合代价逻辑
4. 最后实现 `LPA*`，与 `D* Lite` 共用动态事件输入进行比较

## 输出说明

`main.py` 每次运行后，默认会在输出目录中生成三类内容：

1. `dynamic_maps/`
   主流程生成的动态图 JSON 文件
2. `results/`
   - `run_result.json`：完整结果
   - `run_summary.json`：摘要结果
3. `visualizations/`
   - 每个算法一份文本可视化或图片占位
   - `manifest.json`：可视化产物清单
