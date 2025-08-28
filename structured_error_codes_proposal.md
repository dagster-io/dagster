# Structured Error Code Enhancement Proposal

## Current State Analysis

### Current JSON Error Format

```json
{
  "error": "Unauthorized access"
}
```

**Problems:**

- No programmatic error handling for clients
- Requires string parsing to determine error type
- No HTTP status code context for CLI tools
- Inconsistent with GraphQL schema's structured error types

### GraphQL Schema Error Types

The schema contains 50+ structured error types including:

- `UnauthorizedError implements Error`
- `PythonError implements Error`
- `AssetNotFoundError implements Error`
- `InvalidSubsetError implements Error`
- `ConfigTypeNotFoundError implements Error`

## Proposed Enhancement

### Enhanced JSON Error Format

```json
{
  "error": "Unauthorized access",
  "code": "UNAUTHORIZED",
  "statusCode": 401,
  "type": "authentication_error"
}
```

### Error Code Categories

#### Authentication Errors (401)

- `UNAUTHORIZED` - Invalid or missing authentication
- `INVALID_TOKEN` - Token expired or malformed
- `AUTHENTICATION_REQUIRED` - Authentication needed

#### Authorization Errors (403)

- `FORBIDDEN` - Valid auth but insufficient permissions
- `INSUFFICIENT_PERMISSIONS` - Specific permission missing
- `RESOURCE_ACCESS_DENIED` - Cannot access specific resource

#### Client Errors (400)

- `INVALID_INPUT` - Malformed request parameters
- `VALIDATION_ERROR` - Input validation failed
- `MISSING_REQUIRED_FIELD` - Required parameter missing
- `INVALID_FILTER` - Filter syntax error

#### Not Found Errors (404)

- `RESOURCE_NOT_FOUND` - Deployment/asset/run not found
- `PIPELINE_NOT_FOUND` - Pipeline/job not found
- `CONFIG_TYPE_NOT_FOUND` - Configuration type missing

#### Server Errors (500)

- `INTERNAL_ERROR` - Unexpected server error
- `GRAPHQL_ERROR` - GraphQL execution failed
- `PYTHON_ERROR` - Python exception in user code
- `CONNECTION_ERROR` - External service unavailable

## Implementation Plan

### 1. Create Error Handling Utilities

Add to `dagster_dg_cli/cli/api/shared.py`:

```python
from typing import Dict, Any
import json

class ApiErrorCode:
    # Authentication
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_TOKEN = "INVALID_TOKEN"

    # Authorization
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Client errors
    INVALID_INPUT = "INVALID_INPUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # Not found
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PIPELINE_NOT_FOUND = "PIPELINE_NOT_FOUND"

    # Server errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    GRAPHQL_ERROR = "GRAPHQL_ERROR"

def format_error_response(
    message: str,
    error_code: str,
    status_code: int,
    error_type: str
) -> Dict[str, Any]:
    """Format consistent error response for JSON output."""
    return {
        "error": message,
        "code": error_code,
        "statusCode": status_code,
        "type": error_type
    }

def classify_exception(exception: Exception) -> Dict[str, Any]:
    """Map Python exceptions to structured error codes."""
    error_message = str(exception)

    # Authentication patterns
    if "authentication" in error_message.lower() or "unauthorized" in error_message.lower():
        return format_error_response(
            message=error_message,
            error_code=ApiErrorCode.UNAUTHORIZED,
            status_code=401,
            error_type="authentication_error"
        )

    # GraphQL specific errors
    if "GraphQL" in error_message:
        return format_error_response(
            message=error_message,
            error_code=ApiErrorCode.GRAPHQL_ERROR,
            status_code=500,
            error_type="server_error"
        )

    # Default to internal error
    return format_error_response(
        message=error_message,
        error_code=ApiErrorCode.INTERNAL_ERROR,
        status_code=500,
        error_type="server_error"
    )
```

### 2. Update API_CONVENTIONS.md

Replace current error handling section with:

````markdown
## Error Handling Standards

### JSON Error Format (--json flag):

```json
{
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "statusCode": 401,
  "type": "error_category"
}
```
````

### HTTP Status Code Mapping:

- **401**: Authentication errors (UNAUTHORIZED, INVALID_TOKEN)
- **403**: Authorization errors (FORBIDDEN, INSUFFICIENT_PERMISSIONS)
- **400**: Client errors (INVALID_INPUT, VALIDATION_ERROR)
- **404**: Resource not found (RESOURCE_NOT_FOUND, PIPELINE_NOT_FOUND)
- **500**: Server errors (INTERNAL_ERROR, GRAPHQL_ERROR)

### Error Types:

- `authentication_error`: Authentication required or failed
- `authorization_error`: Valid auth but insufficient permissions
- `client_error`: Invalid request parameters or format
- `server_error`: Internal server or GraphQL errors
- `not_found_error`: Requested resource doesn't exist

````

### 3. Update Command Implementation

Modify `deployment.py` error handling:

```python
except Exception as e:
    if output_json:
        error_response = classify_exception(e)
        click.echo(json.dumps(error_response), err=True)
    else:
        click.echo(f"Error querying Dagster Plus API: {e}", err=True)

    # Set exit code based on error type
    error_info = classify_exception(e)
    exit_code = error_info.get("statusCode", 1)
    raise click.ClickException(f"Failed to list deployments: {e}") from e
````

## Benefits

### For API Consumers

✅ **Programmatic Error Handling**: Clients can handle `error.code` without parsing strings  
✅ **HTTP Status Context**: Standard status codes for different error categories  
✅ **Error Classification**: `error.type` enables category-based error handling  
✅ **Consistent Format**: All API commands use same error structure

### For Development

✅ **GraphQL Alignment**: Maps GraphQL error types to CLI error codes  
✅ **Debugging**: Structured errors easier to log and analyze  
✅ **Monitoring**: Error codes enable better alerting and metrics  
✅ **Backward Compatibility**: Human-readable messages preserved

## Example Usage

```bash
# Command that fails
$ dg api deployment list --json
{
  "error": "Authentication required. Run 'dg plus login' to authenticate.",
  "code": "UNAUTHORIZED",
  "statusCode": 401,
  "type": "authentication_error"
}

# Client can handle programmatically
if error.code == "UNAUTHORIZED":
    prompt_for_login()
elif error.type == "client_error":
    show_usage_help()
```

This enhancement provides structured, machine-readable error information while maintaining human-readable messages for interactive use.
