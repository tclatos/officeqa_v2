# officeqa_v2 — Agent Map

> Built with [genai-tk](https://github.com/tclatos/genai-tk) and [genai-graph](https://github.com/tclatos/genai-graph).  
> **Agents:** this is your entry point. Read top-to-bottom, then follow the pointers.

## Build Commands

```bash
uv sync              # install dependencies
cli bench run        # run OfficeQA Pro V2 benchmark
cli bench report     # view score summary
cli bench tui        # explore run trajectories in TUI
just test            # run tests
just lint            # ruff check
just fmt             # ruff format
```

## Project Structure

```
officeqa_v2/
  adapter.py        # OfficeQA Pro V2 dataset adapter (re-export)
  adapter_v2.py     # Dataset loader and Hugging Face resolver
  json_transformer.py # Layout-aware parsed JSON to Markdown transformer
  reward.py         # Databricks official reference reward function
  commands/         # CLI command groups
  tools/            # LangChain tools (calculator, etc.)
config/
  app_conf.yaml     # CLI commands registry, profile selection
  bench.yaml        # Benchmark execution profiles (dual scoring)
  docgraph.yaml     # Ladybug Knowledge Graph build profile
  agents.yaml       # Agent profiles (OfficeQA Pro V2 deep agent)
  providers/        # LLM and embeddings provider aliases
skills/
  custom/
    officeqa-v2-qa/ # Domain skill: historical conventions, TAS, multi-doc routing
    getting-started/# General navigation reference
data/
  jsons/            # Downloaded parsed JSON corpus (249 documents)
  saved_markdown/   # Structured Markdown documents
  kg/               # Ladybug Document Graph database (officeqa_v2.db)
```

## Architecture Invariants

1. **Pydantic v2** for all data models — never `dataclass`
2. **Absolute imports** only: `from officeqa_v2.commands import ...`
3. **uv** for all Python execution and package management
4. **Skills** for domain knowledge — read `officeqa-v2-qa` for corpus conventions
5. **Dual Evaluation** — official Databricks `reward.py` (0.0% tolerance exact match) + LLM-as-judge rubric diagnostics
