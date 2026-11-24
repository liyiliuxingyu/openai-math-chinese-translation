OpenAI math 全文中文翻译工程：接续说明
交接日期：2026-11-19

这是可供新对话接续的现行工程包。请先阅读本文件和 handoff_state.json，再校验文件与状态；不要依赖此前对话的隐含记忆。

一、当前准确状态
固定仓库：https://github.com/openai/math
固定提交：4eaee87548250b2682affda7d05d947c05554bae（目录记录提交日期 2026-10-30）。
现行目录 721 篇论文，分属 373 个成果族；完成第 001–018 篇，剩余 703 篇。18 篇中文单篇共 1118 页，最新合订本也是 1118 页。数字 721 是现行目录稿件数，既不是成果族数，也不表示全部原稿都已下载。存档/撤回版本、图形 PDF 的范围口径见 math_translation/scope_audit/。
本包的恢复基线依据为 math_translation/progress.json 及对应已保存进度第 15 版。本轮不更新远端进度；下一轮发布前须读取当时最新进度版本并核对，不能把第 15 版当作永远有效的当前版本。完整目录为 math_translation/source_catalog/catalog.json。目录保持原始当前状态，前 18 项 complete，第 19 项 pending。
下一篇：第 019 篇 The Dimension of the Two-Adic Hecke Algebra at Odd Level。此前续译用名为“奇数级 2 进 Hecke 代数的维数”；catalog 尚无中文标题字段，中文正文尚未开始。本轮已把固定提交的 README、main.tex、references.bib、原 PDF 共 4 个文件备齐并校验 Git blob，仅准备原稿不算开始或完成翻译。
第 019 篇仓库目录：preprints/The-Dimension-of-the-Two-Adic-Hecke-Algebra-at-Odd-Level-October-5-2026
本地原稿：math_translation/original/0019/build/main.tex；书目：同目录 references.bib；原 PDF：math_translation/original/0019/two-adic-hecke.pdf。

二、新对话开始时的操作顺序
1. 将完整工程包解压到可写目录，进入包含本文件、handoff_state.json、resume.py、verify_project.py 的包根目录。路径与解压位置无关；不要依赖旧工作区绝对路径。
2. 先读 handoff_state.json、recovery_evidence/recovery_report.json；需要回溯具体稿件时再读该篇的 qa 和原文。
3. 依次运行以下只读命令，保存或报告实际结果：
   python verify_project.py --manifest project_manifest.json --json
   python resume.py status --json
   python resume.py next --json
   python resume.py doctor --json
   verify 的成功表示清单及规定引用检查通过，不表示重新审过数学证明。status/next 展示接续状态；doctor 检查依赖，不自行下载安装。脚本退出码：0 成功，1 检查/完整性错误，2 输入/用法错误。以脚本 --help 为准。
4. 首次接续只校验已有 project_manifest.json，不运行 --create-manifest 来重置基线。若有缺失、哈希不符或字段冲突，先定位具体文件和恢复证据；不要静默覆盖清单、放宽检查器或把错误状态改为 pass。可继续处理不依赖该问题的工作。
5. 核对第 019 篇条目与 4 个原稿文件，然后从完整阅读原文开始翻译。不能把当前远端 main 的目录或源文件直接代入固定提交，不能将准备好的英文文件当作已译中文。

