# Partition Selection ANTLR Migration Plan

## Executive Summary

This document outlines a plan to replace the current regex-based partition selection parser with an ANTLR-based parser that properly supports special characters in partition keys through quoted string syntax.

## Problem Statement

### Current Shortcomings

The existing partition selection text parser in `SpanRepresentation.tsx` uses simple string splitting and regex matching, which fails when partition keys contain special characters:

1. **Comma (`,`)**: Used as the separator between partition terms
   - Input: `my,partition` → Incorrectly parsed as two partitions: `my` and `partition`

2. **Square brackets (`[`, `]`)**: Used for range syntax `[start...end]`
   - Input: `[special]` → May be incorrectly interpreted as a malformed range

3. **Ellipsis (`...`)**: Used as range delimiter
   - Input: `data...backup` → Incorrectly parsed as a range from `data` to `backup`

4. **Asterisk (`*`)**: Used for wildcard matching
   - Input: `file*.txt` → Incorrectly triggers wildcard matching logic

5. **Pipe (`|`)**: Used in URLs to separate multi-dimensional partition keys
   - Input: `dim1|dim2` in 2D context → Split incorrectly

### Root Cause

The parser at `SpanRepresentation.tsx:56-79` uses naive string operations:

```typescript
export function parseSpanText(text: string): ParsedSpanTerm[] {
  const terms = text.split(',').map((s) => s.trim());  // ← Problem: splits on ALL commas
  // ...
  const rangeMatch = /^\[(.*)\.\.\.(.*)\]$/g.exec(term);  // ← Problem: greedy regex
  // ...
  } else if (term.includes('*')) {  // ← Problem: any asterisk triggers wildcard
```

There is no escaping mechanism, so partition keys containing these characters cannot be properly represented.

### Backend Validation Gaps

The backend has inconsistent validation:

| Partition Type | Validated Characters | Location |
|---------------|---------------------|----------|
| Static (single-dim) | `...`, escape chars | `base.py:11` |
| Static (multi-dim) | `\|`, `,`, `[`, `]` | `multi.py:26` |
| Dynamic | **None** | - |
| Time Window | **None** | - |

This means users can create partition keys with special characters that the UI cannot handle.

---

## Architecture Analysis

### Current Code Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INPUT LAYER                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DimensionRangeInput.tsx          OrdinalPartitionSelector.tsx          │
│  (Text input for time-series)     (Dropdown for ordinal partitions)     │
│           │                                   │                          │
│           ▼                                   │                          │
│  spanTextToSelectionsOrError()                │                          │
│           │                                   │                          │
└───────────┼───────────────────────────────────┼──────────────────────────┘
            │                                   │
            ▼                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          PARSING LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  SpanRepresentation.tsx                                                  │
│  ├── parseSpanText(text) → ParsedSpanTerm[]                             │
│  ├── convertToPartitionSelection(terms, keys) → Selection | Error       │
│  ├── partitionsToText(selected, all) → string                           │
│  ├── stringForSpan(span, keys) → string                                 │
│  └── allPartitionsSpan(dimension) → string                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         STATE MANAGEMENT LAYER                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  usePartitionDimensionSelections.tsx                                     │
│  ├── Manages PartitionDimensionSelection state                          │
│  ├── Syncs with URL query string via buildSerializer()                  │
│  └── Uses spanTextToSelectionsOrError() for parsing                     │
│                                                                          │
│  usePartitionKeyInParams.tsx                                             │
│  ├── Manages focused partition key in URL                               │
│  └── Uses '|' delimiter for multi-dimensional keys                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PartitionDimensionSelection {                                          │
│    dimension: PartitionHealthDimension;                                 │
│    selectedKeys: string[];                                              │
│    selectedRanges: PartitionDimensionSelectionRange[];                  │
│  }                                                                       │
│                                                                          │
│  ParsedSpanTerm (intermediate representation)                           │
│    | { type: 'range'; start: string; end: string }                      │
│    | { type: 'wildcard'; prefix: string; suffix: string }               │
│    | { type: 'single'; key: string }                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### UI Entry Points Using Text Parsing

| Component | File Path | Selection Method | Uses Text Parser |
|-----------|-----------|------------------|------------------|
| Asset Partitions Tab | `src/assets/AssetPartitions.tsx:246` | `DimensionRangeWizard` | ✅ Yes |
| Launch Partitions Dialog | `src/assets/LaunchAssetChoosePartitionsDialog.tsx:493` | `DimensionRangeWizards` | ✅ Yes |
| Backfill Selector | `src/partitions/BackfillSelector.tsx:202` | `DimensionRangeWizard` | ✅ Yes |
| Report Events Dialog | `src/assets/useReportEventsDialog.tsx:39` | `DimensionRangeWizards` | ✅ Yes |
| URL Query String Sync | `src/assets/usePartitionDimensionSelections.tsx:117` | `spanTextToSelectionsOrError` | ✅ Yes |

