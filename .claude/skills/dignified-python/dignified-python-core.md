---
---

# Dignified Python - Core Standards

This document contains the core Python coding standards that apply to 80%+ of Python code. These principles are loaded with every skill invocation.

For conditional loading of specialized patterns:

- CLI development → Load `cli-patterns.md`
- Subprocess operations → Load `subprocess.md`

---

## The Cornerstone: LBYL Over EAFP

**Look Before You Leap: Check conditions proactively, NEVER use exceptions for control flow.**

This is the single most important rule in dignified Python. Every pattern below flows from this principle.

```python
# ✅ CORRECT: Check first
if key in mapping:
    value = mapping[key]
    process(value)

# ❌ WRONG: Exception as control flow
try:
    value = mapping[key]
    process(value)
except KeyError:
    pass
```

---

## Exception Handling

### Core Principle

**ALWAYS use LBYL, NEVER EAFP for control flow**

LBYL means checking conditions before acting. EAFP (Easier to Ask for Forgiveness than Permission) means trying operations and catching exceptions. In dignified Python, we strongly prefer LBYL.

### Dictionary Access Patterns

```python
# ✅ CORRECT: Membership testing
if key in mapping:
    value = mapping[key]
    process(value)
else:
    handle_missing()

# ✅ ALSO CORRECT: .get() with default
value = mapping.get(key, default_value)
process(value)

# ✅ CORRECT: Check before nested access
if "config" in data and "timeout" in data["config"]:
    timeout = data["config"]["timeout"]

# ❌ WRONG: KeyError as control flow
try:
    value = mapping[key]
except KeyError:
    handle_missing()
```

### When Exceptions ARE Acceptable

Exceptions are ONLY acceptable at:

1. **Error boundaries** (CLI/API level)
2. **Third-party API compatibility** (when no alternative exists)
3. **Adding context before re-raising**

#### 1. Error Boundaries

```python
# ✅ ACCEPTABLE: CLI command error boundary
@click.command("create")
@click.pass_obj
def create(ctx: ErkContext, name: str) -> None:
    """Create a worktree."""
    try:
        create_worktree(ctx, name)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: Git command failed: {e.stderr}", err=True)
        raise SystemExit(1)
```

#### 2. Third-Party API Compatibility

```python
# ✅ ACCEPTABLE: Third-party API forces exception handling
def _get_bigquery_sample(sql_client, table_name):
    """
    BigQuery's TABLESAMPLE doesn't work on views.
    There's no reliable way to determine a priori whether
    a table supports TABLESAMPLE.
    """
    try:
        return sql_client.run_query(f"SELECT * FROM {table_name} TABLESAMPLE...")
    except Exception:
        return sql_client.run_query(f"SELECT * FROM {table_name} ORDER BY RAND()...")
```

> **The test for "no alternative exists"**: Can you validate or check the condition BEFORE calling the API? If yes (even using a different function/method), use LBYL. The exception only applies when the API provides NO way to determine success a priori—you literally must attempt the operation to know if it will work.

#### What Does NOT Qualify as Third-Party API Compatibility

Standard library functions with known LBYL alternatives do NOT qualify:

```python
# ❌ WRONG: int() has LBYL alternative (str.isdigit)
try:
    port = int(user_input)
except ValueError:
    port = 80

# ✅ CORRECT: Check before calling
if user_input.lstrip('-+').isdigit():
    port = int(user_input)
else:
    port = 80

# ❌ WRONG: datetime.fromisoformat() can be validated first
try:
    dt = datetime.fromisoformat(timestamp_str)
except ValueError:
    dt = None

# ✅ CORRECT: Validate format before parsing
def _is_iso_format(s: str) -> bool:
    return len(s) >= 10 and s[4] == "-" and s[7] == "-"

if _is_iso_format(timestamp_str):
    dt = datetime.fromisoformat(timestamp_str)
else:
    dt = None
```

#### 3. Adding Context Before Re-raising

