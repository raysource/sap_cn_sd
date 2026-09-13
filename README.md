# SAP SD 培训课程站（`sap_cn/`）

SAP SD（销售与分销）培训课程：**从概念到流程、从总体到局部**。静态 HTML，无外部依赖，
双击 `index.html` 即可离线打开（`file://` 直接可用，不需要服务器、不联网）。

- 站点入口：`index.html`（课程地图 = 思维导图 + 学习路线）
- Excel：`SAPSD_课程大纲_学习WBS.xlsx`（8 张表）
- 真实截图：`assets/img/sd/**`、`assets/img/prep/**`（269 张，SAP GUI 中文界面）
- 自绘图：`assets/diagrams/*.svg`（7 张：思维导图 / 流程图 / 结构图）

## 16 页的结构（教学顺序 = 导航顺序）

| 页 | 内容 | 自绘图 | 真实截图 |
|---|---|---|---|
| `index.html` | 课程地图、学习路线、六大板块、角色路线 | 思维导图 | — |
| `concept.html` | 概念与定位：真实系统界面、三大概念层、五大单据、12 个常见误解 | 结构图×2、流程图×2 | 3 |
| `org.html` | 组织结构：企业结构 / 销售结构 / 装运结构 + 12 个配置任务 | 组织结构图 | 11 |
| `master.html` | 主数据：客户三层、四个伙伴角色、物料销售视图、条件记录 | — | 9 |
| `pricing.html` | 定价：条件表 → 存取顺序 → 条件类型 → 定价过程 → 过程确定 → 账户确定 | 结构图 | 3 |
| `flow.html` | 端到端 O2C 流程（泳道图）、集成点、状态、顺序错误 | 流程图 | 1 |
| `order.html` | 报价 → 订单（参照创建）、逐字段读法、库存不足的处理 | 流程图 | 8 |
| `delivery.html` | VL01N 交货 → 拣配 → 发货过账（601）→ 库存与会计影响 | — | 6 |
| `billing.html` | VF01 开票 → VF02 下达 → 会计凭证 → 原始凭证/单据流 → 收款 | 流程图 | 8 |
| `analysis.html` | 单据流、VA05、MCTA（含前置条件）、对账、教材踩坑集 | — | 8 |
| `config.html` | **48 个配置任务**按 A~J 十组索引（SPATH 路径 + 手顺 + 画面） | — | 96 |
| `practice.html` | 五个实训任务（做什么 / 完成基准 / 常见错误 / 对应画面） | — | 10 |
| `instructor.html` | 讲师版：课时分配、板书路线、必问 12 题与答案、评分标准 | — | — |
| `worksheet.html` | 学员版：记入表（单据号 / 状态 / 金额 / 自评），可打印 | — | — |
| `quiz.html` | 30 题自测（概念 5 / 组织 4 / 主数据 5 / 定价 6 / 流程 7 / 分析 3），合格 75% | — | — |
| `glossary.html` | 术语中英对照（48 条）+ T-code 速查（33 个）+ 常用表 | — | — |

## 素材来源（重要）

1. **真实截图**取自教材文档 `S4.docx`（与本目录同级的 `sap_sd_cn/S4.docx`，425 页、内嵌 1385 张图）。
   本站按课程需要**复用了 SD 模块与准备章的 269 张**（`sd/`、`prep/` 两棵目录），
   每张图的说明行里保留了**原文件名**（如 `01_1_image1297.png`），可回 Word 原稿逐张核对。
2. **任务号与 SPRO 路径与教材一致**：`work/sd_source.json` 是从 `sap_sd_cn/work/site_model.json`
   导出的 SD 模块 48 个任务（标题 / IMG 路径 / 手顺 / T-code / 截图清单），页面里的路径与
   截图都从它取，不手抄。
3. **自绘图（`assets/diagrams/*.svg`）是本课程自绘**，用于讲清结构与顺序；图上的数值是
   课程场景值，不是标准值。

## 标准值的写法

凡可能因版本/行业方案而异的地方，页面给出「在自系统里怎么确认」（F1/F4、IMG 路径、SE16N 表名），
而不是断言。已确认的场景值（来自教材画面）直接标注来源，例如：
净价值 960,000.00 RMB、发票 `F2` 90000000、出具发票日期 2021.04.15、付款方 10000000、
120 PC、物料 F999-100、起运点 Z999 颐宁装运点、账户分配组 M1/M2、定价过程 RVAA01。