三、工程内的主要位置
包根 handoff_state.json：可移植的接续状态、18 篇实际入口及 PDF、下一篇原稿信息和相对路径。
包根 project_manifest.json：最终打包文件的完整性清单；verify_project.py 用它校验。
包根 resume.py / verify_project.py：本轮新增的可移植接续/校验脚本。
recovery_evidence/delivery_registry.json：根据历史 publication_manifest 和本轮元数据重建的交付身份登记，明确标记 recovered；它不是缺失原上传回执的替代证明。旧包未含 saved_deliverables.json 或原始上传回执，不应伪造成功回执。
包根 dependency_inventory.json、DEPENDENCIES.md：本轮实际环境、资源、许可与重建说明；编译能力以该报告与当次 doctor 的实际结果为准。requirements-render.txt 列出渲染/合并依赖；仅运行 status/next/verify 不需要这些额外 Python 包。
math_translation/original/0001–0019/：已完成 18 篇及下一篇的原始文件，原稿数学保持不改。
math_translation/translated/0001–0018/：现行完整中文 TeX、书目及许可。不同篇入口可能为 main.tex、paper.tex 或 build/main.tex，不要凭文件名猜测；以 handoff_state.json 每条 entrypoint 为准。
math_translation/qa/0001–0018/：各轮作者自校、独立语义审校、公式文字映射、图形/书目核验、编译及视觉审阅等历史证据。报告格式因轮次不同可能有差异；应检查其明确的范围和 SHA。
math_translation/source_catalog/、scope_audit/：固定目录与范围核对。
math_translation/scripts/ 及其他保留脚本：原检查器、翻译辅助、编译、渲染和汇总脚本。旧脚本/报告可能记录当时绝对路径，未因迁移逐个改写；正常接续入口为包根 resume.py，不盲目执行旧脚本。尤其 finalize/complete/record 脚本属于历史批次，可能写死旧计数、旧路径或回执位置；第 019 篇发布需按实际新状态适配，不能直接重放旧批次。
output/：18 份最终单篇 PDF、最新合订本以及已保存进度快照。
recovery_evidence/：归档来源、解包与去重记录、补取原稿、逐稿库存及本轮字节校验。
historical/：有保留价值的旧脚本和第 010 篇部分译稿等历史材料，不作为现行完成版本。
现行原稿、译稿、书目和许可均保留。本包按现行续作需要恢复并去重；并不冒称所有运行缓存或每个旧累积 PDF 都原样重存。旧第 001–003 篇累积 PDF、已被完整第 010 篇替代的部分 PDF 等明确排除项，逐项见 recovery_report.json；旧脚本版本选择也在该报告中记录。

四、必须区分的三种证据
历史状态与审校范围：固定目录将前 18 篇记为 complete；本包保留这一历史状态，不擅自重写进度。各篇实际留下的审校方法与覆盖范围并不完全相同，不能笼统说前 18 篇都做过同等完整的独立逐句语义审校及逐张全尺寸目视。具体以各篇报告明确的范围与 SHA 为准。
已知早期限制：qa/0001、0002、0003/validation.json 明确记录“全部页面通过渲染联系表检查，并对标题、数学展示式、图与参考文献等作全尺寸检查”；这不等同于后期每张整页图都实际打开的流程。qa/0002/prose_review.json 的独立逐段对照只覆盖第 06–10 节，共 286 段，并明确未审第 01–05 节；不能把该报告外推为全篇独立语义覆盖。本轮不追认或补造早期未记录的覆盖。
这些历史记录仅对应其绑定版本，不能改写成新对话刚完成的审校；后续翻译采用下述完整审校标准，不意味着这些标准已在每个早期版本同等执行。
本轮恢复校验：恢复报告记录 001–018 共 216 个原文件及 019 的 4 个原文件，合计 220 个文件与固定提交 Git blob 一致；18 个中文单篇 PDF 和 1118 页合订本 SHA256 与历史保存版本一致。原第 001 篇 README 在旧包中缺失，本轮从同一固定提交补回；019 原稿也是本轮补取。完整文件清单、数量和逐文件证据均见 recovery_evidence/。
数学证明正确性：历史翻译审校与本轮恢复核验均不构成对原论文定理的独立证明验证。本轮没有重新逐句审译全部 18 篇，也没有重新逐页看完全部 1118 页。不能把哈希一致、编译通过或译文忠实称为证明原结论成立。