```python
# ✅ ACCEPTABLE: Adding context before re-raising
try:
    process_file(config_file)
except yaml.YAMLError as e:
    raise ValueError(f"Failed to parse config file {config_file}: {e}") from e
```

### Exception Chaining (B904 Lint Compliance)

**Ruff rule B904** requires explicit exception chaining when raising inside an `except` block. This prevents losing the original traceback.

```python
# ✅ CORRECT: Chain to preserve context
try:
    parse_config(path)
except ValueError as e:
    click.echo(json.dumps({"success": False, "error": str(e)}))
    raise SystemExit(1) from e  # Preserves traceback

# ✅ CORRECT: Explicitly break chain when intentional
try:
    fetch_from_cache(key)
except KeyError:
    # Original exception is not relevant to caller
    raise ValueError(f"Unknown key: {key}") from None

# ❌ WRONG: Missing exception chain (B904 violation)
try:
    parse_config(path)
except ValueError:
    raise SystemExit(1)  # Lint error: missing 'from e' or 'from None'

# ✅ CORRECT: CLI error boundary with JSON output
try:
    result = some_operation()
except RuntimeError as e:
    click.echo(json.dumps({"success": False, "error": str(e)}))
    raise SystemExit(0) from None  # Exception is in JSON, traceback irrelevant to CLI user
```

**When to use each:**

- `from e` - Preserve original exception for debugging
- `from None` - Intentionally suppress original (e.g., transforming exception type, CLI JSON output)

### Exception Anti-Patterns

**❌ Never swallow exceptions silently**

Even at error boundaries, you must at least log/warn so issues can be diagnosed:

```python
# ❌ WRONG: Silent exception swallowing
try:
    risky_operation()
except:
    pass

# ❌ WRONG: Silent swallowing even at error boundary
try:
    optional_feature()
except Exception:
    pass  # Silent - impossible to diagnose issues

# ✅ CORRECT: Let exceptions bubble up (default)
risky_operation()

# ✅ CORRECT: At error boundaries, log the exception
try:
    optional_feature()
except Exception as e:
    logging.warning("Optional feature failed: %s", e)  # Diagnosable
```

**❌ Never use silent fallback behavior**

```python
# ❌ WRONG: Silent fallback masks failure
def process_text(text: str) -> dict:
    try:
        return llm_client.process(text)
    except Exception:
        return regex_parse_fallback(text)

# ✅ CORRECT: Let error bubble to boundary
def process_text(text: str) -> dict:
    return llm_client.process(text)
```

---

## Path Operations

### The Golden Rule

**ALWAYS check `.exists()` BEFORE `.resolve()` or `.is_relative_to()`**

### Why This Matters

- `.resolve()` raises `OSError` for non-existent paths
- `.is_relative_to()` raises `ValueError` for invalid comparisons
- Checking `.exists()` first avoids exceptions entirely (LBYL!)

### Correct Patterns

```python
from pathlib import Path

# ✅ CORRECT: Check exists first
for wt_path in worktree_paths:
    if wt_path.exists():
        wt_path_resolved = wt_path.resolve()
        if current_dir.is_relative_to(wt_path_resolved):
            current_worktree = wt_path_resolved
            break

# ❌ WRONG: Using exceptions for path validation
try:
    wt_path_resolved = wt_path.resolve()
    if current_dir.is_relative_to(wt_path_resolved):
        current_worktree = wt_path_resolved
except (OSError, ValueError):
    continue
```

### Pathlib Best Practices

**Always Use Pathlib (Never os.path)**

```python
# ✅ CORRECT: Use pathlib.Path
from pathlib import Path

config_file = Path.home() / ".config" / "app.yml"
if config_file.exists():
    content = config_file.read_text(encoding="utf-8")

# ❌ WRONG: Use os.path
import os.path
config_file = os.path.join(os.path.expanduser("~"), ".config", "app.yml")
```

**Always Specify Encoding**

```python
# ✅ CORRECT: Always specify encoding
content = path.read_text(encoding="utf-8")
path.write_text(data, encoding="utf-8")

# ❌ WRONG: Default encoding
content = path.read_text()  # Platform-dependent!
```

