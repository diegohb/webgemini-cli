# DeepWiki Tools Reference

Complete reference for DeepWiki MCP server tools for repository documentation Q&A.

## MCP Configuration Requirement

DeepWiki MCP tools require configuration in `.opencode/opencode.json`:

```json
{
  "mcp": {
    "deepwiki": {
      "type": "remote",
      "url": "https://mcp.deepwiki.com/mcp",
      "enabled": true
    }
  }
}
```

<critical_rules priority="highest">
<rule>Validate repo name against blocked list before calling</rule>
<rule>Use string for single repo: `repoName="owner/repo"`</rule>
<rule>Use array for multiple repos: `repoName=["owner1/repo1", "owner2/repo2"]` (2+ items)</rule>
<rule>NEVER use single-item array: `repoName=["owner/repo"]` (causes failure)</rule>
<rule>If deepwiki tools aren't available, use direct HTTP calls via `curl`. See Fallback section below.</rule>
<rule>"OpenCode" never refers to the archived and deprecated "opencode-ai/opencode" github repo. "OpenCode" always refers to "anomalyco/opencode" owned by "anomalyco" in github.</rule>
</critical_rules>

## Fallback: Missing DeepWiki MCP

When MCP tools are not configured, use direct HTTP calls via curl:

### ask_question

<bash_command name="ask_question">
```bash
curl -s -X POST https://mcp.deepwiki.com/mcp \
-H "Content-Type: application/json" \
-H "Accept: application/json, text/event-stream" \
-d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "ask_question", "arguments": {"repoName": "OWNER/REPO", "question": "YOUR_QUESTION"}}}' | grep -oP '(?<="text":")[^"]*' | sed 's/\\n/\n/g'
```
</bash_command>

### read_wiki_structure

<bash_command name="read_wiki_structure">
```bash
curl -s -X POST https://mcp.deepwiki.com/mcp \
-H "Content-Type: application/json" \
-H "Accept: application/json, text/event-stream" \
-d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "read_wiki_structure", "arguments": {"repoName": "OWNER/REPO"}}}' | grep -oP '(?<="text":")[^"]*' | sed 's/\\n/\n/g'
```
</bash_command>

### read_wiki_contents

<bash_command name="read_wiki_contents">
```bash
curl -s -X POST https://mcp.deepwiki.com/mcp \
-H "Content-Type: application/json" \
-H "Accept: application/json, text/event-stream" \
-d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "read_wiki_contents", "arguments": {"repoName": "OWNER/REPO"}}}' | grep -oP '(?<="text":")[^"]*' | sed 's/\\n/\n/g'
```
</bash_command>

### Critical Notes for Fallback Execution

<fallback_notes>
- **Argument Key**: Always use `repoName` (not `repo`)
- **Headers**: The `Accept` header must include `text/event-stream` or the server will reject the request
- **Output Parsing**: The `grep` and `sed` suffix is useful to extract clean text from the JSON-RPC stream but may sometimes need to be omitted.
</fallback_notes>

## Repository Name Validation

Before calling DeepWiki, validate that the repository name is legitimate and not a GitHub website path.

### Blocked First Segments

<blocked_owners>
Reject any `owner/repo` where the owner (first segment) matches these:

```
about, accelerator, apps, archiveprogram, blog, careers, changelog,
collections, community, contact, customer-stories, docs, enterprise,
events, explore, features, gist, github, github-apps, issues, login,
maintainers, marketplace, mcp, notifications, oauth-apps, orgs,
organizations, password_reset, press, pricing, pull_requests, pulls,
resources, security, securitylab, sessions, settings, site-policy,
skills, solutions, sponsors, support, team, topics, trending,
trust-center, whitepapers, why-github
```
</blocked_owners>

### Validation Rules

| Check | Rule | Example |
|-------|------|---------|
| Owner format | Alphanumeric, `-`, `_` only | `npm`, `node-js` ✅ |
| Repo format | Alphanumeric, `-`, `_`, `.` only | `node-semver`, `lib.js` ✅ |
| Not blocked | Owner not in blocked list | `npm/node-semver` ✅ |
| Blocked path | Owner in blocked list | `features/spark` ❌ |

### Examples