五、环境与重建
已保存 PDF 可直接阅读，无需先重建。历史上成功编译不保证新解压环境立即具备相同 TeX 宏包、字体或格式文件。请查看 dependency_inventory.json 和当次 doctor；资源路径与版本以实际盘点为准。
本轮环境初探发现 TeX 文件数据库断链、中文宏包/字体和 xelatex.fmt 不齐。现已把 ctex、xeCJK、zhnumber、Fandol 及许可随包放入 vendor/texmf；portable_tex.py 提供本机格式文件准备与环境配置。私有环境已解析 18 篇实际使用的 TeX 依赖，253 个现行译稿文件也已匹配历史包哈希；其后全部 18 篇实际隔离重编也已通过，独立报告见下。依赖解析与实际构建分别保留证据。包内不含整套 TeX Live、系统二进制或可跨机器复用的格式文件；需要主机提供的 TeX 二进制和基础资源以 dependency_inventory.json 为准。可用 python portable_tex.py prepare 准备本机格式文件，不覆盖原稿或历史 PDF。
本轮已实际对恢复的第 018 篇执行隔离构建：4 轮 XeLaTeX + 1 轮 BibTeX 全部 exit0，最终 diagnostics=[]，输出 27 页，输入源文件保持不变。详细证据为 recovery_evidence/dependency_compile_0018.json，测试输出为 runtime/dependency_probe/0018/main.pdf；它不替代 output/ 中已审校的历史最终 PDF，也不是新一轮语义/视觉审校。其后还已对第 001–018 篇逐篇完成整批隔离重编：18 份均 result=built、exit0、diagnostics=[]，failed=[]；每篇新 PDF 页数与历史一致，合计 1118 页；253 个现行源文件及全部 18 个历史 PDF 均未改。报告为 recovery_evidence/all_papers_rebuild_test.json，SHA256：e717c98ebb1b3f0f67d1c6f78cf1a909bc7baf9bf54566980277c0222658c35e。此结论只说明本轮所测私有环境能够重建全部现行译稿，不等于新一轮逐句语义、逐页视觉或独立数学证明审校，也不承诺任意新机器无需依赖准备即可构建。
需要再次批测时，tools/rebuild_all.py 使用 PyMuPDF 并调用可移植构建入口，仅把测试输出写入 runtime；它不更新历史报告或进度。先运行 prepare 和 doctor，明确需要整批复测后再执行 python tools/rebuild_all.py --run。该工具要求显式 --run 才运行；--help 仅显示帮助，未带 --run 不执行构建，可用 --jobs 1..4 控制并发。
如确需复编已完成稿件，依赖满足后可执行：
   python resume.py build 0018
默认输出到 runtime/build/0018，原译稿、已保存 PDF 和历史 QA 保持基线。build 只重建已完成稿件，不会翻译第 019 篇、不更新完成进度，也不替代新的语义或视觉审校。个别稿件有专用脚本和入口，先查记录及脚本帮助。
迁移测试也已实际执行：把脚本、译稿和私有 TeX 资源复制到带空格的新目录，从工程目录外调用 resume.py build 0016，四轮 XeLaTeX 加一次 BibTeX 成功，得到 11 页、零诊断，10 个该篇源文件字节保持一致。报告为 recovery_evidence/portable_relocation_smoke.json。该测试只证明本轮所测迁移与构建路径可行，不证明任意新机器已具备依赖，亦未替代历史 PDF 或开展新的语义/视觉审校。
重新编译产生的 PDF 即使内容等价，其文件 SHA 也可能变化；应把新构建结果和诊断另存，不能用新哈希倒写历史实看记录。

