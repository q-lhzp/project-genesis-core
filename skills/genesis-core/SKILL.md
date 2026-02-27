---
name: genesis-core
description: Genesis Core OS - Autonomous Lifecycle Management and Evolution.
metadata:
  openclaw:
    emoji: "🌌"
    requires:
      plugins:
        - project-genesis-core-bridge
---

# 🌌 Genesis Core OS

This skill provides autonomous lifecycle management and evolution capabilities for the Genesis entity.

## Architecture

Genesis Core OS is built on a **Kernel-based architecture**. All state management and entity interactions MUST go through the `project-genesis-core-bridge` tools. Direct manipulation of JSON files in `memory/reality/` is **prohibited**.

## Required Tools

All agents MUST use the following bridge tools to interact with the Genesis Kernel:

| Tool | Purpose |
|------|---------|
| `kernel_status` | Retrieve the current kernel state, engine health, and system diagnostics |
| `reality_needs` | Query and manage the entity's biological needs (energy, hunger, mood, social, etc.) |

## Interaction Rules

1. **Never edit JSON files directly** in `memory/reality/` - always use bridge tools
2. **Query before modify** - Use `kernel_status` to understand current state
3. **Respect biological priorities** - Check needs status before suggesting actions
4. **Event-driven updates** - Emit events rather than direct state mutations when possible

## Kernel Health

Run `kernel_status` at the start of each session to ensure all engines are operational.
