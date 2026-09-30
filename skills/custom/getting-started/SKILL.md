---
name: getting-started
description: Getting started guide and overview for officeqa agents and capabilities.
tags: [getting-started, overview]
version: "1.0"
author: ""
---

# Getting Started with officeqa

## Overview

This project uses genai-tk and genai-graph for AI agent capabilities over government documents
and U.S. Treasury Bulletins. This skill gives agents an overview of the project's tools and capabilities.

## Available Tools

- **calculator** — evaluate arithmetic and Python code
- **document graph tools** — `get_folder_toc`, `get_document_toc`, `get_section_content`, `search_sections`
- Add your own in `officeqa/tools/`

## Available Agent Profiles

Run `cli agents list` to see configured profiles.

## Workflow

1. Check `config/agents.yaml` for available profiles
2. Use `cli agents run <profile> --chat` to start a session
3. Tools are automatically available based on the profile configuration

## Adding New Capabilities

See `docs/EXTENDING.md` for how to add tools, commands, and agent profiles.
For skills management: `docs/SKILLS.md`
