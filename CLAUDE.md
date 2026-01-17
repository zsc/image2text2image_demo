方法一（json-only）：以下面提示词实现“图到文”

请以json结构化数据的形式提取这张图片，将图片中所有可见信息以结构化文本的形式提取。
然后直接塞给文到图

方法二（json + SVG）：

请以json结构化数据的形式提取这张图片，将图片中所有可见信息以结构化文本的形式提取。然后再将图片细细转作 SVG。
再

根据以上 json 和 svg（来自同一个图片），生成图片（宽高与 SVG 一致）

---
把以上整理为 Makefile。复杂操作用 python，比如生图脚本用 https://ai.google.dev/gemini-api/docs/image-generation 提取的信息进进封装；又比如当一次的生成结果有两种时，可能用 regex 提取。
整体流程是：输入图片 -> json/svg -> 包含两种重建图片和原始图片对比的 html
