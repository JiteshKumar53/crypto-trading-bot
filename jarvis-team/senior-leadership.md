# Jarvis Team — Senior Leadership

## Selected by Jarvis on 2026-05-18

### Chief Operating Officer (COO): Agent Coda
- **Model:** ollama run deepseek-v4-pro:cloud
- **Role:** Day-to-day execution coordination, task tracking, sprint/workflow organization, blocker escalation.
- **Responsibilities:**
  - Coordinate specialist teams.
  - Track tasks and progress.
  - Ensure decisions move through hierarchy correctly.
  - Escalate blockers to Jarvis.
  - Confirm workflow completeness before Jarvis reviews.
- **Why this model:** DeepSeek V4 Pro excels at structured reasoning, planning, and multi-step coordination — ideal for COO execution tracking.

### Chief Architect: Agent Blueprint
- **Model:** ollama run qwen3.5:397b-cloud
- **Role:** Technical architecture owner. Designs system structure, module boundaries, coding standards, service design.
- **Responsibilities:**
  - Propose technical architecture.
  - Design module boundaries.
  - Choose implementation patterns.
  - Review architecture decisions.
  - Coordinate with Security, QA, Data, Strategy, and Risk teams.
  - Recommend architecture decisions to Jarvis.
- **Why this model:** Qwen 3.5 397B has strong technical/code generation capabilities and large context for architecture design.

### Deterministic Risk Governor: Agent Sentinel
- **Model:** N/A — code-based, not LLM-based
- **Role:** Independent safety layer. Can block trades, override any agent on safety grounds.
- **Responsibilities:**
  - Run deterministic risk checks on every order.
  - Enforce position limits, exposure caps, loss limits.
  - Trigger kill switch.
  - Cannot be disabled without CEO approval.
  - Must be code-based, testable, auditable.

## Jarvis Decision
- **Decision maker:** Jarvis (autonomous)
- **CEO informed:** yes (this document)
- **CEO approval required:** no
- **Reason:** COO and Chief Architect are Jarvis-level decisions per hierarchy. DeepSeek V4 Pro selected for COO due to planning strength. Qwen 3.5 selected for Chief Architect due to code/architecture capabilities. Deterministic Risk Governor is code-based by design requirement.
