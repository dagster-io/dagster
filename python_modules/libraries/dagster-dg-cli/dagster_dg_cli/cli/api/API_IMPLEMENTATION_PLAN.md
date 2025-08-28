# Dagster Plus API CLI Implementation Plan

## Standard Verbs Pattern

- **list** - List all resources with filtering/pagination
- **view <id>** - Show detailed information about specific resource
- **create** - Create new resource (where applicable)
- **update <id>** - Update existing resource (where applicable)
- **delete <id>** - Remove resource (where applicable)

---

## **Tier 1: Core Infrastructure**

### 1. **deployment** ✅ _Already implemented_

```bash
# Implemented
dg api deployment list [--json]

# Future verbs
dg api deployment view <name> [--json]
dg api deployment create --name <name> --type <serverless|hybrid>
dg api deployment update <name> [--settings <file>]
dg api deployment delete <name>
```

**GraphQL**: `fullDeployments`, `currentDeployment`, `deploymentByName`

### 2. **secret**

```bash
dg api secret list [--location <name>] [--scope <deployment|organization>] [--json]
dg api secret view <name> [--location <name>] [--json]
dg api secret create --name <name> --value <value> [--location <name>] [--scope <scope>]
dg api secret update <name> --value <value> [--location <name>]
dg api secret delete <name> [--location <name>]
```

**GraphQL**: `secretsOrError`

### 3. **agent**

```bash
dg api agent list [--json]
dg api agent view <id> [--json]
# Agents are typically managed via configuration, not CRUD operations
```

**GraphQL**: `agents`

### 4. **run**

```bash
dg api run list [--status <status>] [--pipeline <name>] [--limit <n>] [--json]
dg api run view <run-id> [--json]
dg api run create --pipeline <name> [--config <file>] [--tags <key=value>]
dg api run terminate <run-id>
dg api run delete <run-id>
```

**GraphQL**: `runsOrError`, `pipelineRunsOrError`, `runOrError`

### 5. **asset**

```bash
dg api asset list [--prefix <path>] [--limit <n>] [--json]
dg api asset view <asset-key> [--json]
# Assets are typically managed through code, not direct API
```

**GraphQL**: `assetsOrError`, `assetNodes`, `assetOrError`

---

## **Tier 2: Cloud Management**

### 6. **user**

```bash
dg api user list [--json]
dg api user view <user-id> [--json]
dg api user create --email <email> --role <role>
dg api user update <user-id> --role <role>
dg api user delete <user-id>
```

**GraphQL**: `usersOrError`

### 7. **team**

```bash
dg api team list [--json]
dg api team view <team-id> [--json]
dg api team create --name <name> [--members <user-id1,user-id2>]
dg api team update <team-id> [--add-member <user-id>] [--remove-member <user-id>]
dg api team delete <team-id>
```

**GraphQL**: `teamPermissions`

### 8. **alert-policy**

```bash
dg api alert-policy list [--json]
dg api alert-policy view <policy-id> [--json]
dg api alert-policy create --name <name> --config <file>
dg api alert-policy update <policy-id> --config <file>
dg api alert-policy delete <policy-id>
```

**GraphQL**: `alertPolicies`, `alertPolicyById`

### 9. **code-location**

```bash
dg api code-location list [--json]
dg api code-location view <location-name> [--json]
dg api code-location create --name <name> --image <image> --config <file>
dg api code-location update <location-name> --image <image> [--config <file>]
dg api code-location delete <location-name>
```

**GraphQL**: `repositoriesOrError`, `repositoryOrError`

### 10. **workspace**

```bash
dg api workspace list [--json]
dg api workspace view [--json]
dg api workspace update --config <file>
# Workspace is typically singular per deployment
```

**GraphQL**: `workspaceOrError`

---

## **Tier 3: Extended Management**

### 11. **check**

```bash
dg api check list [--asset <asset-key>] [--status <status>] [--json]
dg api check view <check-name> --asset <asset-key> [--json]
# Checks are defined in code, not directly manageable
```

**GraphQL**: `assetCheckExecutions`

### 12. **schedule**

```bash
dg api schedule list [--location <name>] [--status <running|stopped>] [--json]
dg api schedule view <schedule-name> --location <name> [--json]
dg api schedule start <schedule-name> --location <name>
dg api schedule stop <schedule-name> --location <name>
```

**GraphQL**: `schedulesOrError`, `scheduleOrError`

### 13. **sensor**

```bash
dg api sensor list [--location <name>] [--status <running|stopped>] [--json]
dg api sensor view <sensor-name> --location <name> [--json]
dg api sensor start <sensor-name> --location <name>
dg api sensor stop <sensor-name> --location <name>
```

**GraphQL**: `sensorsOrError`, `sensorOrError`

### 14. **backfill**

```bash
dg api backfill list [--status <status>] [--json]
dg api backfill view <backfill-id> [--json]
dg api backfill create --asset <asset-key> --partitions <range>
dg api backfill cancel <backfill-id>
```

**GraphQL**: `partitionBackfillsOrError`, `partitionBackfillOrError`

### 15. **env-var**

```bash
dg api env-var list [--location <name>] [--json]
dg api env-var view <var-name> [--location <name>] [--json]
# Environment variables managed through deployment settings
```

**GraphQL**: `utilizedEnvVarsOrError`

---