---

## Import Organization

### Core Rules

1. **Default: ALWAYS place imports at module level**
2. **Use absolute imports only** (no relative imports)
3. **Inline imports only for specific exceptions** (see below)

### Correct Import Patterns

```python
# ✅ CORRECT: Module-level imports
import json
import click
from pathlib import Path
from erk.config import load_config

def my_function() -> None:
    data = json.loads(content)
    click.echo("Processing")
    config = load_config()

# ❌ WRONG: Inline imports without justification
def my_function() -> None:
    import json  # NEVER do this
    import click  # NEVER do this
    data = json.loads(content)
```

### Legitimate Inline Import Patterns

#### 1. Circular Import Prevention

```python
# commands/sync.py
def register_commands(cli_group):
    """Register commands with CLI group (avoids circular import)."""
    from myapp.cli import sync_command  # Breaks circular dependency
    cli_group.add_command(sync_command)
```

**When to use:**

- CLI command registration
- Plugin systems with bidirectional dependencies
- Lazy loading to break import cycles

#### 2. Conditional Feature Imports

```python
def process_data(data: dict, dry_run: bool = False) -> None:
    if dry_run:
        # Inline import: Only needed for dry-run mode
        from myapp.dry_run import NoopProcessor
        processor = NoopProcessor()
    else:
        processor = RealProcessor()
    processor.execute(data)
```

**When to use:**

- Debug/verbose mode utilities
- Dry-run mode wrappers
- Optional feature modules
- Platform-specific implementations

#### 3. TYPE_CHECKING Imports

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myapp.models import User  # Only for type hints

def process_user(user: "User") -> None:
    ...
```

**When to use:**

- Avoiding circular dependencies in type hints
- Forward declarations

#### 4. Startup Time Optimization (Rare)

Some packages have genuinely heavy import costs (pyspark, jupyter ecosystem, large ML frameworks). Deferring these imports can improve CLI startup time.

**However, apply "innocent until proven guilty":**

- Default to module-level imports
- Only defer imports when you have MEASURED evidence of startup impact
- Document the measured cost in a comment

```python
# ✅ ACCEPTABLE: Measured heavy import (adds 800ms to startup)
def run_spark_job(config: SparkConfig) -> None:
    from pyspark.sql import SparkSession  # Heavy: 800ms import time
    session = SparkSession.builder.getOrCreate()
    ...

# ❌ WRONG: Speculative deferral without measurement
def check_staleness(project_dir: Path) -> None:
    # Inline imports to avoid import-time side effects  <- WRONG: no evidence
    from myapp.staleness import get_version
    ...
```

**When NOT to defer:**

- Standard library modules
- Lightweight internal modules
- Modules you haven't measured
- "Just in case" optimization

### Absolute vs Relative Imports

```python
# ✅ CORRECT: Absolute import
from erk.config import load_config

# ❌ WRONG: Relative import
from .config import load_config
```

---

## Import-Time Side Effects

### Core Rule

**Avoid computation and side effects at import time. Defer to function calls.**

Module-level code runs when the module is imported. Side effects at import time cause:

1. **Slower startup** - Every import triggers computation
2. **Test brittleness** - Hard to mock/control behavior
3. **Circular import issues** - Dependencies evaluated too early
4. **Unpredictable order** - Import order affects behavior

### Common Anti-Patterns

```python
# ❌ WRONG: Path computed at import time
SESSION_ID_FILE = Path(".erk/scratch/current-session-id")

def get_session_id() -> str | None:
    if SESSION_ID_FILE.exists():
        return SESSION_ID_FILE.read_text(encoding="utf-8")
    return None

# ❌ WRONG: Config loaded at import time
CONFIG = load_config()  # I/O at import!

# ❌ WRONG: Connection established at import time
DB_CLIENT = DatabaseClient(os.environ["DB_URL"])  # Side effect at import!
```

### Correct Patterns

**Use `@cache` for deferred computation:**

```python
from functools import cache

