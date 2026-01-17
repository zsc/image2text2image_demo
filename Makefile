# 图生文生图 (Image-to-Text-to-Image) 流程 Makefile

PYTHON := python
PIP := $(PYTHON) -m pip
SCRIPT := process_image.py

# 默认输入图片 (可以通过命令覆盖: make run INPUT=my_image.jpg)
INPUT ?= test_image.jpg

# 输出目录
OUT_DIR := output
# 确保输出目录存在
$(shell mkdir -p $(OUT_DIR))

# 中间文件定义
JSON_TEXT := $(OUT_DIR)/analysis_json.txt
SVG_TEXT := $(OUT_DIR)/analysis_svg.txt
JSON_IMG := $(OUT_DIR)/reconstructed_json.png
SVG_IMG := $(OUT_DIR)/reconstructed_svg.png
REPORT := $(OUT_DIR)/report.html

.PHONY: all help install clean run

all: run

help:
	@echo "用法:"
	@echo "  make install         安装依赖"
	@echo "  make run             使用默认图片 ($(INPUT)) 运行流程"
	@echo "  make run INPUT=x.jpg 使用指定图片运行流程"
	@echo "  make clean           清理输出目录"

install:
	$(PIP) install -r requirements.txt

# 运行完整流程
run: $(REPORT)
	@echo "流程完成。请查看报告: $(REPORT)"

# 步骤 1: 分析图片 (JSON 方法)
$(JSON_TEXT): $(INPUT)
	@echo "正在分析图片 (JSON 方法)..."
	$(PYTHON) $(SCRIPT) analyze $(INPUT) --method json --output-text $@

# 步骤 2: 分析图片 (JSON + SVG 方法)
$(SVG_TEXT): $(INPUT)
	@echo "正在分析图片 (JSON+SVG 方法)..."
	$(PYTHON) $(SCRIPT) analyze $(INPUT) --method json_svg --output-text $@

# 步骤 3: 根据 JSON 分析结果生成图片
$(JSON_IMG): $(JSON_TEXT)
	@echo "正在根据 JSON 分析结果生成图片..."
	$(PYTHON) $(SCRIPT) generate $(JSON_TEXT) $@

# 步骤 4: 根据 SVG 分析结果生成图片
$(SVG_IMG): $(SVG_TEXT)
	@echo "正在根据 SVG 分析结果生成图片..."
	$(PYTHON) $(SCRIPT) generate $(SVG_TEXT) $@

# 步骤 5: 生成 HTML 报告
$(REPORT): $(JSON_IMG) $(SVG_IMG)
	@echo "正在生成 HTML 报告..."
	$(PYTHON) $(SCRIPT) report \
		--original $(INPUT) \
		--json-img $(JSON_IMG) \
		--svg-img $(SVG_IMG) \
		--json-text $(JSON_TEXT) \
		--svg-text $(SVG_TEXT) \
		--output $@

clean:
	rm -rf $(OUT_DIR)