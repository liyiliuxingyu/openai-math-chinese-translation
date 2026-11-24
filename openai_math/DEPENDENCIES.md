# 依赖与重新编译说明

本包保留第 001–018 篇历史全文译稿和 PDF。恢复后的 253 个现行译稿文件已逐一匹配旧包中的 SHA256 清单；228 个 TeX 和 10 个 Bib 文件中的本地输入依赖完整，没有外部 `includegraphics` 文件。图形使用原生 TikZ、tikz-cd、CD 或数学 array。第 001–003 篇共用包根与 `source_catalog` 中的 Apache-2.0 许可证，其余篇另有篇内许可证。详见 `dependency_inventory.json` 与 `recovery_evidence/translation_archive_integrity.json`。

## 已包含什么

`vendor/texmf` 收入未经改写的 ctex、xeCJK、zhnumber、Fandol 字体及相应文档和许可证。文件来自 Debian 官方 `texlive-lang-chinese` 和 `texlive-lang-cjk` 的 `2024.20250309-1` 软件包；下载地址、软件包 SHA256、逐文件 SHA256 和包内原路径记在 `vendor/resource_provenance.json`。另附 LaTeX 项目官方 LPPL 1.3c 文本。Fandol 的 GPL 及字体例外全文见 `vendor/texmf/doc/fonts/fandol/COPYING.gz`，字体说明见同目录 `README`。这些第三方资源遵循各自许可证，不改标为本项目的 Apache-2.0。

不包含整套 TeX Live、系统二进制或可跨机器直接复用的 `.fmt` 格式文件。`runtime/` 是本机生成物，重新编译仍需主机具备 XeTeX、BibTeX 和标准 TeX 宏包。源文件与依赖清单使用项目相对路径；历史 QA 中记录的旧绝对路径仅用于溯源。

## 当前环境的实测结果

恢复环境为 Python 3.12.14、XeTeX 0.999996、BibTeX 0.99d，基础 LaTeX 内核为 2024-11-01 patch level 2。系统原有 `ls-R` 与 `fmtutil.cnf` 指向不存在的位置，且缺少中文资源及 XeLaTeX 格式；仅看到 `xelatex` 命令不代表可编译。

`portable_tex.py` 只为子进程设置私有 TEXMF 搜索路径及项目内缓存，不修改系统安装。它允许在文件名数据库失效时直接搜索发行版目录，并使用本包中文资源。`prepare` 首先尝试 `fmtutil-user`；若没有产生格式文件，则用系统原有、未经修改的 `xelatex.ini` 直接生成格式。当前环境缺少 `language.dat`，格式生成使用发行版 `hyphen.tex` 的英语断词回退；中文由 xeCJK 处理。没有对额外语言支持作出承诺。

本依赖审计实际在独立目录完成了第 018 篇的四轮 XeLaTeX 和一轮 BibTeX 编译：全部退出码为 0，27 页，最终无编译错误、未定义引用、缺字或溢出警告。记录见 `recovery_evidence/dependency_compile_0018.json`。该子审计未改写历史稿件、PDF、QA 或进度，其记录范围仍仅限第 018 篇。

随后，根代理通过可移植入口对第 001–018 篇全部完成了独立批量构建。`recovery_evidence/all_papers_rebuild_test.json` 记录 18 篇均返回 `built`、退出码为 0、最终诊断列表为空；每篇页数与历史交付一致，合计 1118 页。253 个历史译稿文件和全部历史交付 PDF 均未改写。这是本次真实执行的完整构建测试，不是从第 018 篇子审计推断的结果。

重新生成的 PDF 可能因元数据或 TeX 版本不同而具有不同哈希；重新编译成功不等于重新完成逐句语义审校或逐页视觉审校。历史交付 PDF 及其原检查记录继续保留。

## 新机器上的操作

在已安装 TeX Live 的机器上，先在工程根目录运行：

```bash
python portable_tex.py prepare
python resume.py doctor
```

只有 doctor 确认关键二进制、宏包、字体和格式文件可用后再构建：

```bash
python resume.py build 0018
```

新构建写入 `runtime/build/`，不覆盖历史译稿目录。第 002 篇的工作目录为 `math_translation/translated/0002/build/`；其余入口和所需宏包均列在依赖清单中，由 resume 入口处理。

若主机尚未安装 TeX，需先安装正常、版本一致的 TeX Live（或兼容发行版），至少具备 XeTeX/BibTeX、AMS 宏包、mathtools、geometry、hyperref、microtype、enumitem、booktabs/array/longtable/tabularx、natbib、tocbibind、cleveref、TikZ/tikz-cd、mathrsfs、xurl 等清单所列包。Debian 系可参考 `texlive-xetex`、`texlive-latex-recommended`、`texlive-latex-extra`、`texlive-science`、`texlive-fonts-recommended`；本包已附中文资源，亦可由主机的 `texlive-lang-chinese` 提供。该安装命令未在本无管理员权限的恢复环境执行，不应把包名建议当作每个系统上都已测试的安装方案。

常规检查和续作定位只需 Python 标准库。若要运行 PDF 渲染/合并辅助脚本，再安装本次已使用的依赖：

```bash
python -m pip install -r requirements-render.txt
```

不建议直接运行历史 `complete_*_package.py` 或 `record_*_delivery.py`：它们记录当时的单篇交付流程和旧外部存储状态，可能写入历史进度。续作应从 `resume.py status`、`resume.py next` 和交接说明开始。