# ✅ CORRECT: Defer computation until first call
@cache
def _session_id_file_path() -> Path:
    """Return path to session ID file (cached after first call)."""
    return Path(".erk/scratch/current-session-id")

def get_session_id() -> str | None:
    session_file = _session_id_file_path()
    if session_file.exists():
        return session_file.read_text(encoding="utf-8")
    return None
```

**Use functions for resources:**

```python
# ✅ CORRECT: Defer resource creation to function call
@cache
def get_config() -> Config:
    """Load config on first call, cache result."""
    return load_config()

@cache
def get_db_client() -> DatabaseClient:
    """Create database client on first call."""
    return DatabaseClient(os.environ["DB_URL"])
```

### When Module-Level Constants ARE Acceptable

Simple, static values that don't involve computation or I/O:

```python
# ✅ ACCEPTABLE: Static constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
SUPPORTED_FORMATS = frozenset({"json", "yaml", "toml"})
```

### Decision Checklist

Before writing module-level code:

- [ ] Does this involve any computation (even `Path()` construction)?
- [ ] Does this involve I/O (file, network, environment)?
- [ ] Could this fail or raise exceptions?
- [ ] Would tests need to mock this value?

If any answer is "yes", wrap in a `@cache`-decorated function instead.

---

## Dependency Injection

### Core Rule

**Use ABC for interfaces, NEVER Protocol**

### ABC Interface Pattern

```python
# ✅ CORRECT: Use ABC for interfaces
from abc import ABC, abstractmethod

class Repository(ABC):
    @abstractmethod
    def save(self, entity: Entity) -> None:
        """Save entity to storage."""
        ...

    @abstractmethod
    def load(self, id: str) -> Entity:
        """Load entity by ID."""
        ...

class PostgresRepository(Repository):
    def save(self, entity: Entity) -> None:
        # Implementation
        pass

    def load(self, id: str) -> Entity:
        # Implementation
        pass

# ❌ WRONG: Using Protocol
from typing import Protocol

class Repository(Protocol):
    def save(self, entity: Entity) -> None: ...
    def load(self, id: str) -> Entity: ...
```

### Benefits of ABC

1. **Explicit inheritance** - Clear class hierarchy
2. **Runtime validation** - Errors if abstract methods not implemented
3. **Better IDE support** - Autocomplete and refactoring work better
4. **Documentation** - Clear contract definition

### Complete DI Example

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Define the interface
class DataStore(ABC):
    @abstractmethod
    def get(self, key: str) -> str | None:
        """Retrieve value by key."""
        ...

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """Store value with key."""
        ...

# Real implementation
class RedisStore(DataStore):
    def get(self, key: str) -> str | None:
        return self.client.get(key)

    def set(self, key: str, value: str) -> None:
        self.client.set(key, value)

# Fake for testing
class FakeStore(DataStore):
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        if key not in self._data:
            return None
        return self._data[key]

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

# Business logic accepts interface
@dataclass
class Service:
    store: DataStore  # Depends on abstraction

    def process(self, item: str) -> None:
        cached = self.store.get(item)
        if cached is None:
            result = expensive_computation(item)
            self.store.set(item, result)
        else:
            result = cached
        use_result(result)
```

---

## Performance Guidelines

### Properties Must Be O(1)

```python
# ❌ WRONG: Property doing I/O
@property
def size(self) -> int:
    return self._fetch_from_db()

# ✅ CORRECT: Explicit method name
def fetch_size_from_db(self) -> int:
    return self._fetch_from_db()

# ✅ CORRECT: O(1) property
@property
def size(self) -> int:
    return self._cached_size
```

### Magic Methods Must Be O(1)

```python
# ❌ WRONG: __len__ doing iteration
def __len__(self) -> int:
    return sum(1 for _ in self._items)

# ✅ CORRECT: O(1) __len__
def __len__(self) -> int:
    return self._count
```

---

## Using `typing.cast()`

### Core Rule

**ALWAYS verify `cast()` with a runtime assertion, unless there's a documented reason not to.**

`typing.cast()` is a compile-time only construct—it tells the type checker to trust you but performs no runtime verification. If your assumption is wrong, you'll get silent misbehavior instead of a clear error.