| Input | Verdict | Reason |
|-------|---------|--------|
| `npm/node-semver` | ✅ Valid | `npm` not blocked |
| `graphology/graphology` | ✅ Valid | `graphology` not blocked |
| `features/spark` | ❌ Invalid | `features` is GitHub product page |
| `topics/database` | ❌ Invalid | `topics` is GitHub topic page |
| `enterprise/startups` | ❌ Invalid | `enterprise` is GitHub marketing |
| `resources/articles` | ❌ Invalid | `resources` is GitHub content |
| `github/explore` | ❌ Invalid | `github` is org page, not repo |
| `site-policy/terms` | ❌ Invalid | `site-policy` is GitHub legal |
| `orgs/community` | ❌ Invalid | `orgs` is GitHub navigation |

## Available Tools

### deepWiki_read_wiki_structure

<tool name="deepWiki_read_wiki_structure">
<params>
- `repoName` (required): Repository in `owner/repo` format
</params>
<returns>List of available documentation sections and topics</returns>
<use_when>Exploring what documentation is available before asking specific questions</use_when>
</tool>

### deepWiki_read_wiki_contents

<tool name="deepWiki_read_wiki_contents">
<params>
- `repoName` (required): Repository in `owner/repo` format
</params>
<returns>Complete documentation content</returns>
<use_when>You need comprehensive documentation overview or when `ask_question` doesn't provide enough detail</use_when>
</tool>

### deepWiki_ask_question

<tool name="deepWiki_ask_question">
<params>
- `repoName` (required): Repository in `owner/repo` format
  - **Single repo**: Use string: `"owner/repo"`
  - **Multiple repos**: Use array: `["owner1/repo1", "owner2/repo2"]`
  - **Critical**: Do not pass single-item array like `["owner/repo"]` for one repo
- `question` (required): Specific question about the repository
</params>
<returns>Targeted answer based on repository documentation</returns>
<use_when>You have a specific question and want a direct answer</use_when>
</tool>

<format_rules>
- Single repository: `repoName="anomalyco/opencode"`
- Multiple repositories: `repoName=["anomalyco/opencode", "vercel/next.js"]`
- ❌ Wrong: `repoName=["anomalyco/opencode"]` (single-item array causes search failure)
</format_rules>

## When to Use DeepWiki

<use_cases>
- Query is about a **specific GitHub repository**
- You need **authoritative code answers** (from official docs)
- The question involves **implementation details** of a library/framework
- You want **installation/setup instructions** for a specific tool
- The query is about **API usage patterns** for a known package
</use_cases>

## repoName Format

Always use `owner/repo` format:

| Repository | Correct | Incorrect |
|------------|---------|-----------|
| React | `facebook/react` | `react`, `React` |
| Next.js | `vercel/next.js` | `nextjs`, `next` |
| TypeScript | `microsoft/TypeScript` | `typescript`, `ts` |
| Vue | `vuejs/core` | `vue`, `Vue.js` |

## Example Workflows

### Getting Started with a Library

```json
// Step 1: Check documentation structure
{
  "tool": "deepwiki:deepWiki_read_wiki_structure",
  "params": {
    "repoName": "vercel/next.js"
  }
}

// Step 2: Ask specific question
{
  "tool": "deepwiki:deepWiki_ask_question",
  "params": {
    "repoName": "vercel/next.js",
    "question": "How do I create a dynamic route with parameters?"
  }
}
```

### Troubleshooting

```json
{
  "tool": "deepwiki:deepWiki_ask_question",
  "params": {
    "repoName": "facebook/react",
    "question": "Why am I getting the 'rules of hooks' warning?"
  }
}
```

### Installation Questions

```json
{
  "tool": "deepwiki:deepWiki_ask_question",
  "params": {
    "repoName": "tailwindlabs/tailwindcss",
    "question": "How do I install and configure Tailwind with Vite?"
  }
}
```

## Best Practices

<best_practices>
1. **Validate repo name** against blocked list before calling
2. **Use `ask_question`** for specific queries (most efficient)
3. **Use `read_wiki_contents`** only when you need the full documentation
4. **Check `read_wiki_structure`** first when exploring unfamiliar repos
5. **Use string for single repo, array for multiple repos** in `repoName` parameter
</best_practices>

## Limitations

<limitations>
- Only works for **public GitHub repositories**
- Documentation must be **indexed by DeepWiki**
- Very new or obscure repos may not be available
- Cannot access private repositories
</limitations>