### Components NOT Using Text Parser (Dropdown Only)

| Component | File Path | Notes |
|-----------|-----------|-------|
| Delete Dynamic Partitions | `src/assets/DeleteDynamicPartitionsDialog.tsx` | Uses `OrdinalPartitionSelector` |
| Ordinal/Range Selector | `src/partitions/OrdinalOrSingleRangePartitionSelector.tsx` | Uses `OrdinalPartitionSelector` |
| Create Partition Dialog | `src/partitions/CreatePartitionDialog.tsx` | Direct text input, no parsing |

---

## Existing ANTLR Infrastructure

The codebase has mature ANTLR4 infrastructure that we can leverage:

### Existing Grammars

| Grammar | Location | Features |
|---------|----------|----------|
| `SelectionAutoComplete.g4` | `src/selection/` | Quoted strings, operators, whitespace handling |
| `AssetSelection.g4` | `src/asset-selection/` | Key matching, traversals, tags |
| `JobSelection.g4` | `src/job-selection/` | Job filtering |
| `OpSelection.g4` | `src/op-selection/` | Step selection |
| `RunSelection.g4` | `src/run-selection/` | Run filtering |

### Key Pattern: Quoted String Support

From `SelectionAutoComplete.g4:133`:
```antlr
QUOTED_STRING: '"' (~["\\\r\n])* '"';
```

This pattern supports double-quoted strings and is already used throughout the codebase.

### Generation Scripts

Each grammar has a generation script in `src/scripts/`:
```typescript
// src/scripts/generateSelection.ts
import {execSync} from 'child_process';
import path from 'path';

const GRAMMAR_FILE_PATH = path.resolve('./src/selection/SelectionAutoComplete.g4');
execSync(`antlr4ts -visitor -o ./src/selection/generated ${GRAMMAR_FILE_PATH}`);
```

---

## Implementation Plan

### Phase 1: Create ANTLR Grammar and Generated Code

#### 1.1 Create Grammar File

**File:** `src/partitions/PartitionSelection.g4`

```antlr
grammar PartitionSelection;

// Entry point
start: partitionExpr EOF;

// A partition expression is a comma-separated list of items
partitionExpr
    : partitionItem (COMMA partitionItem)*
    | /* empty */
    ;

// Each item can be a range, wildcard, or single partition key
partitionItem
    : range
    | wildcard
    | partitionKey
    ;

// Range syntax: [start...end] with optional quotes
range
    : LBRACKET partitionKey RANGE_DELIM partitionKey RBRACKET
    ;

// Wildcard pattern (only valid unquoted)
wildcard
    : WILDCARD_PATTERN
    ;

// A partition key can be quoted or unquoted
partitionKey
    : QUOTED_STRING
    | UNQUOTED_STRING
    ;

// =============================================================================
// LEXER RULES
// =============================================================================

// Structural tokens
LBRACKET: '[';
RBRACKET: ']';
RANGE_DELIM: '...';
COMMA: ',';

// Quoted strings support escape sequences
// Examples: "my,key", "my\"quote", "bracket[test]"
QUOTED_STRING
    : '"' ( ESCAPE_SEQ | ~["\\\r\n] )* '"'
    ;

fragment ESCAPE_SEQ
    : '\\' ["\\/]  // Escaped quote, backslash, or forward slash
    ;

// Wildcard patterns - must contain exactly one asterisk
// Examples: 2024-*, *-suffix, prefix-*-suffix
WILDCARD_PATTERN
    : UNQUOTED_CHAR* '*' UNQUOTED_CHAR*
    ;

// Unquoted strings - simple partition keys without special characters
// Examples: 2024-01-01, my_partition, region-us-east-1
UNQUOTED_STRING
    : UNQUOTED_CHAR+
    ;

fragment UNQUOTED_CHAR
    : [a-zA-Z0-9_.:/@-]  // Alphanumeric plus common partition key chars
    ;

// Whitespace is skipped
WS: [ \t\r\n]+ -> skip;
```

#### 1.2 Create Generation Script

**File:** `src/scripts/generatePartitionSelection.ts`

```typescript
import {execSync} from 'child_process';
import path from 'path';

const GRAMMAR_FILE_PATH = path.resolve('./src/partitions/PartitionSelection.g4');
execSync(`antlr4ts -visitor -o ./src/partitions/generated ${GRAMMAR_FILE_PATH}`);

const files = [
  'PartitionSelectionLexer.ts',
  'PartitionSelectionListener.ts',
  'PartitionSelectionParser.ts',
  'PartitionSelectionVisitor.ts',
];

files.forEach((file) => {
  execSync(`yarn prettier ./src/partitions/generated/${file} --write`);
});
```