### Required Pattern

```python
from collections.abc import MutableMapping
from typing import Any, cast

# ✅ CORRECT: Runtime assertion before cast
assert isinstance(doc, MutableMapping), f"Expected MutableMapping, got {type(doc)}"
cast(dict[str, Any], doc)["key"] = value

# ✅ CORRECT: Alternative with hasattr for duck typing
assert hasattr(obj, '__setitem__'), f"Expected subscriptable, got {type(obj)}"
cast(dict[str, Any], obj)["key"] = value
```

### Anti-Pattern

```python
# ❌ WRONG: Cast without runtime verification
cast(dict[str, Any], doc)["key"] = value  # If doc isn't a dict-like, silent failure
```

### When to Skip Runtime Verification

**Default: Always add the assertion when cost is trivial (O(1) checks like `in`, `isinstance`).**

Skip the assertion only in these narrow cases:

1. **Immediately after a type guard**: The check was just performed and would be redundant

   ```python
   if isinstance(value, str):
       # No assertion needed - we just checked
       result = cast(str, value).upper()
   ```

2. **Performance-critical hot path**: Add a comment explaining the measured overhead
   ```python
   # Skip assertion: called 10M times/sec, isinstance adds 15% overhead
   # Type invariant maintained by _validate_input() at entry point
   cast(int, cached_value)
   ```

**What is NOT a valid reason to skip:**

- "Click validates the choice set" - Add assertion anyway; cost is trivial
- "The library guarantees the type" - Add assertion anyway; defense in depth
- "It's obvious from context" - Add assertion anyway; future readers benefit

### Why This Matters

- **Silent bugs are worse than loud bugs**: An assertion failure gives you a stack trace and clear error message
- **Documentation**: The assertion documents your assumption for future readers
- **Defense in depth**: Third-party libraries can change behavior between versions

---

## Programmatically Significant Strings

**Use `Literal` types for strings that have programmatic meaning.**

When strings represent a fixed set of valid values (error codes, status values, command types), model them in the type system using `Literal`.

### Why This Matters

1. **Type safety** - Typos caught at type-check time, not runtime
2. **IDE support** - Autocomplete shows valid options
3. **Documentation** - Valid values are explicit in the code
4. **Refactoring** - Rename operations work correctly

### Naming Convention

**Use kebab-case for all internal Literal string values:**

```python
# ✅ CORRECT: kebab-case for internal values
IssueCode = Literal["orphan-state", "orphan-dir", "missing-branch"]
ErrorType = Literal["not-found", "invalid-format", "timeout-exceeded"]
```

**Exception: When modeling external systems, match the external API's convention:**

```python
# ✅ CORRECT: Match GitHub API's UPPER_CASE
PRState = Literal["OPEN", "MERGED", "CLOSED"]

# ✅ CORRECT: Match GitHub Actions API's lowercase
WorkflowStatus = Literal["completed", "in_progress", "queued"]
```

The rule is: kebab-case by default, external convention when modeling external APIs.

### Pattern

```python
from dataclasses import dataclass
from typing import Literal

# ✅ CORRECT: Define a type alias for the valid values
IssueCode = Literal["orphan-state", "orphan-dir", "missing-branch"]

@dataclass(frozen=True)
class Issue:
    code: IssueCode
    message: str

def check_state() -> list[Issue]:
    issues: list[Issue] = []
    if problem_detected:
        issues.append(Issue(code="orphan-state", message="description"))  # Type-checked!
    return issues

# ❌ WRONG: Bare strings without type constraint
def check_state() -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    issues.append(("orphen-state", "desc"))  # Typo goes unnoticed!
    return issues
```

### When to Use Literal

- Error/issue codes
- Status values (pending, complete, failed)
- Command types or action names
- Configuration keys with fixed valid values
- Any string that is compared programmatically

### Decision Checklist

Before using a bare `str` type, ask:

- Is this string compared with `==` or `in` anywhere?
- Is there a fixed set of valid values?
- Would a typo in this string cause a bug?

