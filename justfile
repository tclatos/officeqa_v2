# Justfile for officeqa
# Run `just` to see available recipes.

# Default recipe — show help
default:
    @just --list

# ── Development ─────────────────────────────────────────────────────────────

# Install / sync dependencies
sync:
    uv sync

# Format code with ruff
fmt:
    uv run ruff format .

# Lint code with ruff
lint:
    uv run ruff check .
    uv run cli skills validate --all || true

# Format + lint
check: fmt lint

# Run tests
test:
    uv run pytest tests/ -v

# Run unit tests only
test-unit:
    uv run pytest tests/unit_tests/ -v

# ── Skills ───────────────────────────────────────────────────────────────────

# List all available skills
skills:
    uv run cli skills list

# Add a skill by name (bundled)
add-skill name:
    uv run cli skills add {{name}}

# Validate all skills
lint-skills:
    uv run cli skills validate --all

# ── Web Interface ────────────────────────────────────────────────────────────

# Launch Streamlit webapp (entry point discovered from genai-tk package)
webapp:
    entry=$(uv run python -c 'import pathlib, genai_tk; print(pathlib.Path(genai_tk.__file__).parent / "webapp/main/streamlit.py")') && uv run python -m streamlit run "$entry"

# ── Project-specific ─────────────────────────────────────────────────────────

# Launch agent chat
run:
    uv run cli agent chat

# ── FinanceBench bench harness ─────────────────────────────────────────────────

# Install deps incl. the harnessing extra (DeepAgents SDK) needed for the deep agent
bench-setup:
    uv sync --extra harnessing

# Full benchmark run via CLI
bench:
    uv run cli bench run

# Benchmark run skipping PDF fetch (for already downloaded filings)
bench-multi:
    uv run cli bench run --skip fetch

bench-fetch:
    uv run cli bench run --step fetch

bench-build:
    uv run cli bench run --step build

bench-run:
    uv run cli bench run --step run

bench-grade:
    uv run cli bench run --step grade