#### 1.3 Add Script to package.json

Add to `package.json` scripts:
```json
{
  "scripts": {
    "generate-partition-selection": "ts-node src/scripts/generatePartitionSelection.ts"
  }
}
```

### Phase 2: Implement Visitor and Parser Interface

#### 2.1 Create Visitor Implementation

**File:** `src/partitions/AntlrPartitionSelectionVisitor.ts`

```typescript
import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';
import {
  PartitionSelectionVisitor,
  StartContext,
  PartitionExprContext,
  PartitionItemContext,
  RangeContext,
  WildcardContext,
  PartitionKeyContext,
} from './generated/PartitionSelectionVisitor';

export type ParsedPartitionTerm =
  | {type: 'range'; start: string; end: string}
  | {type: 'wildcard'; prefix: string; suffix: string}
  | {type: 'single'; key: string};

export class AntlrPartitionSelectionVisitor
  extends AbstractParseTreeVisitor<ParsedPartitionTerm[]>
  implements PartitionSelectionVisitor<ParsedPartitionTerm[]>
{
  protected defaultResult(): ParsedPartitionTerm[] {
    return [];
  }

  protected aggregateResult(
    aggregate: ParsedPartitionTerm[],
    nextResult: ParsedPartitionTerm[],
  ): ParsedPartitionTerm[] {
    return [...aggregate, ...nextResult];
  }

  visitStart(ctx: StartContext): ParsedPartitionTerm[] {
    return this.visit(ctx.partitionExpr());
  }

  visitPartitionExpr(ctx: PartitionExprContext): ParsedPartitionTerm[] {
    return ctx.partitionItem().flatMap((item) => this.visit(item));
  }

  visitPartitionItem(ctx: PartitionItemContext): ParsedPartitionTerm[] {
    if (ctx.range()) {
      return this.visit(ctx.range()!);
    }
    if (ctx.wildcard()) {
      return this.visit(ctx.wildcard()!);
    }
    if (ctx.partitionKey()) {
      const key = this.extractPartitionKey(ctx.partitionKey()!);
      return [{type: 'single', key}];
    }
    return [];
  }

  visitRange(ctx: RangeContext): ParsedPartitionTerm[] {
    const keys = ctx.partitionKey();
    const start = this.extractPartitionKey(keys[0]!);
    const end = this.extractPartitionKey(keys[1]!);
    return [{type: 'range', start, end}];
  }

  visitWildcard(ctx: WildcardContext): ParsedPartitionTerm[] {
    const pattern = ctx.WILDCARD_PATTERN().text;
    const asteriskIndex = pattern.indexOf('*');
    return [{
      type: 'wildcard',
      prefix: pattern.substring(0, asteriskIndex),
      suffix: pattern.substring(asteriskIndex + 1),
    }];
  }

  private extractPartitionKey(ctx: PartitionKeyContext): string {
    if (ctx.QUOTED_STRING()) {
      // Remove surrounding quotes and unescape
      const quoted = ctx.QUOTED_STRING()!.text;
      return this.unescapeQuotedString(quoted);
    }
    return ctx.UNQUOTED_STRING()!.text;
  }

  private unescapeQuotedString(quoted: string): string {
    // Remove surrounding quotes
    const inner = quoted.slice(1, -1);
    // Unescape sequences: \" -> ", \\ -> \, \/ -> /
    return inner.replace(/\\(["\\/])/g, '$1');
  }
}
```

#### 2.2 Create Parser Interface

**File:** `src/partitions/parsePartitionSelection.ts`