If any answer is "yes", use `Literal` instead.

---

## Anti-Patterns

### Preserving Unnecessary Backwards Compatibility

```python
# ❌ WRONG: Keeping old API unnecessarily
def process_data(data: dict, legacy_format: bool = False) -> Result:
    if legacy_format:
        return legacy_process(data)
    return new_process(data)

# ✅ CORRECT: Break and migrate immediately
def process_data(data: dict) -> Result:
    return new_process(data)
```

### No Re-Exports: One Canonical Import Path

**Core Principle:** Every symbol has exactly one import path. Never re-export.

This rule applies to:

- `__all__` exports in `__init__.py`
- Re-exporting symbols from other modules
- Shim modules that import and expose symbols from elsewhere

```python
# ❌ WRONG: __all__ exports create duplicate import paths
# myapp/__init__.py
from myapp.core import Process
__all__ = ["Process"]

# Now Process can be imported two ways - breaks grepability

# ❌ WRONG: Re-exporting symbols in a shim module
# myapp/compat.py
from myapp.core import Process, Config, execute
# These can now be imported from myapp.compat OR myapp.core

# ✅ CORRECT: Empty __init__.py, import from canonical location
# from myapp.core import Process

# ✅ CORRECT: Shim imports only what it needs for its own use
# myapp/cli_entry.py (needs the click command for CLI registration)
from myapp.core import main_command  # Only import what this module uses
# Other code imports Process, Config from myapp.core directly
```

**Why prohibited:**

1. Breaks grepability - hard to find all usages
2. Confuses static analysis tools
3. Impairs refactoring safety
4. Violates explicit > implicit
5. Creates confusion about canonical import location

**Shim modules:** When a module must exist as an entry point (e.g., for plugin systems or CLI registration), import only the minimum symbols needed for that purpose. Document that other symbols should be imported from the canonical location.

**CI Review Behavior:**

- New `__all__` usage → Always flagged
- Modifications to existing `__all__` (adding exports) → Flagged
- Pre-existing `__all__` in file only moved/refactored (unchanged) → Skipped

The principle: If you're actively modifying a file, fix its violations. If you're just moving it, don't force unrelated cleanup.

**When re-exports ARE required:** Some systems (like plugin entry points) require a module to exist at a specific path and expose a specific symbol. In these cases, use the explicit `import X as X` syntax to signal intentional re-export:

```python
# ✅ CORRECT: Explicit re-export syntax for required entry points
# This shim exists because the plugin system expects a module at this path
from myapp.core.feature import my_function as my_function

# ❌ WRONG: Plain import looks like unused import to linters
from myapp.core.feature import my_function  # ruff will flag as F401
```

The `as X` syntax is the PEP 484 standard for indicating intentional re-exports. It tells both linters and readers that this import is meant to be consumed from this module.

### Default Parameter Values Are Dangerous

**Avoid default parameter values unless absolutely necessary.** They are a significant source of bugs.

**Why defaults are dangerous:**

1. **Silent incorrect behavior** - Callers forget to pass a parameter and get unexpected results
2. **Hidden coupling** - The default encodes an assumption that may not hold for all callers
3. **Audit difficulty** - Hard to verify all call sites are using the right value
4. **Refactoring hazard** - Adding a new parameter with a default doesn't trigger errors at existing call sites

```python
# ❌ DANGEROUS: Default that might be wrong for some callers
def process_file(path: Path, encoding: str = "utf-8") -> str:
    return path.read_text(encoding=encoding)

# Caller forgets encoding, silently gets wrong behavior for legacy file
content = process_file(legacy_latin1_file)  # Bug: should be encoding="latin-1"

# ✅ SAFER: Require explicit choice
def process_file(path: Path, encoding: str) -> str:
    return path.read_text(encoding=encoding)

# Caller must think about encoding
content = process_file(legacy_latin1_file, encoding="latin-1")
```

**When you discover a default is never overridden, eliminate it:**

