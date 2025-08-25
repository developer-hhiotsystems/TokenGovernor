# TokenGovernor

A standalone governance system for agentic coding workflows that manages token usage, enforces priorities, requests checkpoints, and schedules task resumption.

## Overview

TokenGovernor integrates with external systems (LangChain, AutoGen) via APIs, using Claude-Code for code generation, Claude-Flow for workflow orchestration with deep inspection, and `ccusage` for token tracking.

## Key Features

- **Hierarchical Monitoring**: Project → Agent → Task → Optional Subtasks
- **Token Budget Enforcement** with heuristics and `ccusage`
- **Checkpoint Management** for task safety
- **Scheduler** for paused tasks/packages
- **Status Reporting** via CLI, API, and dashboard
- **GitHub-based Change Management** with PR process
- **Claude-Flow Orchestration** with dynamic agent allocation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize project
token-gov init --inspect

# Register a project
token-gov register --id <uuid> --budget <int>

# Check status
token-gov status --ccusage
```

## Development Phases

- **Phase 0**: GitHub Setup and Change Management (Current)
- **Phase 1**: Core Governance and CLI
- **Phase 2**: Dashboard and Simulations  
- **Phase 3**: Optimizations and Scalability

## Architecture

See `docs/architecture.md` for detailed system design.

## Contributing

All changes must go through the PR process. See `.github/pull_request_template.md` for guidelines.