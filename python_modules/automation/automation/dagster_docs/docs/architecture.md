# Architecture Overview

## System Purpose

The dagster_docs module is a sophisticated documentation validation system designed to enforce consistency across multiple documentation layers in the Dagster codebase:

1. **Python Docstrings** (Google-style format)
2. **Sphinx RST Documentation** (API reference files)
3. **`@public` API Decorators** (marking public APIs)
4. **Top-Level Package Exports** (what users can import)


## Core Components

### 1. CLI Interface Layer

#### main.py (Simple Interface)
- Direct docstring validation for single symbols
- Watch mode for development workflow
- Minimal interface focused on individual symbol validation

```bash
# Entry points:
# dagster-docs dagster.asset
# dagster-docs dagster.asset --watch
```

#### cli.py (Complex Commands)
- Multi-command interface using Click
- Groups: `check`, `ls`, `watch`
- Comprehensive validation workflows

#### commands/ Directory
- **check.py**: Multiple check types (docstrings, rst-symbols, public-symbols, exports, exclude-lists)
- **ls.py**: List symbols and their validation status
- **watch.py**: File watching capabilities

### 2. Core Validation Engine

#### validator.py (Heart of the System)

**Key Functions:**
- `validate_docstring_text(docstring, symbol_path)` - Core validation function
- `validate_symbol_docstring(dotted_path)` - Symbol-based validation
- `SymbolImporter` - Dynamic symbol importing and metadata extraction

**Validation Pipeline:**
1. **Import Phase**: Load symbol and extract metadata
2. **Napoleon Processing**: Convert Google-style to RST using Sphinx
3. **Rule Application**: Apply validation rules in sequence
4. **Result Aggregation**: Collect errors and warnings

```python
def validate_docstring_text(docstring: str, symbol_path: str) -> ValidationResult:
    # 1. Napoleon processing (Google-style to RST)
    processed_rst = GoogleDocstring(docstring)
    
    # 2. Create validation context
    context = ValidationContext(docstring, symbol_path, processed_rst)
    
    # 3. Apply validation rules
    for validator in [rst_syntax, section_header, sphinx_filter]:
        result = validator(context, result)
    
    return result
```

#### SymbolImporter Class
- Dynamic import handling with fallback strategies
- Source file location detection
- Metadata extraction (docstring, file path, line numbers)
- Support for module-level and symbol-level imports

### 3. Validation Rules System

#### Functional Architecture
- **ValidationFunction**: `(ValidationContext, ValidationResult) -> ValidationResult`
- **ValidationContext**: Immutable context with docstring, symbol path, processed RST
- **ValidationResult**: Immutable result with errors, warnings, parsing status

#### Available Rules
1. **RST Syntax Rule** (`rst_syntax_rule.py`): Validates RST syntax using Sphinx parsers
2. **Section Header Rule** (`section_header_rule.py`): Validates Google-style section headers
3. **Sphinx Filter Rule** (`sphinx_filter_rule.py`): Applies Sphinx-specific filters

#### Rule Pattern
```python
def create_rst_syntax_validator() -> ValidationFunction:
    def validate(context: ValidationContext, result: ValidationResult) -> ValidationResult:
        # Validation logic
        if error_found:
            return result.with_error("Error message")
        return result
    return validate
```

### 4. Public API Validation System

#### PublicApiValidator Class
Handles the complex three-way consistency checking between:
- `@public` decorated symbols in Python files
- RST documented symbols
- Top-level package exports

**Key Methods:**
- `find_public_symbols()` - AST parsing to find `@public` decorators
- `find_rst_documented_symbols()` - Regex parsing of RST files
- `validate_public_in_rst()` - Check `@public` symbols have RST docs
- `validate_rst_has_public()` - Check RST symbols have `@public` decorators

#### AST-Based Symbol Discovery
```python
def _extract_public_symbols_from_file(self, file_path: Path) -> list[PublicSymbol]:
    tree = ast.parse(file_content)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if self._has_public_decorator(node):
                # Extract symbol information
```

#### RST Symbol Extraction
```python
def _extract_symbols_from_rst(self, rst_file: Path) -> list[RstSymbol]:
    patterns = [
        (r"^\.\. autoclass:: ([^\s]+)", "autoclass"),
        (r"^\.\. autofunction:: ([^\s]+)", "autofunction"),
        (r"^\.\. autodecorator:: ([^\s]+)", "autodecorator"),
    ]
    # Parse RST files using regex patterns
```

### 5. File System Operations

#### file_discovery.py
- Git integration for changed file detection
- Path filtering and normalization
- Support for incremental validation workflows

#### watcher.py
- File system watching using platform-specific APIs
- Real-time validation during development
- Debounced change detection

#### path_converters.py
- Path conversion utilities for different contexts
- Handles Dagster-specific path conventions
- Module path to file path conversion

### 6. Configuration and Exclude Management

#### exclude_lists.py
Central configuration for incremental migration:
- `EXCLUDE_MISSING_RST`: `@public` symbols without RST docs
- `EXCLUDE_MISSING_PUBLIC`: RST symbols without `@public` decorators
- `EXCLUDE_MISSING_EXPORT`: `@public` symbols not exported at top-level

This allows teams to work incrementally toward full compliance while preventing new violations.

## Data Flow

### Single Symbol Validation Flow
```
Symbol Path → SymbolImporter → Docstring Extraction → Napoleon Processing → 
Rule Application → ValidationResult
```

### Public API Consistency Flow
```
Python Files → AST Parsing → @public Discovery
RST Files → Regex Parsing → RST Symbol Discovery
Package Exports → Dynamic Import → Export Discovery
↓
Three-way Consistency Validation
↓  
ValidationIssue[] (with exclude list filtering)
```

### Watch Mode Flow
```
File Change → Debounce → Symbol Re-import → Validation Pipeline → 
Console Output → Continue Watching
```

## Design Decisions

### Functional vs OOP Architecture
- **Rules System**: Functional approach for composability and testability
- **Data Models**: Record classes (`@record`) for immutability
- **Validation Logic**: Pure functions for predictable behavior
- **File Operations**: Class-based for state management

### Error Handling Strategy
- **Graceful Degradation**: Continue validation even if some rules fail
- **Specific Exception Handling**: Catch only expected exceptions (AttributeError, TypeError)
- **No Silent Failures**: Always log or report errors
- **Parsing vs Validation Errors**: Distinguish between parsing failures and content issues

### Performance Considerations
- **Lazy Loading**: Import symbols only when needed
- **Caching**: File system caches where appropriate
- **Incremental Processing**: Support for changed-files-only validation
- **Parallel Processing**: Designed to support future parallelization

### Extension Points
- **New Validation Rules**: Add to `docstring_rules/` and register in validator
- **New Check Commands**: Add to `commands/` and register in CLI
- **New File Types**: Extend file discovery and path conversion logic
- **New Exclude Categories**: Add to `exclude_lists.py`

## Dependencies

### Core Dependencies
- **Sphinx**: Napoleon docstring processing, RST parsing
- **Click**: CLI interface framework
- **AST**: Python source code parsing
- **Pathlib**: Modern path handling

### Dagster-Specific Dependencies
- **dagster._annotations**: `@public` decorator detection
- **dagster_shared.record**: Immutable data classes

This architecture enables comprehensive documentation validation while maintaining extensibility and performance for the large Dagster codebase.