# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

## [Unreleased]

- Crawls by Place
- 多进程爬虫提升速度
- 支持百度坐标系转换到其他 crs
- 瓦片进度条可视化
- 修复 Google 瓦片服务


## [V1.1] - 2022-09-08

### Added

- 支持一键安装 python 库
- Provider 新增 `Baidu Tile`, 目前共支持 Amap、OpenStreetMap 三大瓦片服务提供商
- 支持百度瓦片和`经纬度`/`bounding box` 之间的转换, 以及瓦片的合并
- 支持通过 `坐标`、`xyz`方式获取瓦片，并计算其经纬度
- 日志的等级设置 `set_logger`
- 支持 proxy pool

### Changed

- `vis_geodata` -> `plot_geodata`, 可视化函数重命名
- `bounds2img` 抽象三种坐标系基本逻辑

## [1.0.0] - 2022-09-01

- initial release

<!-- Links -->
[keep a changelog]: https://keepachangelog.com/en/1.0.0/
[semantic versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[unreleased]: https://github.com/Author/Repository/compare/v0.0.2...HEAD
[1.0.0]: https://git.pcl.ac.cn/huangwk/TileMap