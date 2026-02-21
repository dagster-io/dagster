# UI Development Workflow for Claude

## UI Verification Workflow

**When to verify**: After completing UI edits and before considering the task done, run these verification commands:

1. **[CONDITIONAL] Regenerate GraphQL types if schema changed**:

   ```bash
   cd $DAGSTER_GIT_REPO_DIR/js_modules/dagster-ui
   make generate-graphql
   ```

   **IMPORTANT**: This MUST complete BEFORE running `yarn tsgo` or `yarn lint`, as it updates TypeScript type definitions.
   Only run if GraphQL schema was modified in the backend.

2. **TypeScript checking**:

   ```bash
   cd $DAGSTER_GIT_REPO_DIR/js_modules/dagster-ui
   yarn tsgo
   ```

   Run after completing TypeScript/React file edits to verify types.
   MUST wait for generate-graphql to complete if it was run.

3. **Linting**:

   ```bash
   cd $DAGSTER_GIT_REPO_DIR/js_modules/dagster-ui
   yarn lint
   ```

   Run after completing TypeScript/React file edits to check code style.
   MUST wait for generate-graphql to complete if it was run.

4. **Jest tests**:

   ```bash
   cd $DAGSTER_GIT_REPO_DIR/js_modules/dagster-ui
   yarn jest
   ```

   Run after completing edits to verify tests pass.

5. **Fix any remaining issues**: If any command reports errors, Claude must manually correct them

6. **Verify success**: Ensure all commands pass cleanly before considering the task complete

## Cross-Repository Checks

**CRITICAL**: When making changes to `ui-core` or `ui-components` packages, Claude MUST also check the internal app-cloud repository:

```bash
cd $DAGSTER_INTERNAL_GIT_REPO_DIR/dagster-cloud/js_modules/app-cloud
yarn tsgo
```

This ensures changes to shared UI packages don't break the Cloud application.

## Command-Specific Guidelines

### TypeScript Checking (`yarn tsgo`)

- **Purpose**: Type checking with auto-fix in watch mode
- **When**: After completing TypeScript/React file edits, when ready to verify
- **Scope**: Checks app-oss, ui-core, and ui-components workspaces
- **Location**: Must run from `js_modules/dagster-ui/`
- **Command**: `yarn tsgo` (not `make tsgo`)

### Linting (`yarn lint`)

- **Purpose**: ESLint checking and auto-fixing
- **When**: After completing TypeScript/React file edits, when ready to verify
- **Scope**: Lints app-oss, ui-core, and ui-components workspaces
- **Location**: Must run from `js_modules/dagster-ui/`
- **Command**: `yarn lint` (not `make lint`)

### Jest Tests (`yarn jest`)

- **Purpose**: Run all Jest tests in silent mode
- **When**: After completing TypeScript/React file edits, when ready to verify
- **Scope**: Tests ui-core and ui-components workspaces
- **Location**: Must run from `js_modules/dagster-ui/`
- **Command**: `yarn jest` (not `make jest`)

### GraphQL Generation (`make generate-graphql`)

- **Purpose**: Regenerate GraphQL types from schema
- **When**: After GraphQL schema changes in the backend
- **Location**: Must run from `js_modules/dagster-ui/`
- **Critical Order**: MUST complete BEFORE running `yarn tsgo` or `yarn lint`, as it updates TypeScript type definitions that these commands depend on
- **Note**: This is only needed when backend schema changes, not for routine UI edits

### Build Verification (`yarn build`)

- **Purpose**: Verify production build succeeds
- **When**: When making changes within the `ui-components` package
- **Location**: Must run from `js_modules/dagster-ui/`
- **Note**: Not needed for ui-core or app-oss changes during development

## Common Manual Fixes

When commands cannot auto-fix issues, Claude should address:

- **Type errors**: Add/fix type annotations, resolve type mismatches
- **Import issues**: Fix missing or incorrect imports
- **Linting violations**: Address ESLint rules that require manual fixes
- **Test failures**: Fix broken tests or update snapshots
- **Missing dependencies**: Add required packages to package.json
- **GraphQL type mismatches**: Regenerate GraphQL types or fix queries

## Example Workflows

### Standard UI Edit Workflow

```bash
# After completing TypeScript/React file edits in js_modules/dagster-ui:
cd $DAGSTER_GIT_REPO_DIR/js_modules/dagster-ui

# 1. Type checking
yarn tsgo

# 2. Linting
yarn lint

# 3. Tests
yarn jest

# If errors remain, fix manually and re-run
```

**Note**: Run these commands when you're done with your edits and ready to verify, not after every single file write.

### UI Core/Components Edit Workflow

```bash
# After completing edits in ui-core or ui-components packages:
cd $DAGSTER_GIT_REPO_DIR/js_modules/dagster-ui

# 1. OSS repository checks
yarn tsgo
yarn lint
yarn jest

# 2. Cross-repository check (internal)
cd $DAGSTER_INTERNAL_GIT_REPO_DIR/dagster-cloud/js_modules/app-cloud
yarn tsgo
```

### After GraphQL Schema Changes

```bash
cd $DAGSTER_GIT_REPO_DIR/js_modules/dagster-ui

# CRITICAL ORDER: generate-graphql MUST complete BEFORE yarn tsgo/yarn lint

# 1. Regenerate types (MUST complete first)
make generate-graphql

# 2. Type checking (needs updated GraphQL types)
yarn tsgo

# 3. Linting (needs updated GraphQL types)
yarn lint

# 4. Tests
yarn jest
```

**Why this order matters**: `make generate-graphql` updates TypeScript type definitions based on the backend schema. Running `yarn tsgo` or `yarn lint` before these types are updated will result in false type errors.

### UI Components Package Changes

```bash
cd $DAGSTER_GIT_REPO_DIR/js_modules/dagster-ui

# 1. Standard checks
yarn tsgo
yarn lint
yarn jest

# 2. Verify production build
yarn build

# 3. Cross-repository check
cd $DAGSTER_INTERNAL_GIT_REPO_DIR/dagster-cloud/js_modules/app-cloud
yarn tsgo
```