## **Tier 4: Advanced/Monitoring**

### 16. **alert-notification**

```bash
dg api alert-notification list [--policy-id <id>] [--limit <n>] [--json]
dg api alert-notification view <notification-id> [--json]
# Notifications are read-only audit trail
```

**GraphQL**: `alertPolicyNotifications`

### 17. **audit-log**

```bash
dg api audit-log list [--user <user-id>] [--action <action>] [--limit <n>] [--json]
dg api audit-log view <log-id> [--json]
# Audit logs are read-only
```

**GraphQL**: `auditLog`

### 18. **custom-role**

```bash
dg api custom-role list [--json]
dg api custom-role view <role-id> [--json]
dg api custom-role create --name <name> --permissions <file>
dg api custom-role update <role-id> --permissions <file>
dg api custom-role delete <role-id>
```

**GraphQL**: `customRoles`, `customRoleOrError`

### 19. **api-token**

```bash
dg api api-token list [--type <user|agent>] [--json]
dg api api-token view <token-id> [--json]
dg api api-token create --description <desc> [--type <type>]
dg api api-token revoke <token-id>
```

**GraphQL**: `apiTokensOrError`, `agentTokensOrError`

### 20. **user-token**

```bash
dg api user-token list --user <user-id> [--json]
dg api user-token view <token-id> [--json]
dg api user-token create --user <user-id> --description <desc>
dg api user-token revoke <token-id>
```

**GraphQL**: `userTokensOrError`

---

## **Additional Requested Nouns**

### 21. **branch-deployment**

```bash
dg api branch-deployment list [--pr-status <open|merged>] [--json]
dg api branch-deployment view <deployment-name> [--json]
dg api branch-deployment create --branch <branch> --repo <repo>
dg api branch-deployment delete <deployment-name>
```

**GraphQL**: `branchDeployments`

### 22. **location-schema**

```bash
dg api location-schema list [--json]
dg api location-schema view [--json]
# Schema is typically read-only metadata
```

**GraphQL**: `locationSchema`

### 23. **deployment-setting**

```bash
dg api deployment-setting list [--json]
dg api deployment-setting view [--json]
dg api deployment-setting update --config <file>
# Settings are typically singular per deployment
```

**GraphQL**: `deploymentSettings`

---

## **Implementation Priority by Phase**

### **Phase 1** (Core Operations - Weeks 1-2)

1. ✅ deployment (done)
2. secret
3. agent
4. run

### **Phase 2** (Management - Weeks 3-4)

5. asset
6. user
7. code-location
8. alert-policy

### **Phase 3** (Extended - Weeks 5-6)

9. schedule
10. sensor
11. backfill
12. env-var
13. check

### **Phase 4** (Advanced - Weeks 7-8)

14. team
15. workspace
16. custom-role
17. api-token

### **Phase 5** (Specialized - Week 9)

18. branch-deployment
19. deployment-setting
20. location-schema
21. alert-notification
22. audit-log
23. user-token

---

## **File Organization Structure**

```
dagster_dg_cli/cli/plus/api/
├── __init__.py                   # Main API group
├── shared.py                     # Shared utilities
│
# Tier 1: Core Infrastructure
├── deployment.py                 # ✅ Already implemented
├── secret.py                     # Secrets management
├── agent.py                      # Agent monitoring
├── run.py                        # Pipeline runs
├── asset.py                      # Asset catalog
│
# Tier 2: Cloud Management
├── user.py                       # User management
├── team.py                       # Team management
├── alert_policy.py               # Alert configurations
├── code_location.py              # Code deployment locations
├── workspace.py                  # Workspace management
│
# Tier 3: Extended Management
├── check.py                      # Asset checks
├── schedule.py                   # Scheduled jobs
├── sensor.py                     # Event-driven triggers
├── backfill.py                   # Bulk operations
├── env_var.py                    # Environment variables
│
# Tier 4: Advanced/Monitoring
├── alert_notification.py         # Alert history
├── audit_log.py                  # Audit trail
├── custom_role.py                # Permission management
├── api_token.py                  # API authentication
├── user_token.py                 # User tokens
│
# Additional
├── branch_deployment.py          # PR deployments
├── location_schema.py            # Code location schemas
└── deployment_setting.py         # Configuration
```

---

## **Design Principles**

### **Consistency**

- All commands follow `dg api <noun> <verb>` pattern
- Standard verbs: `list`, `view`, `create`, `update`, `delete`
- `--json` flag available on all commands
- Consistent parameter naming across similar operations

### **Discoverability**

- Help text explains each command's purpose
- Commands grouped by logical tiers
- Clear examples in documentation
- Error messages guide users to correct usage

### **REST-like Interface**

- GraphQL complexity hidden behind simple REST-like operations
- Consistent data transformation from GraphQL to JSON
- Predictable response formats
- Standard HTTP-like status handling

### **GitHub CLI Inspiration**

- Follows `gh` command patterns and conventions
- Similar flag naming and behavior
- Consistent output formatting options
- Familiar user experience for developers

---

## **Implementation Status**

- ✅ **deployment list** - Completed
- 🚧 **Next**: secret, agent, run, asset (Phase 1)
- 📋 **Planned**: 22 additional nouns across 4 more phases

This plan provides a comprehensive roadmap for implementing a complete Dagster Plus API CLI following established patterns and best practices.