```typescript
import {CharStreams, CommonTokenStream} from 'antlr4ts';
import {PartitionSelectionLexer} from './generated/PartitionSelectionLexer';
import {PartitionSelectionParser} from './generated/PartitionSelectionParser';
import {AntlrPartitionSelectionVisitor, ParsedPartitionTerm} from './AntlrPartitionSelectionVisitor';

export class PartitionSelectionParseError extends Error {
  constructor(
    message: string,
    public readonly position: number,
  ) {
    super(message);
    this.name = 'PartitionSelectionParseError';
  }
}

class PartitionSelectionErrorListener {
  errors: PartitionSelectionParseError[] = [];

  syntaxError(
    _recognizer: any,
    _offendingSymbol: any,
    _line: number,
    charPositionInLine: number,
    msg: string,
  ): void {
    this.errors.push(new PartitionSelectionParseError(msg, charPositionInLine));
  }
}

/**
 * Parse a partition selection string into structured terms.
 *
 * Supported syntax:
 * - Single keys: `partition1`, `"key,with,commas"`
 * - Ranges: `[2024-01-01...2024-12-31]`, `["start"..."end"]`
 * - Wildcards: `2024-*`, `*-suffix`
 * - Lists: `key1, key2, [range1...range2]`
 *
 * @param text The partition selection string to parse
 * @returns Array of parsed terms, or Error if parsing fails
 */
export function parsePartitionSelection(text: string): ParsedPartitionTerm[] | Error {
  if (!text.trim()) {
    return [];
  }

  try {
    const inputStream = CharStreams.fromString(text);
    const lexer = new PartitionSelectionLexer(inputStream);

    const errorListener = new PartitionSelectionErrorListener();
    lexer.removeErrorListeners();
    lexer.addErrorListener(errorListener);

    const tokenStream = new CommonTokenStream(lexer);
    const parser = new PartitionSelectionParser(tokenStream);

    parser.removeErrorListeners();
    parser.addErrorListener(errorListener);

    const tree = parser.start();

    if (errorListener.errors.length > 0) {
      return errorListener.errors[0]!;
    }

    const visitor = new AntlrPartitionSelectionVisitor();
    return visitor.visit(tree);
  } catch (e) {
    return e instanceof Error ? e : new Error(String(e));
  }
}
```

### Phase 3: Create Serialization Functions

#### 3.1 Create Serializer

**File:** `src/partitions/serializePartitionSelection.ts`

```typescript
/**
 * Characters that require quoting in partition keys
 */
const SPECIAL_CHARS = /[,\[\].*"\\]/;

/**
 * Escape a partition key for serialization.
 * Keys containing special characters are quoted.
 */
export function escapePartitionKey(key: string): string {
  if (!SPECIAL_CHARS.test(key)) {
    return key;
  }
  // Escape backslashes and quotes, then wrap in quotes
  const escaped = key.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  return `"${escaped}"`;
}

/**
 * Serialize a range to string format.
 */
export function serializeRange(start: string, end: string): string {
  return `[${escapePartitionKey(start)}...${escapePartitionKey(end)}]`;
}

/**
 * Serialize selected partitions to a text representation.
 * Optimizes for readability by using ranges for consecutive keys.
 *
 * @param selectedKeys The selected partition keys
 * @param allKeys All available partition keys (for determining ranges)
 * @returns Serialized string representation
 */
export function serializePartitionSelection(
  selectedKeys: string[],
  allKeys?: string[],
): string {
  if (selectedKeys.length === 0) {
    return '';
  }

  // If we have allKeys, try to optimize into ranges
  if (allKeys && allKeys.length > 0) {
    const spans = assembleIntoSpans(allKeys, selectedKeys);
    return spans
      .map((span) => {
        if (span.startIdx === span.endIdx) {
          return escapePartitionKey(allKeys[span.startIdx]!);
        }
        return serializeRange(allKeys[span.startIdx]!, allKeys[span.endIdx]!);
      })
      .join(', ');
  }

  // Without allKeys, just escape and join
  return selectedKeys.map(escapePartitionKey).join(', ');
}

/**
 * Assemble selected keys into contiguous spans for range optimization.
 */
function assembleIntoSpans(
  allKeys: string[],
  selectedKeys: string[],
): Array<{startIdx: number; endIdx: number}> {
  const selectedSet = new Set(selectedKeys);
  const spans: Array<{startIdx: number; endIdx: number}> = [];

  let currentSpan: {startIdx: number; endIdx: number} | null = null;

  allKeys.forEach((key, idx) => {
    if (selectedSet.has(key)) {
      if (currentSpan === null) {
        currentSpan = {startIdx: idx, endIdx: idx};
      } else {
        currentSpan.endIdx = idx;
      }
    } else {
      if (currentSpan !== null) {
        spans.push(currentSpan);
        currentSpan = null;
      }
    }
  });

  if (currentSpan !== null) {
    spans.push(currentSpan);
  }

  return spans;
}
```

### Phase 4: Update SpanRepresentation.tsx

#### 4.1 Refactor to Use ANTLR Parser

**File:** `src/partitions/SpanRepresentation.tsx` (modified)

