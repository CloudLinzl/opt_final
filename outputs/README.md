# 输出目录说明

本目录只保留输出结构说明，不提交具体实验产物。

推荐约定：

1. 单次运行结果放在 `outputs/<run_name>/`
2. 主流程结果默认写入：
   - `outputs/<run_name>/results/`
   - `outputs/<run_name>/dynamic_maps/`
3. 可视化统一写入：
   - `outputs/visualizations/<run_name>/`

示例：

```text
outputs/
├── .gitkeep
├── README.md
├── demo_run/
│   ├── dynamic_maps/
│   └── results/
└── visualizations/
    └── demo_run/
```