六、继续翻译时保持的工作标准
按固定目录依序继续。每篇先确认完整原文件与 Git blob/哈希，再完整阅读主文和相关定义；作者自校与独立审校分开记录，避免将一个角色的自校称为独立审查。
全文翻译所有标题、摘要、正文、定义、定理、证明、附录、图表标签/说明和参考文献题名；保留作者、出版信息及原题来源。不得用摘要替代证明，不能省略否定、量词、常数依赖、参数次序或适用范围。发现疑似原文数学问题，应忠实保留并单独报告，不能默改原稿或补造论证。
数学符号、公式、编号、环境、label/ref/eqref/cite/URL 和原生图几何结构保持。公式中的自然语言要译；每个允许的文字变化须记录完整含定界符的源公式与译公式、精确替换片段和次数，能精确逆向核对。图中文字翻译同样保留完整原/译图代码及几何一致证据。
公共检查器 math_translation/scripts/check_translation.py 不可为通过结果而修改。当前 SHA256：53893b8ffd2c1562a27d886cec21e25944f357139184ae04663285dbd4eca7b0。公共结构核验之外，按稿件记录精确公式逆映射、锚点及环境检查；说明所有预期差异，不笼统声称未经处理的数学字节完全一致。
术语先读本篇 qa 中的 terminology 文件及已有共享术语，再按数学语境统一。不能机械沿用同词不同义：例如特征/特征标、行列式/行列式律、一般/泛、整序/顺序、差理想/不同、单位特征根/有限阶单位根、完备化/补全等。
独立审校须实际逐句对照全部原文和译文、每个证明与环境外论证，绑定最终源译 SHA、完整行/证明覆盖、修订及未解决项；结构相等不能替代语义通读。
排版使用现行中文 TeX 习惯，保留许可和明确修改说明。成功编译后按最终 PDF 渲染逐页实际查看，核对中文/数学字形、长公式、图、引用、书目、边界、换页与短尾行。不能用文本提取、联系表或无警告日志冒充逐页实看。
修改后只对 PNG 字节完全相同且已有真实实看证据的页继承记录，并注明原 PDF/PNG 哈希；变化页必须重新实际看。新报告绑定最终 PDF 和每页 PNG。
只有全文、独立审校、数学/引用检查、编译和逐页视觉检查均完成，才能把本篇标 complete 并更新目录、progress、单篇/合订本和交付清单。未完成内容明确标未完成，不能以英文源文件存在或部分翻译已写入充数。
本包不包含自动任务，也不承诺对话结束后后台继续。每轮在用户已授权范围内推进，并交付可核验的具体状态。

七、完成新工作后如何制作下一份续作包
首次解压/接续必须核验现有清单，不能重新生成清单以消除异常。只有在已完成新的授权工作、核对全部预期变化，并准备新的可交付快照时，才依次运行：
   python verify_project.py --create-manifest
   python verify_project.py --json
   python pack_project.py --output ../OpenAI_math_project.zip --json
第一条会显式创建/替换清单，因此不是日常验包步骤。第二条通过后才打包。pack_project.py 本身不重建清单，只归档 project_manifest.json 列出的文件和清单本身；ZIP 必须位于工程根外，包内固定顶层为 OpenAI_math_project，旁边生成同名 .zip.sha256。runtime、缓存与未列入清单的私有辅助文件不进入包，也不会自动联网或更新进度。
该打包入口的验证范围见 recovery_evidence/pack_tool_validation.json。新一轮新增的源稿/QA/文档应先完成检查再冻结清单，具体交付及保存操作按当时实际环境执行；不要假造旧上传回执。

八、已完成 18 篇清单（题名取自固定目录；页数为中文最终 PDF）
001 | 32 页 | 阿贝尔簇的 Milne 有理性猜想
      Milne's rationality conjecture for abelian varieties
      入口：math_translation/translated/0001/main.tex
      PDF：output/001_阿贝尔簇的Milne有理性猜想_中文全译.pdf
002 | 79 页 | 由低 Selmer 余秩推出精确的 Birch–Swinnerton-Dyer 公式
      Exact Birch–Swinnerton-Dyer Formula from Low Selmer Corank
      入口：math_translation/translated/0002/build/main.tex
      PDF：output/002_由低Selmer余秩推出精确BSD公式_中文全译.pdf
003 | 67 页 | 椭圆曲线在每个素数处的 Selmer 逆命题
      The Selmer converse for elliptic curves at every prime
      入口：math_translation/translated/0003/main.tex
      PDF：output/003_椭圆曲线在每个素数处的Selmer逆命题_中文全译.pdf
004 | 144 页 | Selmer 余秩至多为一时 Birch–Swinnerton-Dyer 公式的 2 部分
      The two-primary Birch–Swinnerton-Dyer formula in Selmer corank at most one
      入口：math_translation/translated/0004/paper.tex
      PDF：output/004_Selmer余秩至多为一时BSD公式的2部分_中文全译.pdf
