# 项目说明

本项目围绕迷宫竞赛机器人的路径规划问题展开，目标是在统一地图、统一接口和统一评判标准下，对多种静态与动态路径规划算法进行比较分析。

当前已接入或预留的算法主线为：

1. `BFS`：静态无权最短路基准
2. `DFS`：静态深度优先搜索，对比 `BFS`
3. `A*`：启发式搜索效率优化
4. `Weighted A*`：预留
5. `LPA*`：动态环境增量重规划
6. `D* Lite`：在线动态路径规划

## 目录结构

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
│   ├── .gitkeep
│   └── README.md
└── src/
    ├── main.py
    ├── algorithm_registry.py
    ├── dynamic_map_builder.py
    ├── visualization.py
    ├── bfs/
    ├── dfs/
    ├── a_star/
    ├── weighted_a_star/
    ├── lpa/
    └── dlite/
```

整理原则：

1. 原始处理脚本统一放在 `scripts/`
2. 算法和主流程统一放在 `src/`
3. 每个算法保留独立子目录，便于组员并行开发
4. 运行结果统一写入 `outputs/`
5. 可视化统一写入 `outputs/visualizations/<run_name>/`

## 当前状态

当前已经完成：

1. 计划书与接口规范整理
2. Micromouse 地图下载与 JSON 转换
3. 统一地图读取脚本
4. `BFS`、`DFS`、`A*`、`Weighted A*`、`LPA*`、`D* Lite` 可运行版本
5. 主流程 `main.py`、算法注册器、动态图构造器
6. `PNG + GIF` 双产物可视化

## 输出路径

主流程约定：

1. 单次运行结果放在 `outputs/<run_name>/`
2. 其中：
   - `outputs/<run_name>/results/` 保存结果 JSON
   - `outputs/<run_name>/dynamic_maps/` 保存主流程生成的动态图
3. 可视化单独汇总到：
   - `outputs/visualizations/<run_name>/`

默认运行目录现在是：

```bash
outputs/default_run
```

如需更清晰的实验管理，建议显式指定：

```bash
python3 'src/main.py' --output-dir 'outputs/demo_run' --visualize-mode image
```

## 可视化输出

图片模式下，每个已实现算法会同时输出：

1. `PNG`：用于报告和静态插图
2. `GIF`：用于答辩和过程演示

示例文件名：

1. `bfs_process.png`
2. `bfs_process.gif`
3. `dfs_process.png`
4. `dfs_process.gif`
5. `a_star_process.png`
6. `a_star_process.gif`
7. `lpa_process.png`
8. `lpa_process.gif`
9. `dstar_lite_process.png`
10. `dstar_lite_process.gif`

11. `weighted_a_star_process.png`
12. `weighted_a_star_process.gif`

## 常用命令

### 1. 批量转换地图

```bash
python3 'scripts/convert_micromouse_maps.py'
```

### 2. 读取地图

```bash
python3 'scripts/load_map.py'
```

### 3. 运行主流程

```bash
python3 'src/main.py' --output-dir 'outputs/demo_run' --visualize-mode image
```

### 4. 单独调用 `D* Lite`

```python
from pathlib import Path
from src.dlite import run_dstar_lite

result = run_dstar_lite(
    Path("maps/dynamic_json/apec2024_dynamic_1.json")
)
print(result["success"], result["path_length"])
```

### 5. 单独调用 `DFS`

```python
from pathlib import Path
from src.dfs import run_dfs

result = run_dfs(
    Path("maps/json/alljapan-045-2024-exp-fin.json")
)
print(result["success"], result["path_length"])
```
