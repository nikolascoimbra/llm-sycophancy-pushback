.PHONY: help sync test lint eligible distractors infer grade confirmatory exploratory tag-prereg clean

help:
	@echo "Targets:"
	@echo "  sync          - uv sync --all-extras"
	@echo "  test          - run pytest"
	@echo "  lint          - run ruff"
	@echo "  eligible      - filter calibration cache for eligible questions"
	@echo "  distractors   - generate distractor pool (cheap, ~\$0.10)"
	@echo "  infer         - run pushback inference (~\$10, hard cap \$13 reserving \$2 for grading)"
	@echo "  grade         - grade second-turn answers with Claude Haiku 4.5"
	@echo "  confirmatory  - run H1-H5 scripts (gated on prereg-v0 tag)"
	@echo "  exploratory   - run E1-E3 scripts"
	@echo "  tag-prereg    - create prereg-v0 git tag (one-way; review prereg first)"
	@echo "  clean         - remove derived data and figures"

sync:
	uv sync --all-extras

test:
	uv run pytest -q

lint:
	uv run ruff check .

eligible:
	uv run python scripts/00_select_eligible.py

distractors:
	uv run python scripts/01_generate_distractors.py

infer:
	uv run python scripts/02_pushback_inference.py

grade:
	uv run python scripts/03_grade.py

confirmatory:
	uv run python scripts/analyses/H1_cross_provider.py
	uv run python scripts/analyses/H2_asymmetry.py
	uv run python scripts/analyses/H3_politeness.py
	uv run python scripts/analyses/H4_assertiveness.py
	uv run python scripts/analyses/H5_calibration_sycophancy.py

exploratory:
	uv run python scripts/analyses/E1_acceptance.py
	uv run python scripts/analyses/E2_topic.py
	uv run python scripts/analyses/E3_qualitative.py

tag-prereg:
	@if git rev-parse prereg-v0 >/dev/null 2>&1; then \
		echo "Tag prereg-v0 already exists - refusing to retag."; exit 1; \
	fi
	git tag prereg-v0 -m "Pre-registration freeze for sycophancy study"
	@echo "Tagged prereg-v0. The H1-H5 scripts can now run."

clean:
	rm -rf data/processed/ figures/*.png figures/*.pdf