```python
# If every call site uses the default...
activate_worktree(ctx, repo, path, script, "up", preserve_relative_path=True)  # Always True
activate_worktree(ctx, repo, path, script, "down", preserve_relative_path=True)  # Always True

# ✅ CORRECT: Remove the parameter entirely
def activate_worktree(ctx, repo, path, script, command_name) -> None:
    # Always preserve relative path - it's just the behavior
    ...
```

**Acceptable uses of defaults:**

1. **Truly optional behavior** - Where the default is correct for 95%+ of callers
2. **Backwards compatibility** - When adding a parameter to existing API (temporary)
3. **Test conveniences** - Defaults that simplify test setup

**When reviewing code with defaults, ask:**

- Do all call sites actually want this default?
- Would a caller forgetting this parameter cause a bug?
- Is there a safer design that makes the choice explicit?

---

### Speculative Tests

```python
# ❌ FORBIDDEN: Tests for future features
# def test_feature_we_might_add():
#     pass

# ✅ CORRECT: TDD for current implementation
def test_feature_being_built_now():
    result = new_feature()
    assert result == expected
```

---

### Speculative Test Infrastructure

**Don't add parameters to fakes "just in case" they might be useful for testing.**

Fakes should mirror production interfaces. Adding test-only configuration knobs that never get used creates dead code and false complexity.

```python
# ❌ WRONG: Test-only parameter that's never used in production
class FakeGitHub:
    def __init__(
        self,
        prs: dict[str, PullRequestInfo] | None = None,
        rate_limited: bool = False,  # "Might test this later"
    ) -> None:
        self._rate_limited = rate_limited  # Never set to True anywhere

# ✅ CORRECT: Only add infrastructure when you need it
class FakeGitHub:
    def __init__(
        self,
        prs: dict[str, PullRequestInfo] | None = None,
    ) -> None:
        ...
```

**The test for this:** If grep shows a parameter is only ever passed in test files, and those tests are testing hypothetical scenarios rather than actual production behavior, delete both the parameter and the tests.

---

## Code Organization

### Declare Variables Close to Use

**Variables should be declared as close as possible to where they are used.** Avoid early declarations that pollute scope and obscure data flow.

```python
# ❌ WRONG: Variable declared far from use
def process_data(ctx, items):
    # Declared here...
    result_path = compute_result_path(ctx)

    # 20+ lines of other logic...
    validate_items(items)
    transformed = transform_items(items)
    check_permissions(ctx)

    # ...used here, far below
    save_to_path(transformed, result_path)

# ✅ CORRECT: Inline at use site
def process_data(ctx, items):
    validate_items(items)
    transformed = transform_items(items)
    check_permissions(ctx)

    # Computed right where it's needed
    save_to_path(transformed, compute_result_path(ctx))
```

**When passing to functions, prefer inline computation:**

```python
# ❌ WRONG: Unnecessary intermediate variable
worktrees = ctx.git.list_worktrees(repo.root)
relative_path = compute_relative_path(worktrees, ctx.cwd)  # Only used once below

activation_script = render_activation_script(
    worktree_path=target_path,
    target_subpath=relative_path,
)

# ✅ CORRECT: Inline the computation
worktrees = ctx.git.list_worktrees(repo.root)

activation_script = render_activation_script(
    worktree_path=target_path,
    target_subpath=compute_relative_path(worktrees, ctx.cwd),
)
```

**Exception:** If a variable is used multiple times or if inline computation hurts readability, a local variable is appropriate.

### Don't Destructure Objects Into Single-Use Locals

**Prefer direct attribute access over intermediate variables.** When you have an object, access its attributes at the point of use rather than extracting them into local variables that are only used once.

```python
# ❌ WRONG: Unnecessary field extraction
result = fetch_user(user_id)
name = result.name      # only used once below
email = result.email    # only used once below
role = result.role      # only used once below

send_notification(name, email, role)

# ✅ CORRECT: Access fields directly
user = fetch_user(user_id)
send_notification(user.name, user.email, user.role)
```

**Why this matters:**

