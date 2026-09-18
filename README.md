# 芋含的固收平台

面向固收面试准备的移动端市场工作台，覆盖中国利率债、信用债、可转债、美债与商品，并提供当日、本周、本月视角、趋势图和权威来源链接。

网站：[https://luyuhan202303-coder.github.io/yuhan-fixed-income/](https://luyuhan202303-coder.github.io/yuhan-fixed-income/)

## 自动更新

仓库中的 `Daily market update` GitHub Actions 工作流会在中国时间每个工作日 07:45 和 20:45 自动抓取、校验、保存并部署行情。关键来源缺失或日期错位时，任务会停止发布，保留最近一次已核验数据。

详细口径见 [`automation/README.md`](automation/README.md)。