```typescript
import {
  PartitionDimensionSelection,
  PartitionDimensionSelectionRange,
} from '../assets/usePartitionHealthData';
import {parsePartitionSelection} from './parsePartitionSelection';
import {serializePartitionSelection, serializeRange, escapePartitionKey} from './serializePartitionSelection';

// Re-export types for backward compatibility
export type {ParsedPartitionTerm as ParsedSpanTerm} from './AntlrPartitionSelectionVisitor';

/**
 * @deprecated Use parsePartitionSelection directly
 */
export function parseSpanText(text: string) {
  const result = parsePartitionSelection(text);
  return result instanceof Error ? [] : result;
}

export function assembleIntoSpans<T>(keys: string[], keyTestFn: (key: string, idx: number) => T) {
  // Keep existing implementation - used for health status spans
  const spans: {startIdx: number; endIdx: number; status: T}[] = [];

  keys.forEach((key, ii) => {
    const status = keyTestFn(key, ii);
    const lastSpan = spans[spans.length - 1];
    if (!lastSpan || lastSpan.status !== status) {
      spans.push({startIdx: ii, endIdx: ii, status});
    } else {
      lastSpan.endIdx = ii;
    }
  });

  return spans;
}

export function stringForSpan(
  {startIdx, endIdx}: {startIdx: number; endIdx: number},
  all: string[],
): string {
  if (startIdx === endIdx) {
    return escapePartitionKey(all[startIdx]!);
  }
  return serializeRange(all[startIdx]!, all[endIdx]!);
}

export function allPartitionsSpan({partitionKeys}: {partitionKeys: string[]}) {
  return stringForSpan({startIdx: 0, endIdx: partitionKeys.length - 1}, partitionKeys);
}

export function allPartitionsRange({
  partitionKeys,
}: {
  partitionKeys: string[];
}): PartitionDimensionSelectionRange {
  return {
    start: {idx: 0, key: partitionKeys[0]!},
    end: {idx: partitionKeys.length - 1, key: partitionKeys[partitionKeys.length - 1]!},
  };
}

/**
 * Convert parsed terms to partition selection.
 * This replaces the old convertToPartitionSelection function.
 */
export function convertToPartitionSelection(
  parsedTerms: Array<{type: string; [key: string]: any}>,
  allPartitionKeys: string[],
  skipPartitionKeyValidation?: boolean,
): Error | Omit<PartitionDimensionSelection, 'dimension'> {
  const result: Omit<PartitionDimensionSelection, 'dimension'> = {
    selectedKeys: [],
    selectedRanges: [],
  };

  for (const term of parsedTerms) {
    if (term.type === 'range') {
      const allStartIdx = allPartitionKeys.indexOf(term.start);
      const allEndIdx = allPartitionKeys.indexOf(term.end);
      if (allStartIdx === -1 || allEndIdx === -1) {
        return new Error(
          `Could not find partitions for provided range: ${term.start}...${term.end}`,
        );
      }
      result.selectedKeys = result.selectedKeys.concat(
        allPartitionKeys.slice(allStartIdx, allEndIdx + 1),
      );
      result.selectedRanges.push({
        start: {idx: allStartIdx, key: allPartitionKeys[allStartIdx]!},
        end: {idx: allEndIdx, key: allPartitionKeys[allEndIdx]!},
      });
    } else if (term.type === 'wildcard') {
      let start = -1;
      const close = (end: number) => {
        result.selectedKeys = result.selectedKeys.concat(allPartitionKeys.slice(start, end + 1));
        result.selectedRanges.push({
          start: {idx: start, key: allPartitionKeys[start]!},
          end: {idx: end, key: allPartitionKeys[end]!},
        });
        start = -1;
      };

      allPartitionKeys.forEach((key, idx) => {
        const match = key.startsWith(term.prefix) && key.endsWith(term.suffix);
        if (match && start === -1) {
          start = idx;
        }
        if (!match && start !== -1) {
          close(idx - 1);
        }
      });

      if (start !== -1) {
        close(allPartitionKeys.length - 1);
      }
    } else if (term.type === 'single') {
      const idx = allPartitionKeys.indexOf(term.key);
      if (idx === -1 && !skipPartitionKeyValidation) {
        return new Error(`Could not find partition: ${term.key}`);
      }
      result.selectedKeys.push(term.key);
      result.selectedRanges.push({
        start: {idx, key: term.key},
        end: {idx, key: term.key},
      });
    }
  }

  result.selectedKeys = Array.from(new Set(result.selectedKeys));

  return result;
}

/**
 * Parse span text to selections, returning an error if parsing fails.
 */
export function spanTextToSelectionsOrError(
  allPartitionKeys: string[],
  text: string,
  skipPartitionKeyValidation?: boolean,
): Error | Omit<PartitionDimensionSelection, 'dimension'> {
  const parsedTerms = parsePartitionSelection(text);
  if (parsedTerms instanceof Error) {
    return parsedTerms;
  }
  return convertToPartitionSelection(parsedTerms, allPartitionKeys, skipPartitionKeyValidation);
}

/**
 * Serialize selected partitions to text.
 */
export function partitionsToText(selected: string[], all?: string[]): string {
  return serializePartitionSelection(selected, all);
}
```

