# 项目说明

本项目围绕迷宫竞赛机器人的路径规划问题展开，目标是在统一地图、统一接口和统一评判标准下，对多种路径规划算法进行比较与分析。

当前计划采用的算法主线为：

1. `BFS`：静态无权最短路基准算法
2. `A*`：启发式搜索效率优化
3. `改进 A* / 带权 A*`：引入转弯、风险与狭窄区域代价
4. `LPA*`：动态环境下的增量式重规划
5. `D* Lite`：面向在线修正的动态路径规划

## 目录结构

- [计划书.md](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/计划书.md)
  项目背景、研究目标、算法递进关系与分工安排。
- [接口规范.md](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/接口规范.md)
  地图输入格式、算法输出格式、计时方法、总代价公式与评判标准。
- [maps](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/maps)
  下载的 Micromouse 文本迷宫。
- [scripts/convert_micromouse_maps.py](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/scripts/convert_micromouse_maps.py)
  将原始 Micromouse 文本地图批量转换为项目 JSON 格式。
- [scripts/load_map.py](/Users/linzelai/Documents/大学课程/大二下/运筹学/opt_final/scripts/load_map.py)
  读取 JSON 地图或原始文本地图，并提供基础访问函数。

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

## 当前状态

目前已经完成：

1. 计划书与接口规范整理
2. 公开迷宫地图下载
3. 文本地图到 JSON 接口格式的转换脚本
4. 地图读取脚本

后续建议优先完成：

1. `BFS` 基准算法实现
2. `A*` 与改进 `A*` 的统一测试框架
3. `LPA*` 与 `D* Lite` 的动态障碍输入与重规划实验
