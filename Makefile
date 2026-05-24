.PHONY: help sync test lint \
        eligible distractors infer grade confirmatory exploratory tag-prereg \
        v1-canonical v1-eligibility v1-inference v1-grade v1-assemble \
        v1-confirmatory v1-figures tag-prereg-v1 \
        paper clean

help:
	@echo "Targets:"
	@echo ""
	@echo "  Top-level:"
	@echo "    sync             - uv sync --all-extras"
	@echo "    test             - run pytest"
	@echo "    lint             - run ruff"
	@echo "    paper            - build paper/main.pdf (requires tectonic)"
	@echo "    clean            - remove derived data and figures"
	@echo ""
	@echo "  Study 1 (prereg-v0; bare-API panel):"
	@echo "    eligible         - filter calibration cache for eligible questions"
	@echo "    distractors      - generate distractor pool (~\$$0.10)"
	@echo "    infer            - run pushback inference (~\$$10, cap \$$13)"
	@echo "    grade            - grade second-turn answers with Claude Haiku 4.5"
	@echo "    confirmatory     - run H1-H5 (gated on prereg-v0 tag)"
	@echo "    exploratory      - run E2/E4 + R2 robustness"
	@echo "    tag-prereg       - create prereg-v0 git tag"
	@echo ""
	@echo "  Study 2 (prereg-v1; G x C x P factorial):"
	@echo "    v1-canonical     - turn-1 canonical (BV cell, 4 direct-API providers x 500 SimpleQA)"
	@echo "    v1-eligibility   - compute eligible_questions_v1.parquet"
	@echo "    v1-inference     - non-canonical turn-1 + turn-2 (all 8 cells; ~\$$13)"
	@echo "    v1-grade         - grade v1 turn-1 + turn-2"
	@echo "    v1-assemble      - build sycophancy_final_v1.parquet"
	@echo "    v1-confirmatory  - run H6-H8 (gated on prereg-v1 tag)"
	@echo "    v1-figures       - render F4/F5/F6"
	@echo "    tag-prereg-v1    - create prereg-v1 git tag"

sync:
	uv sync --all-extras

test:
	uv run pytest -q

lint:
	uv run ruff check .

# -------- Study 1 (prereg-v0) --------

eligible:
	uv run python scripts/00_select_eligible.py

distractors:
	uv run python scripts/01_generate_distractors.py

infer:
	uv run python scripts/02_pushback_inference.py

grade:
	uv run python scripts/03_grade.py --workers 8

confirmatory:
	uv run python scripts/analyses/H1_cross_provider.py
	uv run python scripts/analyses/H2_asymmetry.py
	uv run python scripts/analyses/H3_politeness.py
	uv run python scripts/analyses/H4_assertiveness.py
	uv run python scripts/analyses/H5_calibration_sycophancy.py

exploratory:
	uv run python scripts/analyses/E2_topic.py
	uv run python scripts/analyses/E4_extended_panel.py
	uv run python scripts/analyses/R2_grader_validation.py

tag-prereg:
	@if git rev-parse prereg-v0 >/dev/null 2>&1; then \
		echo "Tag prereg-v0 already exists - refusing to retag."; exit 1; \
	fi
	git tag prereg-v0 -m "Pre-registration freeze for sycophancy study (Study 1)"
	@echo "Tagged prereg-v0. The H1-H5 scripts can now run."

# -------- Study 2 (prereg-v1) --------

v1-canonical:
	uv run python scripts/v1_01_inference.py --stage turn1_canonical --workers 8

v1-eligibility:
	uv run python scripts/v1_02_eligibility.py

v1-inference: v1-canonical v1-eligibility
	bash scripts/v1_pipeline.sh

v1-grade:
	uv run python scripts/v1_03_grade.py --stage all --workers 8

v1-assemble:
	uv run python scripts/v1_04_assemble.py

v1-confirmatory:
	uv run python scripts/analyses/H6_grounding_main.py
	uv run python scripts/analyses/H7_format_main.py
	uv run python scripts/analyses/H8_grounding_format_interaction.py

v1-figures:
	uv run python scripts/v1_05_figures.py

tag-prereg-v1:
	@if git rev-parse prereg-v1 >/dev/null 2>&1; then \
		echo "Tag prereg-v1 already exists - refusing to retag."; exit 1; \
	fi
	git tag prereg-v1 -m "Pre-registration freeze for sycophancy study (Study 2 factorial)"
	@echo "Tagged prereg-v1. The H6-H8 scripts can now run."

# -------- Paper + cleanup --------

paper:
	cd paper && tectonic main.tex

clean:
	rm -rf data/processed/sycophancy_final*.parquet figures/*.png figures/*.pdf
	rm -f paper/main.pdf paper/main.aux paper/main.bbl paper/main.blg paper/main.log