### Phase 5: Update URL Serialization

#### 5.1 Update usePartitionDimensionSelections.tsx

**File:** `src/assets/usePartitionDimensionSelections.tsx` (modified)

Update the `buildSerializer` function to use `encodeURIComponent`:

```typescript
export function buildSerializer(assetHealth: Pick<PartitionHealthData, 'dimensions'>) {
  const serializer: QueryPersistedStateConfig<DimensionQueryState[]> = {
    defaults: {},
    encode: (state) => {
      return Object.fromEntries(
        state.map((s) => [
          `${s.name}_range`,
          s.rangeText ? encodeURIComponent(s.rangeText) : undefined,
        ]),
      );
    },
    decode: (qs) => {
      const results: Record<string, {text: string; isFromPartitionQueryStringParam: boolean}> = {};
      const {partition, ...remaining} = qs;

      if (typeof partition === 'string') {
        const partitions = partition.split('|');
        partitions.forEach((partitionText, i) => {
          const name = assetHealth?.dimensions[i]?.name;
          if (name) {
            // Decode URI component for partition values
            try {
              results[name] = {
                text: decodeURIComponent(partitionText),
                isFromPartitionQueryStringParam: true,
              };
            } catch {
              results[name] = {text: partitionText, isFromPartitionQueryStringParam: true};
            }
          }
        });
      }

      for (const key in remaining) {
        if (key.endsWith('_range')) {
          const name = key.replace(/_range$/, '');
          const value = qs[key];
          if (typeof value === 'string') {
            try {
              results[name] = {
                text: decodeURIComponent(value),
                isFromPartitionQueryStringParam: false,
              };
            } catch {
              results[name] = {text: value, isFromPartitionQueryStringParam: false};
            }
          }
        }
      }

      return Object.entries(results).map(([name, {text, isFromPartitionQueryStringParam}]) => ({
        name,
        rangeText: text,
        isFromPartitionQueryStringParam,
      }));
    },
  };
  return serializer;
}
```

### Phase 6: Testing

#### 6.1 Unit Tests for Parser

**File:** `src/partitions/__tests__/parsePartitionSelection.test.ts`