> 注意区分：教材的 `F1 / F2` 两个含义 —— SAP GUI 里 **F1/F4 是快捷键**（字段帮助/取值列表），
> 而 **`F2` 是发票的单据类型**，`M1/M2` 是账户分配组。页面上都写明了语境。

## 目录结构

```
sap_cn/
├─ index.html … quiz.html … glossary.html    16 个页面
├─ assets/
│  ├─ style.css main.js quiz.js              共享设计系统（从 sap_sd_cn 复制，未改）
│  ├─ sd.css sd.js                           本站追加样式 / 灯箱（s4cn 的站内副本改名）
│  ├─ img/{sd,prep}/…                        269 张真实截图（原目录结构照搬）
│  └─ diagrams/*.svg                         7 张自绘图
├─ tools/
│  ├─ sitegen/{common.py,p_overview.py,p_process.py,p_admin.py}   内容与骨架
│  ├─ make_diagrams.py                       自绘图生成器（纯 Python → SVG）
│  ├─ build_pages.py                         生成 16 页（幂等）
│  ├─ make_course_xlsx.py                    生成 Excel
│  ├─ verify_course.py                       本站验证器
│  ├─ check_snapshot_cn.sh                   快照验证（gzip / 条目数 / 归档内 SVG 与磁盘 md5 一致）
│  └─ hub_stats.json                         给训练站索引页用的自报统计
└─ work/
   ├─ sd_source.json                         教材 SD 模块 48 任务（原文路径/手顺/截图）
   ├─ img_manifest.json                      截图宽高清单（生成 <img width/height>）
   ├─ gui_screenshot_text.json               27 张关键画面的逐字读图记录（画面文字核对依据）
   └─ diagram_qa.json                        7 张自绘图的排版缺陷检查记录（含已修复项）
```

## 画面上的数值是怎么确认的

页面里所有「教材环境实测值」（`C999` 颐宁销售 / `Z1` 直销·`Z2` 批发 / `P999` 工厂 / `Z999` 起运点 / 库位 `003` /
客户 `10000000` 远东造船厂 / 交货 `80000000` / 发票 `90000000` / 物料 `F999-100` 铸钢泵 170-230 /
PR00 `8,000.00 RMB` 有效期 2021.01.01–9999.04.14 / 净价值 `960,000.00 RMB`）都不是推的：
`work/gui_screenshot_text.json` 是把 27 张关键画面用视觉逐字抄录的结果（窗口标题、字段、表格列名与行数据，
模糊处标注「不清楚」），页面里的数据表就是从它来的。要核对某张画面时看这个文件即可，
必要时再打开 `assets/img/` 下的原图。

## 重新生成 / 验证

```bash
cd ~/Desktop/work/training/sap_cn

python3 tools/make_diagrams.py      # 自绘图 → assets/diagrams/*.svg（幂等，改图后重跑）
python3 tools/build_pages.py        # 16 页 HTML（统计数字自动数，不手写）
python3 tools/make_course_xlsx.py   # Excel（8 表）

python3 tools/verify_course.py                                             # 本站验证器
python3 ~/.hermes/skills/productivity/sap-training-sites/scripts/verify_site.py .   # 共享验证器
```

当前实测结果：

```
pages=16  figure.shot=155（去重 120 / 磁盘 269）  figure.dia=10（去重 7）  quiz=30
RESULT: PASS
PASS: 16 pages, nav identical, 1 active each, tags balanced, copy buttons present, quiz keys valid
```

`verify_course.py` 检查：结构（DOCTYPE/单 article/article 在 footer 前/标签配平/无重复 id）、
导航（各页 href 一致 + 恰好 1 个 active）、站内链接与锚点、图片与自绘图存在、图注（画面编号 + 来源）、
自测 30 题的答案键落在选项里、hub 统计一致、无残留 Markdown/占位符。

## 已知边界（不要当成缺陷）

- **截图是教材原图的小尺寸裁剪**（多数 400–700px 宽，作者在图上画了红框），所以放大到 2× 以上会糊；
  页面提供「画面显示大小 1×/1.5×/2×」与点击 4× 灯箱，投屏建议 1.5×。
- **没有 SAP 系统可登录**，页面里所有「练习」都以「在自系统里怎么看」的方式给出（F1/F4 + 表 + T-code），
  实训任务假定学员有可访问的环境（`practice.html` 有环境准备清单与达不到时的替代做法）。
- 术语按中文教学场景写（销售范围 / 项目类别 / 装运点…），英文原名在 `glossary.html` 对照。
