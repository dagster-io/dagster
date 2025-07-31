#!/bin/bash

# diagnose_bk_failure - Claude Code command to diagnose Buildkite failures
# This script is executed by Claude Code when the user runs /diagnose_bk_failure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Diagnosing Buildkite failures for current PR...${NC}"

# Validation checks
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ Error: GitHub CLI (gh) is not installed${NC}"
    echo -e "Please install from: https://cli.github.com/"
    exit 1
fi

# Get PR information and status checks
echo -e "${BLUE}📋 Getting PR status checks...${NC}"
PR_DATA=$(gh pr view --json number,headRefName,statusCheckRollup 2>/dev/null || echo "ERROR")

if [ "$PR_DATA" = "ERROR" ]; then
    echo -e "${RED}❌ Error: Could not get PR information${NC}"
    echo -e "Make sure you're in a repository with an open PR"
    exit 1
fi

# Parse failing Buildkite builds
FAILING_BUILDS=$(echo "$PR_DATA" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    pr_number = data.get('number')
    branch = data.get('headRefName')
    
    print(f'PR #{pr_number} ({branch})')
    print('---')
    
    failing_builds = []
    for check in data.get('statusCheckRollup', []):
        context = check.get('context', '')
        state = check.get('state', '')
        target_url = check.get('targetUrl', '')
        
        if context.startswith('buildkite/') and state == 'FAILURE':
            pipeline = context.replace('buildkite/', '')
            build_number = ''
            if '/builds/' in target_url:
                build_number = target_url.split('/builds/')[-1]
            
            failing_builds.append({
                'pipeline': pipeline,
                'build_number': build_number,
                'url': target_url
            })
    
    if failing_builds:
        print('FAILING_BUILDS_START')
        for build in failing_builds:
            print(f'{build[\"pipeline\"]}:{build[\"build_number\"]}:{build[\"url\"]}')
        print('FAILING_BUILDS_END')
    else:
        print('NO_FAILURES')
        
except Exception as e:
    print(f'PARSE_ERROR:{str(e)}')
")

# Check results
if echo "$FAILING_BUILDS" | grep -q "NO_FAILURES"; then
    echo -e "${GREEN}✅ No failing Buildkite builds found for this PR${NC}"
    exit 0
fi

if echo "$FAILING_BUILDS" | grep -q "PARSE_ERROR"; then
    ERROR_MSG=$(echo "$FAILING_BUILDS" | grep "PARSE_ERROR" | cut -d: -f2-)
    echo -e "${RED}❌ Error parsing PR data: $ERROR_MSG${NC}"
    exit 1
fi

# Extract build information
echo -e "${YELLOW}⚠️  Found failing Buildkite builds:${NC}"
echo "$FAILING_BUILDS" | sed -n '/FAILING_BUILDS_START/,/FAILING_BUILDS_END/p' | grep -v "FAILING_BUILDS_" | while IFS=':' read -r pipeline build_number url; do
    echo -e "   • ${pipeline} #${build_number}"
done

echo
echo -e "${BLUE}🔗 Build URLs:${NC}"
echo "$FAILING_BUILDS" | sed -n '/FAILING_BUILDS_START/,/FAILING_BUILDS_END/p' | grep -v "FAILING_BUILDS_" | while IFS=':' read -r pipeline build_number url; do
    echo -e "   • ${GREEN}${url}${NC}"
done

echo
echo -e "${YELLOW}⚠️  Buildkite MCP Server Required${NC}"
echo -e "${BLUE}This command requires the Buildkite MCP server to fetch detailed logs.${NC}"
echo -e "If not installed, get it from: ${GREEN}https://github.com/buildkite/buildkite-mcp-server${NC}"

echo
echo -e "${BLUE}📊 Summary:${NC}"
BUILD_COUNT=$(echo "$FAILING_BUILDS" | sed -n '/FAILING_BUILDS_START/,/FAILING_BUILDS_END/p' | grep -v "FAILING_BUILDS_" | wc -l | tr -d ' ')
echo -e "   • ${BUILD_COUNT} failing build(s) found"
echo -e "   • Ready for detailed analysis with MCP server"

# Output structured data for Claude Code to process
echo
echo -e "${BLUE}📋 Structured Data for Analysis:${NC}"
echo "CLAUDE_ANALYSIS_DATA_START"
echo "$FAILING_BUILDS" | sed -n '/FAILING_BUILDS_START/,/FAILING_BUILDS_END/p' | grep -v "FAILING_BUILDS_"
echo "CLAUDE_ANALYSIS_DATA_END"