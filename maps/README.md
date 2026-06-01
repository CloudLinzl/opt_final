# 地图说明

这批地图来自 Micromouse 公开迷宫库，均为适合路径规划实验的 `16x16` 文本格式迷宫。

## 来源

- 主数据源：`micromouseonline/mazefiles`
- 迷宫格式说明：每个交点用 `o` 表示，横墙用 `---` 表示，竖墙用 `|` 表示，起点用 `S` 标记，目标区用 `G` 标记。

## 当前已下载地图

1. `alljapan-045-2024-exp-fin.txt`
   2024 全日本迷宫，适合做较新的正式比赛样本。
2. `alljapan-044-2023-exp-fin.txt`
   2023 全日本迷宫，可与 2024 迷宫对照测试。
3. `apec2025.txt`
   APEC 2025 迷宫，适合做近年国际赛事样本。
4. `apec2024.txt`
   APEC 2024 迷宫，适合做近年国际赛事样本。
5. `Portugal-2024-Final.txt`
   葡萄牙 2024 决赛迷宫，可作为欧洲赛事样本。
6. `br2024-robochallenge-day1.txt`
   巴西 RoboChallenge 2024 地图，可用于补充不同风格结构。
7. `alljapan-031-2010-frsh.txt`
   2010 全日本历史迷宫，可用于历史样本对照。
8. `alljapan-015-1994-exp-fin.txt`
   1994 全日本历史迷宫，可用于早期迷宫结构对照。

## 使用建议

1. `BFS` 与 `A*` 先用其中 2 到 3 张图做静态调试。
2. 改进 `A*` 可在这些地图上人工标注 `risk_cells` 与 `narrow_cells`。
3. `LPA*` 与 `D* Lite` 可在同一底图上额外加入 `dynamic_updates` 做动态测试。