```typescript
import {parsePartitionSelection} from '../parsePartitionSelection';

describe('parsePartitionSelection', () => {
  describe('single keys', () => {
    it('parses simple unquoted key', () => {
      const result = parsePartitionSelection('partition01');
      expect(result).toEqual([{type: 'single', key: 'partition01'}]);
    });

    it('parses date-formatted key', () => {
      const result = parsePartitionSelection('2024-01-01');
      expect(result).toEqual([{type: 'single', key: '2024-01-01'}]);
    });

    it('parses quoted key with comma', () => {
      const result = parsePartitionSelection('"my,key"');
      expect(result).toEqual([{type: 'single', key: 'my,key'}]);
    });

    it('parses quoted key with brackets', () => {
      const result = parsePartitionSelection('"[special]"');
      expect(result).toEqual([{type: 'single', key: '[special]'}]);
    });

    it('parses quoted key with escaped quote', () => {
      const result = parsePartitionSelection('"say\\"hello\\""');
      expect(result).toEqual([{type: 'single', key: 'say"hello"'}]);
    });

    it('parses quoted key with ellipsis', () => {
      const result = parsePartitionSelection('"data...backup"');
      expect(result).toEqual([{type: 'single', key: 'data...backup'}]);
    });
  });

  describe('ranges', () => {
    it('parses simple range', () => {
      const result = parsePartitionSelection('[2024-01-01...2025-01-01]');
      expect(result).toEqual([{type: 'range', start: '2024-01-01', end: '2025-01-01'}]);
    });

    it('parses range with quoted keys', () => {
      const result = parsePartitionSelection('["start,key"..."end,key"]');
      expect(result).toEqual([{type: 'range', start: 'start,key', end: 'end,key'}]);
    });

    it('parses range with mixed quoting', () => {
      const result = parsePartitionSelection('[2024-01-01..."end,key"]');
      expect(result).toEqual([{type: 'range', start: '2024-01-01', end: 'end,key'}]);
    });
  });

  describe('wildcards', () => {
    it('parses prefix wildcard', () => {
      const result = parsePartitionSelection('2024-*');
      expect(result).toEqual([{type: 'wildcard', prefix: '2024-', suffix: ''}]);
    });

    it('parses suffix wildcard', () => {
      const result = parsePartitionSelection('*-production');
      expect(result).toEqual([{type: 'wildcard', prefix: '', suffix: '-production'}]);
    });

    it('parses infix wildcard', () => {
      const result = parsePartitionSelection('prefix-*-suffix');
      expect(result).toEqual([{type: 'wildcard', prefix: 'prefix-', suffix: '-suffix'}]);
    });
  });

  describe('lists', () => {
    it('parses comma-separated keys', () => {
      const result = parsePartitionSelection('key1, key2, key3');
      expect(result).toEqual([
        {type: 'single', key: 'key1'},
        {type: 'single', key: 'key2'},
        {type: 'single', key: 'key3'},
      ]);
    });

    it('parses mixed list with range', () => {
      const result = parsePartitionSelection('key1, [2024-01-01...2024-01-31], key2');
      expect(result).toEqual([
        {type: 'single', key: 'key1'},
        {type: 'range', start: '2024-01-01', end: '2024-01-31'},
        {type: 'single', key: 'key2'},
      ]);
    });

    it('parses list with quoted and unquoted keys', () => {
      const result = parsePartitionSelection('simple, "complex,key", another');
      expect(result).toEqual([
        {type: 'single', key: 'simple'},
        {type: 'single', key: 'complex,key'},
        {type: 'single', key: 'another'},
      ]);
    });
  });

  describe('edge cases', () => {
    it('handles empty string', () => {
      const result = parsePartitionSelection('');
      expect(result).toEqual([]);
    });

    it('handles whitespace only', () => {
      const result = parsePartitionSelection('   ');
      expect(result).toEqual([]);
    });

    it('handles extra whitespace around items', () => {
      const result = parsePartitionSelection('  key1  ,  key2  ');
      expect(result).toEqual([
        {type: 'single', key: 'key1'},
        {type: 'single', key: 'key2'},
      ]);
    });
  });

  describe('backward compatibility', () => {
    // These tests ensure existing unquoted selections continue to work
    it('handles existing date partitions', () => {
      const result = parsePartitionSelection('2022-01-01, 2022-01-02, 2022-01-03');
      expect(result).not.toBeInstanceOf(Error);
    });

    it('handles existing range syntax', () => {
      const result = parsePartitionSelection('[2022-01-01...2022-01-10]');
      expect(result).not.toBeInstanceOf(Error);
    });

    it('handles existing wildcard syntax', () => {
      const result = parsePartitionSelection('2022-01-*');
      expect(result).not.toBeInstanceOf(Error);
    });
  });
});
```

#### 6.2 Unit Tests for Serializer

**File:** `src/partitions/__tests__/serializePartitionSelection.test.ts`

```typescript
import {
  escapePartitionKey,
  serializePartitionSelection,
  serializeRange,
} from '../serializePartitionSelection';

describe('escapePartitionKey', () => {
  it('returns simple keys unchanged', () => {
    expect(escapePartitionKey('partition01')).toBe('partition01');
    expect(escapePartitionKey('2024-01-01')).toBe('2024-01-01');
  });

  it('quotes keys with commas', () => {
    expect(escapePartitionKey('my,key')).toBe('"my,key"');
  });

  it('quotes keys with brackets', () => {
    expect(escapePartitionKey('[special]')).toBe('"[special]"');
  });

  it('quotes and escapes keys with quotes', () => {
    expect(escapePartitionKey('say"hello"')).toBe('"say\\"hello\\""');
  });

  it('quotes keys with asterisks', () => {
    expect(escapePartitionKey('file*.txt')).toBe('"file*.txt"');
  });

  it('quotes keys with ellipsis', () => {
    expect(escapePartitionKey('data...backup')).toBe('"data...backup"');
  });
});

describe('serializeRange', () => {
  it('serializes simple range', () => {
    expect(serializeRange('2024-01-01', '2024-12-31')).toBe('[2024-01-01...2024-12-31]');
  });

  it('serializes range with special characters', () => {
    expect(serializeRange('start,key', 'end,key')).toBe('["start,key"..."end,key"]');
  });
});

describe('serializePartitionSelection', () => {
  const allKeys = ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'];

  it('serializes empty selection', () => {
    expect(serializePartitionSelection([], allKeys)).toBe('');
  });

  it('serializes single key', () => {
    expect(serializePartitionSelection(['2024-01-01'], allKeys)).toBe('2024-01-01');
  });

  it('serializes non-consecutive keys', () => {
    expect(serializePartitionSelection(['2024-01-01', '2024-01-03', '2024-01-05'], allKeys))
      .toBe('2024-01-01, 2024-01-03, 2024-01-05');
  });

  it('serializes consecutive keys as range', () => {
    expect(serializePartitionSelection(['2024-01-01', '2024-01-02', '2024-01-03'], allKeys))
      .toBe('[2024-01-01...2024-01-03]');
  });

  it('serializes mixed selection', () => {
    expect(serializePartitionSelection(
      ['2024-01-01', '2024-01-02', '2024-01-05'],
      allKeys,
    )).toBe('[2024-01-01...2024-01-02], 2024-01-05');
  });

  it('handles keys without allKeys context', () => {
    expect(serializePartitionSelection(['key1', 'key2'])).toBe('key1, key2');
  });
});
```

