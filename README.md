# Image to Text to Image Demo

这是一个基于 Google Gemini API 的“图生文生图”演示项目。它展示了如何通过不同的中间表示（JSON 数据或 SVG 代码）将图像转换为文本，然后再利用这些文本信息重建图像。

## 项目结构

该项目包含两个主要的重建路径，用于对比不同中间信息的提取效果：

1.  **方法一 (JSON-only)**:
    *   **提取**: 利用 Gemini Vision 模型将输入图片中的可见信息提取为结构化的 JSON 文本。
    *   **生成**: 将提取的 JSON 文本作为提示词，再次输入给图像生成模型 (Imagen) 进行重建。

2.  **方法二 (JSON + SVG)**:
    *   **提取**: 除了提取结构化 JSON 信息外，还要求模型将图像细节转换为 SVG 代码。
    *   **生成**: 将 JSON 和 SVG 代码共同作为提示词进行图像重建。

最终结果会生成一个 HTML 报告，直观地对比原始图片与两种方法生成的图片。

## 环境要求

*   Python 3.8+
*   Google Gemini API Key (需要支持 Gemini 1.5 Flash/Pro 和 Imagen 3 模型)

## 安装

1.  克隆或下载本项目。
2.  安装 Python 依赖：

    ```bash
    make install
    ```

## 配置 API Key

在使用之前，必须设置环境变量 `GEMINI_API_KEY`：

```bash
export GEMINI_API_KEY="你的_GOOGLE_GEMINI_API_KEY"
```

*(建议将其添加到你的 shell 配置文件中，如 `.zshrc` or `.bashrc`)*

## 使用方法

本项目使用 `Makefile` 来管理整个工作流。

### 1. 运行默认测试

项目自带了一个生成的测试图片 (`test_image.jpg`)。直接运行以下命令即可体验全流程：

```bash
make run
```

### 2. 使用自定义图片

要处理你自己的图片，请使用 `INPUT` 变量指定文件路径：

```bash
make run INPUT=my_photo.jpg
```

### 3. 批量处理目录 (Batch)

要一次性处理一个目录下的所有图片（支持 jpg, png, webp 等）：

```bash
# 处理默认目录 (images/)
make batch

# 处理指定目录
make batch INPUT_DIR=/path/to/my_images OUTPUT_DIR=my_batch_output
```

生成的报告索引将位于输出目录的 `index.html`。

### 4. 清理输出

清理生成的 `output/` 和 `output_batch/` 目录：

```bash
make clean
```

### 4. 查看帮助

查看所有可用命令：

```bash
make help
```

## 输出结果

流程运行完成后，所有结果将保存在 `output/` 目录下：

*   `output/report.html`: **最终报告**，包含原图、两种方法的重建图以及提取的中间文本。请在浏览器中打开此文件。
*   `output/analysis_json.txt`: 方法一提取的文本。
*   `output/analysis_svg.txt`: 方法二提取的文本。
*   `output/reconstructed_json.png`: 方法一生成的图片。
*   `output/reconstructed_svg.png`: 方法二生成的图片。

## 文件说明

*   `process_image.py`: 核心 Python 脚本，负责调用 Gemini API 进行分析和绘图，以及生成 HTML 报告。
*   `Makefile`: 自动化脚本，串联分析、生成和报告生成的各个步骤。
*   `requirements.txt`: Python 依赖列表。
