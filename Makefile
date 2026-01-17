# Makefile for Image to Text to Image pipeline

PYTHON := python
PIP := $(PYTHON) -m pip
SCRIPT := process_image.py

# Default input image (can be overridden: make run input=my_image.jpg)
INPUT ?= test_image.jpg

# Output directory
OUT_DIR := output
# Ensure output dir exists
$(shell mkdir -p $(OUT_DIR))

# Intermediate files
JSON_TEXT := $(OUT_DIR)/analysis_json.txt
SVG_TEXT := $(OUT_DIR)/analysis_svg.txt
JSON_IMG := $(OUT_DIR)/reconstructed_json.png
SVG_IMG := $(OUT_DIR)/reconstructed_svg.png
REPORT := $(OUT_DIR)/report.html

.PHONY: all help install clean run

all: run

help:
	@echo "Usage:"
	@echo "  make install         Install dependencies"
	@echo "  make run             Run pipeline on default image ($(INPUT))"
	@echo "  make run INPUT=x.jpg Run pipeline on specific image"
	@echo "  make clean           Remove output directory"

install:
	$(PIP) install -r requirements.txt

# Run the full pipeline
run: $(REPORT)
	@echo "Pipeline complete. View report at $(REPORT)"

# Step 1: Analyze image (JSON Method)
$(JSON_TEXT): $(INPUT)
	@echo "Analyzing image (JSON method)"
	$(PYTHON) $(SCRIPT) analyze $(INPUT) --method json --output-text $@

# Step 2: Analyze image (JSON + SVG Method)
$(SVG_TEXT): $(INPUT)
	@echo "Analyzing image (JSON+SVG method)"
	$(PYTHON) $(SCRIPT) analyze $(INPUT) --method json_svg --output-text $@

# Step 3: Generate Image from JSON analysis
$(JSON_IMG): $(JSON_TEXT)
	@echo "Generating image from JSON analysis"
	$(PYTHON) $(SCRIPT) generate $(JSON_TEXT) $@

# Step 4: Generate Image from SVG analysis
$(SVG_IMG): $(SVG_TEXT)
	@echo "Generating image from SVG analysis"
	$(PYTHON) $(SCRIPT) generate $(SVG_TEXT) $@

# Step 5: Generate HTML Report
$(REPORT): $(JSON_IMG) $(SVG_IMG)
	@echo "Generating HTML report"
	$(PYTHON) $(SCRIPT) report \
		--original $(INPUT) \
		--json-img $(JSON_IMG) \
		--svg-img $(SVG_IMG) \
		--json-text $(JSON_TEXT) \
		--svg-text $(SVG_TEXT) \
		--output $@

clean:
	rm -rf $(OUT_DIR)