#### 6.3 Integration Tests

**File:** `src/partitions/__tests__/SpanRepresentation.test.tsx` (update existing)

Add new test cases to the existing test file:

```typescript
// Add to existing test file

describe('SpanRepresentation with special characters', () => {
  describe('round-trip with quoted keys', () => {
    it('handles commas in partition keys', () => {
      const allKeys = ['normal', 'has,comma', 'another'];
      const selected = ['has,comma'];

      const text = partitionsToText(selected, allKeys);
      expect(text).toBe('"has,comma"');

      const parsed = spanTextToSelectionsOrError(allKeys, text);
      expect(parsed).not.toBeInstanceOf(Error);
      expect((parsed as any).selectedKeys).toEqual(['has,comma']);
    });

    it('handles brackets in partition keys', () => {
      const allKeys = ['normal', '[bracketed]', 'another'];
      const selected = ['[bracketed]'];

      const text = partitionsToText(selected, allKeys);
      const parsed = spanTextToSelectionsOrError(allKeys, text);

      expect(parsed).not.toBeInstanceOf(Error);
      expect((parsed as any).selectedKeys).toEqual(['[bracketed]']);
    });

    it('handles quotes in partition keys', () => {
      const allKeys = ['normal', 'has"quote', 'another'];
      const selected = ['has"quote'];

      const text = partitionsToText(selected, allKeys);
      const parsed = spanTextToSelectionsOrError(allKeys, text);

      expect(parsed).not.toBeInstanceOf(Error);
      expect((parsed as any).selectedKeys).toEqual(['has"quote']);
    });
  });
});
```

---

## File Summary

### New Files to Create

| File | Purpose |
|------|---------|
| `src/partitions/PartitionSelection.g4` | ANTLR grammar definition |
| `src/partitions/generated/*.ts` | Auto-generated parser/lexer (4 files) |
| `src/partitions/AntlrPartitionSelectionVisitor.ts` | Visitor implementation |
| `src/partitions/parsePartitionSelection.ts` | Parser interface |
| `src/partitions/serializePartitionSelection.ts` | Serialization utilities |
| `src/scripts/generatePartitionSelection.ts` | Code generation script |
| `src/partitions/__tests__/parsePartitionSelection.test.ts` | Parser tests |
| `src/partitions/__tests__/serializePartitionSelection.test.ts` | Serializer tests |

### Files to Modify

| File | Changes |
|------|---------|
| `src/partitions/SpanRepresentation.tsx` | Replace parsing logic with ANTLR |
| `src/assets/usePartitionDimensionSelections.tsx` | Add URL encoding |
| `src/partitions/__tests__/SpanRepresentation.test.tsx` | Add special char tests |
| `package.json` | Add generation script |

### Files Unchanged (Use Dropdown Selection)

These files don't use text parsing and require no changes:
- `src/assets/DeleteDynamicPartitionsDialog.tsx`
- `src/partitions/OrdinalPartitionSelector.tsx`
- `src/partitions/OrdinalOrSingleRangePartitionSelector.tsx`
- `src/partitions/CreatePartitionDialog.tsx`

---

## Implementation Order

1. **Week 1: Core Parser**
   - Create grammar file
   - Set up generation script
   - Implement visitor
   - Write parser unit tests

2. **Week 2: Integration**
   - Update SpanRepresentation.tsx
   - Update URL serialization
   - Add integration tests

3. **Week 3: Testing & Polish**
   - Manual testing across all UI entry points
   - Edge case testing
   - Performance validation
   - Documentation updates

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Parser rejects valid legacy input | Low | High | Comprehensive backward compatibility tests |
| Performance regression | Low | Medium | Benchmark parser vs regex |
| URL encoding issues | Medium | Medium | Test with various browsers |
| ANTLR version conflicts | Low | Low | Pin antlr4ts version |

---

## Success Criteria

1. ✅ All existing partition selection tests pass
2. ✅ New tests for special character handling pass
3. ✅ Partition keys with `,`, `[`, `]`, `"`, `*`, `...` work correctly
4. ✅ URL bookmarks with special characters work after encoding
5. ✅ No performance regression in partition selection UI
