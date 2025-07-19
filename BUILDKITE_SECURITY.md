# Buildkite Token Security Guide

## Security Issue: Hardcoded API Tokens

The security bot detected a hardcoded Buildkite Analytics API token in the source code. This is a security risk that needs to be addressed immediately.

## How to Fix Token Security

### 1. Remove Hardcoded Tokens

**NEVER** commit API tokens directly in source code. Instead, use environment variables:

```python
# BAD - Never do this
BUILDKITE_ANALYTICS_TOKEN = "bkua_b750f13ba09caac2e2eafe1daac6e4732e119c8e"

# GOOD - Use environment variables
analytics_token = os.environ.get("BUILDKITE_ANALYTICS_TOKEN")
```

### 2. Set Up Environment Variables

**For Local Development:**

```bash
# Set the token in your shell session
export BUILDKITE_ANALYTICS_TOKEN="your_actual_token_here"

# Or create a .env file (already gitignored)
echo "BUILDKITE_ANALYTICS_TOKEN=your_actual_token_here" > .env
```

**For CI/CD (Buildkite):**

```bash
# Add to your Buildkite pipeline environment variables
# Go to: Pipeline Settings > Environment Variables
BUILDKITE_ANALYTICS_TOKEN=your_actual_token_here
```

### 3. Token Management Best Practices

1. **Generate New Token**: If the old token was committed, revoke it and generate a new one
2. **Scope Permissions**: Only grant minimum required permissions
3. **Rotate Regularly**: Change tokens periodically for security
4. **Monitor Usage**: Check token usage in Buildkite Analytics dashboard

### 4. How to Get a New Token

1. Go to [Buildkite Analytics](https://buildkite.com/organizations/your-org/analytics)
2. Navigate to Settings > API Tokens
3. Create a new token with appropriate permissions
4. Copy the token and set it as an environment variable
5. **Never commit the token to source control**

### 5. Testing the Fix

```bash
# Set your token as environment variable
export BUILDKITE_ANALYTICS_TOKEN="your_new_token"

# Run tests with buildkite integration
BUILDKITE=1 python -m pytest -o addopts="-v" python_modules/dagster/dagster_tests/logging_tests/
```

## Token Security Checklist

- [ ] Remove hardcoded token from source code
- [ ] Add token to environment variables
- [ ] Verify `.env` files are in `.gitignore`
- [ ] Test token works via environment variable
- [ ] Revoke old token if it was committed
- [ ] Update CI/CD environment variables
- [ ] Document token setup for team members

## Environment Variables Needed

For Buildkite integration, set these environment variables:

```bash
BUILDKITE_ANALYTICS_TOKEN=your_token_here
BUILDKITE=true
BUILDKITE_ORGANIZATION_SLUG=dagster
BUILDKITE_PIPELINE_SLUG=unit-tests
```

Other variables are typically set automatically by Buildkite CI.

## File Structure

```
.env.example          # Template file - can be deployed (no real tokens)
.env                  # Local development file - ignored by git
.gitignore           # Contains: .env* and !.env.example
```

This ensures `.env.example` can be deployed as a template, but `.env` with real tokens stays local.
