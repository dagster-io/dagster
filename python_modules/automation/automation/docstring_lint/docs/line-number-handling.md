# Line Number Handling in Docstring Validation

## The Problem

Docstring validation errors need to report line numbers that developers can use to navigate directly to the problem in their editor. However, line numbers are complex because they flow through multiple transformations:

1. **Source file**: Original Python code with actual line numbers
2. **AST parsing**: Provides line numbers for function definitions and docstring nodes
3. **Content extraction**: `inspect.getdoc()` normalizes and processes the raw docstring
4. **Validation**: Operates on the processed content with its own line indexing

## The Solution: File-Relative Line Numbers

### Core Formula
```python
file_line = docstring_start_line + content_line - 1
```

Where:
- `docstring_start_line`: Line number from AST where docstring begins (from `docstring_node.lineno`)
- `content_line`: 1-indexed line number within the processed docstring content
- `file_line`: The actual line number in the source file that the user can navigate to

### Why This Works

The AST provides the exact line where the docstring starts in the source file. The processed content maintains the same line structure as the original (though leading/trailing whitespace may be removed). Therefore, a simple offset calculation gives us the correct file position.

## Detailed Example

### Source File: `example.py`
```python
195  @public
196  def asset(
197      name: Optional[str] = None,
198      key_prefix: Optional[Union[str, Sequence[str]]] = None,
199  ) -> Callable:
200      """Decorator to define an asset.
201      
202      This decorator is used to create asset definitions from functions.
203      
204      Argsxkx:  # ← ERROR: Invalid section header (line 204)
205          name: The name of the asset
206          key_prefix: Prefix for the asset key
207      
208      Returns:
209          The decorated function
210      """
211      pass
```

### AST Parsing Results
```python
# Function definition
function_node.lineno = 196  # Line where "def asset(" starts

# Docstring node  
docstring_node.lineno = 200  # Line where '"""Decorator...' starts
```

### Processed Docstring Content
After `inspect.getdoc()` normalization:
```
Line 1: "Decorator to define an asset."
Line 2: ""
Line 3: "This decorator is used to create asset definitions from functions."  
Line 4: ""
Line 5: "Argsxkx:"  # ← ERROR detected here
Line 6: "    name: The name of the asset"
Line 7: "    key_prefix: Prefix for the asset key"
Line 8: ""
Line 9: "Returns:"
Line 10: "    The decorated function"
```

### Line Number Calculation
When validation finds the error on line 5 of the processed content:
```python
docstring_start_line = 200  # From AST
content_line = 5           # "Argsxkx:" in processed content  
file_line = 200 + 5 - 1 = 204  # Actual file location ✓
```

The error message becomes:
```
Invalid section header: 'Argsxkx:'. Did you mean 'Args:'? (line 204)
```

## Implementation Details

### In `_read_docstring_from_file()`
```python
# Extract docstring and its starting line from AST
if target_node:
    if (target_node.body 
        and isinstance(target_node.body[0], ast.Expr)
        and isinstance(target_node.body[0].value, (ast.Str, ast.Constant))):
        
        docstring_node = target_node.body[0].value
        docstring_start_line = docstring_node.lineno  # ← Key: AST line number
        
        # Apply inspect.getdoc() normalization
        DummyWithDocstring.__doc__ = raw_docstring
        return inspect.getdoc(DummyWithDocstring), docstring_start_line
```

### In `_check_docstring_structure()`
```python
def calculate_file_line_number(docstring_line_number: int) -> Optional[int]:
    """Calculate file-relative line number from docstring-relative line number."""
    if docstring_start_line is None:
        return docstring_line_number  # Fall back to docstring-relative
    
    # The core calculation
    return docstring_start_line + docstring_line_number - 1

# Usage in validation
for i, line in enumerate(lines, 1):  # i is content_line
    if error_detected:
        result = result.with_error(
            f"Error message", 
            calculate_file_line_number(i)  # Converts to file_line
        )
```

## Edge Cases and Fallbacks

### No File Information Available
When `docstring_start_line` is `None` (e.g., when validating raw text without file context):
```python
if docstring_start_line is None:
    return docstring_line_number  # Return docstring-relative line
```

This ensures the system degrades gracefully and still provides useful line numbers.

### Multi-line String Literals
For docstrings that span multiple lines with explicit `\n` characters, the AST still correctly identifies the starting line of the string literal.

### Triple-quoted Strings
Both `"""` and `'''` style docstrings work correctly because the AST treats them uniformly as string nodes.

## Testing Line Number Handling

### Unit Test Pattern
```python
def test_file_relative_line_numbers():
    validator = DocstringValidator()
    
    docstring = '''Function with error.
    
    Argsxkx:  # Error on line 3 of content
        param: Description
    '''
    
    # Simulate file info
    docstring_start_line = 100
    result = validator.validate_docstring_text(
        docstring, "test.function", 
        file_path="/fake/path.py", 
        docstring_start_line=docstring_start_line
    )
    
    # Should report file line: 100 + 3 - 1 = 102
    assert "(line 102)" in result.errors[0]
```

### Manual Testing
```bash
# This should show file-relative line numbers
cd python_modules/automation  
python -m automation.docs_cli.main check docstrings --symbol=dagster.asset

# Look for:
# "Invalid section header: 'Argsxkx:'. Did you mean 'Args:'? (line 201)"
# Instead of: "(line 15)"
```

## Debugging Line Number Issues

### Common Problems

1. **Off-by-one errors**: Usually caused by incorrect offset calculation
   - Check: Is content_line 1-indexed as expected?
   - Check: Is docstring_start_line from AST correct?

2. **Missing file information**: Line numbers fall back to docstring-relative
   - Check: Is `_read_docstring_from_file()` finding the symbol?
   - Check: Is AST parsing successful?

3. **Wrong function matched**: AST finds wrong function with same name
   - Check: Is `candidates` selection logic choosing the right function?
   - Check: Are line number distances calculated correctly?

### Debugging Tools
```python
# Add debug logging to _check_docstring_structure()
print(f"docstring_start_line: {docstring_start_line}")
print(f"content_line: {i}")  
print(f"calculated file_line: {calculate_file_line_number(i)}")

# Verify AST parsing
import ast
with open(file_path) as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        print(f"Function {node.name} at line {node.lineno}")
```

## Performance Considerations

### AST Parsing Cost
Each call to `validate_symbol_docstring()` parses the source file with AST. This is acceptable for:
- Individual symbol validation
- Small batch validation
- Development-time checking

For large-scale validation, consider caching parsed ASTs.

### Memory Usage
The current implementation re-parses files for each symbol. For better efficiency when validating multiple symbols from the same file, consider:
- File-level caching of AST results
- Batch processing of symbols from the same file

## Future Improvements

### Enhanced Accuracy
- **Column information**: AST also provides `col_offset` for more precise positioning
- **Multi-line tokens**: Better handling of docstrings that span many lines
- **Syntax highlighting**: Integration with editor plugins for real-time validation

### Better Error Context
- **Show surrounding lines**: Include context around the error line
- **Highlight specific text**: Point to the exact problematic text within the line
- **Diff suggestions**: Show before/after for suggested fixes