005 | 191 页 | 准黎曼猜想：实部大于八分之七的无零点半平面
      The Quasi-Riemann Hypothesis: A Zero-Free Half-Plane $`\Re s\gt 7/8`$ 
      入口：math_translation/translated/0005/paper.tex
      PDF：output/005_准黎曼猜想_实部大于八分之七的无零点半平面_中文全译.pdf
006 | 50 页 | 准黎曼猜想：十二分之十一无零点半平面的另一种证明
      The Quasi-Riemann Hypothesis (alternate 11/12 proof)
      入口：math_translation/translated/0006/paper.tex
      PDF：output/006_准黎曼猜想_十二分之十一无零点半平面的另一种证明_中文全译.pdf
007 | 10 页 | Landau–Siegel 零点的一致排除
      Uniform exclusion of Landau–Siegel zeros
      入口：math_translation/translated/0007/paper.tex
      PDF：output/007_Landau-Siegel_零点的一致排除_中文全译.pdf
008 | 58 页 | 有理数域上的 Hilbert 第十问题
      Hilbert’s tenth problem over the rational numbers
      入口：math_translation/translated/0008/main.tex
      PDF：output/008_有理数域上的Hilbert第十问题_中文全译.pdf
009 | 84 页 | 具有有理二挠点的椭圆曲线的逐点 2-逆命题
      A pointwise 2-converse for elliptic curves with rational two-torsion
      入口：math_translation/translated/0009/paper.tex
      PDF：output/009_具有有理二挠点的椭圆曲线的逐点2-逆命题_中文全译.pdf
010 | 43 页 | Catalan 常数是无理数
      Catalan's constant is irrational
      入口：math_translation/translated/0010/main.tex
      PDF：output/010_Catalan常数是无理数_中文全译.pdf
011 | 113 页 | Goldfeld 的解析密度猜想与椭圆曲线的 2-逆命题
      Goldfeld's analytic density conjecture and the 2-converse for elliptic curves
      入口：math_translation/translated/0011/main.tex
      PDF：output/011_Goldfeld的解析密度猜想与椭圆曲线的2-逆命题_中文全译.pdf
012 | 39 页 | 椭圆曲线二次扭曲的平均解析秩
      The mean analytic rank of quadratic twists of elliptic curves
      入口：math_translation/translated/0012/main.tex
      PDF：output/012_椭圆曲线二次扭曲的平均解析秩_中文全译.pdf
013 | 77 页 | 积性函数的普通二点相关
      Ordinary two-point correlations of multiplicative functions
      入口：math_translation/translated/0013/main.tex
      PDF：output/013_积性函数的普通二点相关_中文全译.pdf
014 | 38 页 | Deligne–Drinfeld 猜想
      The Deligne-Drinfeld conjecture
      入口：math_translation/translated/0014/paper.tex
      PDF：output/014_Deligne-Drinfeld猜想_中文全译.pdf
015 | 31 页 | 由模ℓ Milnor K理论重构函数域
      Reconstruction of Function Fields from Mod-ℓ Milnor K-Theory
      入口：math_translation/translated/0015/main.tex
      PDF：output/015_由模ℓ_Milnor_K理论重构函数域_中文全译.pdf
016 | 11 页 | 由模特征的 Milnor K 理论重构
      Reconstruction from Milnor K-theory modulo the characteristic
      入口：math_translation/translated/0016/main.tex
      PDF：output/016_由模特征的Milnor_K理论重构_中文全译.pdf
017 | 24 页 | Bogomolov–Pop 重构定理
      The Bogomolov-Pop reconstruction theorem
      入口：math_translation/translated/0017/paper.tex
      PDF：output/017_Bogomolov-Pop重构定理_中文全译.pdf
018 | 27 页 | 素数 2 处的无限制 pro-模性
      Unrestricted pro-modularity at the prime two
      入口：math_translation/translated/0018/main.tex
      PDF：output/018_素数2处的无限制pro模性_中文全译.pdf

最新合订本：output/OpenAI_math_中文全译_第001至018篇_合订本.pdf
SHA256：52e728c82fcf3c234a25efdb0aa0aefe568db0c14be29d3cfef0b25cdbc489bf
