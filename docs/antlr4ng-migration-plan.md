# antlr4ts to antlr4ng Migration Assessment and Plan

## Executive Summary

This document assesses the migration of Dagster's UI codebase from `antlr4ts` (0.5.0-alpha.4) to `antlr4ng`, the actively maintained successor. The migration is recommended due to `antlr4ts` being unmaintained since 2020, while `antlr4ng` offers better performance (9-35% faster), stricter TypeScript support, and active development.

**Migration Complexity**: Medium
**Estimated Files to Modify**: ~30+ files
**Risk Level**: Medium (due to API changes and stricter nullability)

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [antlr4ng Overview](#antlr4ng-overview)
3. [API Differences & Breaking Changes](#api-differences--breaking-changes)
4. [Migration Steps](#migration-steps)
5. [Potential Pitfalls](#potential-pitfalls)
6. [Pros and Cons](#pros-and-cons)
7. [Risk Mitigation](#risk-mitigation)
8. [Testing Strategy](#testing-strategy)

---

## Current State Analysis

### Packages Currently Used

| Package | Version | Purpose |
|---------|---------|---------|
| `antlr4ts` | 0.5.0-alpha.4 | Runtime library |
| `antlr4ts-cli` | 0.5.0-alpha.4 | Code generator (dev dependency) |

### Grammar Files (6 total)

| Grammar | Location | Purpose |
|---------|----------|---------|
| `SelectionAutoComplete.g4` | `src/selection/` | UI selection autocomplete |
| `AssetSelection.g4` | `python_modules/.../antlr_asset_selection/` | Asset selection DSL |
| `AutomationSelection.g4` | `src/automation-selection/` | Automation selection |
| `JobSelection.g4` | `src/job-selection/` | Job selection |
| `OpSelection.g4` | `src/op-selection/` | Op selection |
| `RunSelection.g4` | `src/run-selection/` | Run selection |

### Files Using antlr4ts (52 files total)

**Hand-written implementation files (~20):**
- `src/selection/BaseSelectionVisitor.ts`
- `src/selection/CustomErrorListener.ts`
- `src/selection/SelectionInputParser.ts`
- `src/selection/SelectionAutoCompleteVisitor.ts`
- `src/selection/SelectionInputHighlighter.ts`
- `src/selection/createSelectionLinter.ts`
- `src/asset-selection/AntlrAssetSelectionVisitor.oss.ts`
- `src/asset-selection/parseAssetSelectionQuery.ts`
- `src/run-selection/AntlrRunSelection.ts`
- `src/run-selection/AntlrRunSelectionVisitor.ts`
- `src/job-selection/AntlrJobSelection.ts`
- `src/job-selection/AntlrJobSelectionVisitor.ts`
- `src/op-selection/AntlrOpSelection.ts`
- `src/op-selection/AntlrOpSelectionVisitor.ts`
- `src/automation-selection/AntlrAutomationSelection.ts`
- `src/automation-selection/AntlrAutomationSelectionVisitor.ts`
- Various test files

**Generated files (~24, 4 per grammar):**
- `*Lexer.ts`
- `*Parser.ts`
- `*Listener.ts`
- `*Visitor.ts`

### Key API Usage Patterns

```typescript
// Core imports (will need updates)
import {CharStreams, CommonTokenStream, Lexer, Parser} from 'antlr4ts';
import {ParserRuleContext} from 'antlr4ts';
import {BailErrorStrategy} from 'antlr4ts';
import {ANTLRErrorListener, RecognitionException, Recognizer} from 'antlr4ts';

// Tree imports (will need updates)
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';
import {ParseTree} from 'antlr4ts/tree/ParseTree';
import {TerminalNode} from 'antlr4ts/tree/TerminalNode';

// ATN imports (in generated code)
import {ATN, ATNDeserializer, ParserATNSimulator} from 'antlr4ts/atn/...';
```

---

## antlr4ng Overview

[antlr4ng](https://github.com/mike-lischke/antlr4ng) is the Next Generation TypeScript runtime for ANTLR4.

### Key Characteristics

- **Active Maintenance**: Actively developed with regular releases
- **Performance**: 9-35% faster than other JS/TS runtimes
- **TypeScript-First**: Native TypeScript with proper types
- **ES2022+**: Requires modern JavaScript features
- **ESM Only**: No CommonJS support (as of v3.0.0)
- **Zero Runtime Dependencies**: No third-party runtime dependencies
- **Stricter Nullability**: More explicit null handling

### Associated Packages

| Package | Purpose |
|---------|---------|
| `antlr4ng` | Runtime library |
| `antlr4ng-cli` | Code generator (transitional) |
| `antlr-ng` | Next-gen ANTLR tool (future) |

---

## API Differences & Breaking Changes

### 1. Import Path Changes

```typescript
// Before (antlr4ts)
import {CharStreams, CommonTokenStream} from 'antlr4ts';
import {ParserRuleContext} from 'antlr4ts';
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';
import {ParseTree} from 'antlr4ts/tree/ParseTree';
import {TerminalNode} from 'antlr4ts/tree/TerminalNode';

// After (antlr4ng)
import {CharStream, CommonTokenStream} from 'antlr4ng';
import {ParserRuleContext} from 'antlr4ng';
import {AbstractParseTreeVisitor} from 'antlr4ng';
import {ParseTree} from 'antlr4ng';
import {TerminalNode} from 'antlr4ng';
```

### 2. Class/Method Renames

| antlr4ts | antlr4ng | Notes |
|----------|----------|-------|
| `CharStreams.fromString()` | `CharStream.fromString()` | Class name change |
| `Parser._ctx` | `Parser.context` | Property rename |
| `Parser._errHandler` | `Parser.errorHandler` | Property rename |
| `Parser._input` | `Parser.inputStream` | Property rename |
| `Recognizer._interp` | `Recognizer.interpreter` | Property rename |
| `Lexer._type` | `Lexer.type` | Property rename (v3.0.0) |
| `Lexer._channel` | `Lexer.channel` | Property rename (v3.0.0) |
| `Lexer._mode` | `Lexer.mode` | Property rename (v3.0.0) |
| `Parser._parseListeners` | `Parser.parseListeners` | Property rename (v3.0.0) |

### 3. Nullability Changes (Critical)

antlr4ng exposes Java nullability more strictly. Many properties that were implicitly non-null in antlr4ts may now be nullable.

```typescript
// Before (antlr4ts) - worked without null checks
const stopIndex = ctx.stop.stopIndex;

// After (antlr4ng) - requires null handling
const stopIndex = ctx.stop?.stopIndex ?? 0;
// OR
const stopIndex = ctx.stop!.stopIndex; // if you're certain it's not null
```

**Affected patterns in Dagster code:**
```typescript
// Current code patterns that need attention:
ctx.stop!.stopIndex + 1  // Already using non-null assertion
ctx.parent!.getChild(2)  // Already using non-null assertion
ctx.start.startIndex     // May now require null check
```

### 4. RuleContext Merge (v3.0.0)

The `RuleContext` class has been merged into `ParserRuleContext`, simplifying the class hierarchy.

### 5. Tree Visitor API

```typescript
// Before (antlr4ts)
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';

class MyVisitor extends AbstractParseTreeVisitor<Result> {
  defaultResult() { return null; }
}

// After (antlr4ng)
import {AbstractParseTreeVisitor} from 'antlr4ng';

class MyVisitor extends AbstractParseTreeVisitor<Result> {
  protected defaultResult(): Result { return null; }
}
```

### 6. Error Listener Interface

```typescript
// Before (antlr4ts)
import {ANTLRErrorListener, RecognitionException, Recognizer} from 'antlr4ts';

class CustomErrorListener implements ANTLRErrorListener<any> {
  syntaxError(
    recognizer: Recognizer<any, any>,
    offendingSymbol: any,
    line: number,
    charPositionInLine: number,
    msg: string,
    e: RecognitionException | undefined
  ): void { }
}

// After (antlr4ng)
import {ANTLRErrorListener, RecognitionException, Recognizer} from 'antlr4ng';

// Interface is similar but may have subtle type differences
```

---

## Migration Steps

### Phase 1: Preparation

1. **Audit current usage**
   ```bash
   grep -r "antlr4ts" js_modules/dagster-ui/packages/ui-core/src --include="*.ts" | grep -v "generated/"
   ```

2. **Ensure comprehensive test coverage**
   - Run existing tests: `yarn jest`
   - Document any gaps in selection/parsing tests

3. **Create migration branch**
   ```bash
   git checkout -b feature/antlr4ng-migration
   ```

### Phase 2: Package Updates

1. **Update package.json dependencies**
   ```json
   {
     "dependencies": {
       "antlr4ng": "^3.0.4"  // Replace antlr4ts
     },
     "devDependencies": {
       "antlr4ng-cli": "^3.0.0"  // Replace antlr4ts-cli
     }
   }
   ```

2. **Remove old packages**
   ```bash
   yarn remove antlr4ts antlr4ts-cli
   yarn add antlr4ng
   yarn add -D antlr4ng-cli
   ```

### Phase 3: Regenerate Parsers

1. **Update generator scripts**

   All scripts in `src/scripts/generate*.ts` need updating:

   ```typescript
   // Before
   execSync(`antlr4ts -visitor -o ./src/selection/generated ${GRAMMAR_FILE_PATH}`);

   // After
   execSync(`antlr4ng -visitor -o ./src/selection/generated ${GRAMMAR_FILE_PATH}`);
   ```

2. **Regenerate all parsers**
   ```bash
   yarn generate-asset-selection
   yarn generate-selection-autocomplete
   yarn generate-run-selection
   yarn generate-op-selection
   yarn generate-job-selection
   yarn generate-automation-selection
   ```

3. **Fix ESLint issues in generated files**
   ```bash
   yarn lint
   ```

### Phase 4: Update Import Statements

Create a sed script or use find-replace for bulk updates:

```bash
# Key replacements
s/from 'antlr4ts'/from 'antlr4ng'/g
s/from 'antlr4ts\/tree\/AbstractParseTreeVisitor'/from 'antlr4ng'/g
s/from 'antlr4ts\/tree\/ParseTree'/from 'antlr4ng'/g
s/from 'antlr4ts\/tree\/TerminalNode'/from 'antlr4ng'/g
s/from 'antlr4ts\/tree\/RuleNode'/from 'antlr4ng'/g
s/CharStreams\.fromString/CharStream.fromString/g
```

**Files requiring import updates:**
- `src/selection/BaseSelectionVisitor.ts`
- `src/selection/CustomErrorListener.ts`
- `src/selection/SelectionInputParser.ts`
- `src/selection/SelectionAutoCompleteVisitor.ts`
- `src/selection/SelectionInputHighlighter.ts`
- `src/selection/createSelectionLinter.ts`
- `src/asset-selection/AntlrAssetSelectionVisitor.oss.ts`
- `src/asset-selection/parseAssetSelectionQuery.ts`
- All `Antlr*Selection.ts` and `Antlr*SelectionVisitor.ts` files
- Test files

### Phase 5: Fix Type Errors

1. **Address nullability issues**

   Run TypeScript compiler and fix errors:
   ```bash
   yarn tsgo
   ```

2. **Common fixes needed:**

   ```typescript
   // Pattern 1: ctx.stop access
   // Before
   const stopIndex = ctx.stop.stopIndex;
   // After
   const stopIndex = ctx.stop?.stopIndex ?? ctx.start.startIndex;

   // Pattern 2: parent access
   // Before
   const parent = ctx.parent;
   // After
   const parent = ctx.parent; // May need null check depending on usage

   // Pattern 3: token access
   // Before
   const token = ctx.payload;
   // After (may need adjustment based on actual API)
   const token = ctx.symbol; // or ctx.payload with null check
   ```

3. **Review and fix `TerminalNode` usage:**
   ```typescript
   // Current code in BaseSelectionVisitor.ts
   } else if (ctx instanceof TerminalNode) {
     start = ctx.payload.startIndex;
     stop = ctx.payload.stopIndex;
   }

   // May need adjustment based on antlr4ng API
   ```

### Phase 6: Update Error Handling

```typescript
// CustomErrorListener.ts may need updates
import {ANTLRErrorListener, RecognitionException, Recognizer, Token} from 'antlr4ng';

export class CustomErrorListener implements ANTLRErrorListener<Token> {
  syntaxError(
    recognizer: Recognizer<Token>,
    offendingSymbol: Token | null,
    line: number,
    charPositionInLine: number,
    msg: string,
    e: RecognitionException | null
  ): void {
    // Implementation
  }
}
```

### Phase 7: ESM Compatibility

antlr4ng v3.0.0+ is ESM-only. Check for compatibility:

1. **Verify tsconfig.json settings:**
   ```json
   {
     "compilerOptions": {
       "module": "ESNext",
       "moduleResolution": "bundler"
     }
   }
   ```

2. **Check build tooling compatibility (Vite, Jest, etc.)**

### Phase 8: Testing

1. **Run unit tests**
   ```bash
   yarn jest
   ```

2. **Run TypeScript checks**
   ```bash
   yarn tsgo
   ```

3. **Run linting**
   ```bash
   yarn lint
   ```

4. **Manual testing of selection inputs**
   - Asset selection queries
   - Run selection
   - Job/Op selection
   - Autocomplete functionality

---

## Potential Pitfalls

### 1. ESM-Only Distribution (High Risk)

**Issue**: antlr4ng v3.0.0+ doesn't support CommonJS.

**Impact**: May break Jest tests or other tools expecting CJS.

**Mitigation**:
- Ensure Jest is configured for ESM
- Update jest.config.js:
  ```javascript
  module.exports = {
    transform: {
      '^.+\\.(ts|tsx)$': ['ts-jest', { useESM: true }]
    },
    extensionsToTreatAsEsm: ['.ts', '.tsx']
  };
  ```

### 2. Stricter Null Checking (Medium Risk)

**Issue**: Many properties now correctly expose nullability.

**Impact**: TypeScript errors throughout the codebase.

**Mitigation**:
- Add null checks or non-null assertions strategically
- Review each case to determine appropriate handling
- The codebase already uses `!` in many places, but needs review

### 3. Generated Code Differences (Medium Risk)

**Issue**: Generated parser/lexer code structure may differ.

**Impact**: Hand-written code depending on generated code structure may break.

**Mitigation**:
- Regenerate all parsers before updating hand-written code
- Compare generated output structure
- Update dependent code accordingly

### 4. ES2022 Requirement (Low-Medium Risk)

**Issue**: Requires ES2022+ features (private fields, static init blocks).

**Impact**: May not work in older browsers.

**Mitigation**:
- Check browserslist in package.json (currently `">0.2%", "not dead"`)
- Ensure build target is compatible
- The package.json already excludes IE11

### 5. Token/TerminalNode API Differences (Medium Risk)

**Issue**: Access patterns for tokens may differ.

**Impact**: `TerminalNode.payload` access patterns may need updates.

**Example from current code:**
```typescript
// BaseSelectionVisitor.ts line 124-126
} else if (ctx instanceof TerminalNode) {
  start = ctx.payload.startIndex;
  stop = ctx.payload.stopIndex;
}
```

### 6. Visitor Method Signatures (Low Risk)

**Issue**: Optional vs required visit methods.

**Impact**: Generated visitor interfaces may have different optional/required methods.

**Mitigation**: Review generated `*Visitor.ts` interfaces and update implementations.

---

## Pros and Cons

### Pros

| Benefit | Description |
|---------|-------------|
| **Active Maintenance** | Regular updates, bug fixes, and security patches |
| **Better Performance** | 9-35% faster parsing performance |
| **Stricter TypeScript** | Better type safety, fewer runtime errors |
| **Modern JS Features** | Uses ES2022+ features for cleaner code |
| **No Runtime Deps** | Zero third-party runtime dependencies |
| **Better Nullability** | Explicit null handling prevents bugs |
| **Future-Proof** | Aligned with antlr-ng, the next-gen ANTLR tool |
| **Active Community** | 336+ dependent projects, active development |

### Cons

| Drawback | Description |
|----------|-------------|
| **Migration Effort** | Significant code changes required (~30+ files) |
| **ESM-Only** | May require build tooling adjustments |
| **Breaking Changes** | API renames require careful search/replace |
| **Null Check Burden** | More explicit null handling needed |
| **Testing Required** | Comprehensive testing needed post-migration |
| **ES2022 Requirement** | May limit browser compatibility |
| **Learning Curve** | Team needs to learn new API patterns |

---

## Risk Mitigation

### 1. Incremental Migration

Consider migrating one grammar at a time:
1. Start with `SelectionAutoComplete.g4` (most central)
2. Validate thoroughly
3. Proceed to other grammars

### 2. Feature Flags

Implement temporary feature flags to switch between old/new parsers:
```typescript
const USE_ANTLR4NG = process.env.REACT_APP_USE_ANTLR4NG === 'true';
```

### 3. Comprehensive Testing

1. **Unit tests**: Ensure all existing tests pass
2. **Integration tests**: Test full selection workflows
3. **Visual regression**: Screenshot tests for syntax highlighting
4. **Performance benchmarks**: Validate performance improvements

### 4. Rollback Plan

Keep antlr4ts code in a separate branch for quick rollback if issues arise post-deployment.

---

## Testing Strategy

### Pre-Migration Baseline

```bash
# Capture current test results
yarn jest --coverage > baseline-coverage.txt
yarn tsgo 2>&1 | tee baseline-types.txt
```

### Post-Migration Validation

1. **TypeScript compilation**
   ```bash
   yarn tsgo
   ```

2. **Unit tests**
   ```bash
   yarn jest
   ```

3. **Lint checks**
   ```bash
   yarn lint
   ```

4. **Manual testing checklist**:
   - [ ] Asset selection with various queries
   - [ ] Autocomplete suggestions work correctly
   - [ ] Syntax highlighting displays properly
   - [ ] Error messages show for invalid syntax
   - [ ] Traversal operators (`+`, `++`) work
   - [ ] Boolean operators (`and`, `or`, `not`) work
   - [ ] Attribute queries (`key:`, `tag:`, etc.) work
   - [ ] Parentheses grouping works
   - [ ] Run selection works
   - [ ] Job/Op selection works
   - [ ] Automation selection works

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Preparation | 1 day | None |
| Package Updates | 0.5 day | Phase 1 |
| Regenerate Parsers | 0.5 day | Phase 2 |
| Update Imports | 1 day | Phase 3 |
| Fix Type Errors | 2-3 days | Phase 4 |
| Update Error Handling | 0.5 day | Phase 5 |
| ESM Compatibility | 0.5-1 day | Phase 6 |
| Testing & Fixes | 2-3 days | Phase 7 |
| **Total** | **8-11 days** | |

---

## Conclusion

The migration from `antlr4ts` to `antlr4ng` is **recommended** due to:

1. **antlr4ts is abandoned** (last release: 2020)
2. **antlr4ng is actively maintained** with regular releases
3. **Performance improvements** of 9-35%
4. **Better TypeScript support** with stricter types
5. **Future compatibility** with antlr-ng

The migration is **feasible** with moderate effort. The main challenges are:
- ESM-only distribution (v3.0.0+)
- Stricter nullability requiring code updates
- Import path changes across 30+ files

**Recommendation**: Proceed with migration using the phased approach outlined above, starting with a proof-of-concept on `SelectionAutoComplete.g4` before full rollout.

---

## References

- [antlr4ng GitHub Repository](https://github.com/mike-lischke/antlr4ng)
- [antlr4ng NPM Package](https://www.npmjs.com/package/antlr4ng)
- [antlr4ng-cli NPM Package](https://www.npmjs.com/package/antlr4ng-cli)
- [antlr-ng Parser Generator](https://www.antlr-ng.org/)
- [ANTLR Discussion Group - antlr-ng Announcement](https://groups.google.com/g/antlr-discussion/c/lokMvh6slUc)
- [antlr4ts Deprecation Discussion](https://github.com/tunnelvisionlabs/antlr4ts/issues/340)