- Reduces cognitive load - no need to track extra variable names
- Makes data flow clearer - you can see where values come from
- Avoids stale variable bugs when object is mutated
- The object name (`user`) provides context; `name` alone is ambiguous

**Exception:** Extract to a local when:

- The value is used multiple times
- The expression is complex and a name improves readability
- You need to modify the value before use

---

### Indentation Depth Limit

**Maximum indentation: 4 levels**

```python
# ❌ WRONG: Too deeply nested
def process_items(items):
    for item in items:
        if item.valid:
            for child in item.children:
                if child.enabled:
                    for grandchild in child.descendants:
                        # 5 levels deep!
                        pass

# ✅ CORRECT: Extract helper functions
def process_items(items):
    for item in items:
        if item.valid:
            process_children(item.children)

def process_children(children):
    for child in children:
        if child.enabled:
            process_descendants(child.descendants)
```

---

## Backwards Compatibility Philosophy

**Default stance: NO backwards compatibility preservation**

Only preserve backwards compatibility when:

- Code is clearly part of public API
- User explicitly requests it
- Migration cost is prohibitively high (rare)

Benefits:

- Cleaner, maintainable codebase
- Faster iteration
- No legacy code accumulation
- Simpler mental models

---

## Decision Checklist

### Before writing `try/except`:

- [ ] Is this at an error boundary? (CLI/API level)
- [ ] Can I check the condition proactively? (LBYL)
- [ ] Am I adding meaningful context, or just hiding?
- [ ] Is third-party API forcing me to use exceptions? (No LBYL check exists—not even format validation)
- [ ] Have I encapsulated the violation?
- [ ] Am I catching specific exceptions, not broad?
- [ ] If catching at error boundary, am I logging/warning? (Never silently swallow)

**Default: Let exceptions bubble up**

### Before path operations:

- [ ] Did I check `.exists()` before `.resolve()`?
- [ ] Did I check `.exists()` before `.is_relative_to()`?
- [ ] Am I using `pathlib.Path`, not `os.path`?
- [ ] Did I specify `encoding="utf-8"`?

### Before using `typing.cast()`:

- [ ] Have I added a runtime assertion to verify the cast?
- [ ] Is the assertion cost trivial (O(1))? If yes, always add it.
- [ ] If skipping, is it because I just performed an isinstance check (redundant)?
- [ ] If skipping for performance, have I documented the measured overhead?

**Default: Always add runtime assertion before cast when cost is trivial**

### Before preserving backwards compatibility:

- [ ] Did the user explicitly request it?
- [ ] Is this a public API with external consumers?
- [ ] Have I documented why it's needed?
- [ ] Is migration cost prohibitively high?

**Default: Break the API and migrate callsites immediately**

### Before inline imports:

- [ ] Is this to break a circular dependency?
- [ ] Is this for TYPE_CHECKING?
- [ ] Is this for conditional features?
- [ ] If for startup time: Have I MEASURED the import cost?
- [ ] If for startup time: Is the cost significant (>100ms)?
- [ ] If for startup time: Have I documented the measured cost in a comment?
- [ ] Have I documented why the inline import is needed?

**Default: Module-level imports**

### Before importing/re-exporting symbols:

- [ ] Is there already a canonical location for this symbol?
- [ ] Am I creating a second import path for the same symbol?
- [ ] If this is a shim module, am I importing only what's needed for this module's purpose?
- [ ] Have I avoided `__all__` exports?

**Default: Import from canonical location, never re-export**

### Before declaring a local variable:

- [ ] Is this variable used more than once?
- [ ] Is this variable used close to where it's declared?
- [ ] Would inlining the computation hurt readability?
- [ ] Am I extracting object fields into locals that are only used once?

**Default: Inline single-use computations at the call site; access object attributes directly**

### Before adding a default parameter value:

- [ ] Do 95%+ of callers actually want this default?
- [ ] Would forgetting to pass this parameter cause a subtle bug?
- [ ] Is there a safer design that makes the choice explicit?
- [ ] If the default is never overridden anywhere, should this parameter exist at all?

**Default: Require explicit values; eliminate unused defaults**
