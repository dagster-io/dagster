# Dagster Plus API Documentation

This directory contains comprehensive documentation for the Dagster Plus API implementation and GraphQL usage patterns.

## Primary References

### **[INTERNAL_GRAPHQL_USAGE.md](./INTERNAL_GRAPHQL_USAGE.md)** 🔍

**For agents and humans**: This is the authoritative reference for the current state of the Dagster Plus GraphQL API.

Contains complete documentation of:

- Asset health and stateful GraphQL queries
- Production usage patterns from the internal Dagster Cloud frontend
- Fragment patterns and query examples across all Dagster Plus entities
- Implementation recommendations for new API endpoints
- Schema types and production fragments for all entities

### **[API_CONVENTIONS.md](./API_CONVENTIONS.md)** 📋

Implementation guidelines for `dg api` CLI commands following GitHub CLI patterns:

- Command structure (`dg api <noun> <verb>`)
- File organization and directory structure
- Standard flags (`--json`, `--limit`, `--cursor`)
- Output formatting (human-readable vs JSON)
- Error handling standards and HTTP status mapping
- GraphQL abstraction patterns
- Implementation templates and testing conventions

### **[API_IMPLEMENTATION_PLAN.md](./API_IMPLEMENTATION_PLAN.md)** 🗺️

Comprehensive roadmap for implementing the complete Dagster Plus API CLI:

- Standard verbs pattern (list, get, create, update, delete)
- Tier-based implementation plan (Core Infrastructure → Cloud Management → Extended → Advanced)
- GraphQL field mappings for each noun
- File organization structure
- Implementation priorities by phase
- Design principles and consistency guidelines

## Quick Navigation

| Document                     | Purpose                     | When to Use                                               |
| ---------------------------- | --------------------------- | --------------------------------------------------------- |
| `INTERNAL_GRAPHQL_USAGE.md`  | GraphQL API reference       | When implementing GraphQL queries or understanding schema |
| `API_CONVENTIONS.md`         | CLI implementation patterns | When building new `dg api` commands                       |
| `API_IMPLEMENTATION_PLAN.md` | Development roadmap         | When planning API feature development                     |

## For Developers

1. **Start with** `INTERNAL_GRAPHQL_USAGE.md` to understand the GraphQL schema and production patterns
2. **Follow** `API_CONVENTIONS.md` for consistent CLI implementation
3. **Reference** `API_IMPLEMENTATION_PLAN.md` for planned features and priorities
