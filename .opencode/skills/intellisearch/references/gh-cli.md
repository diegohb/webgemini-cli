# GitHub CLI Search

Using `gh` CLI for direct GitHub repository search.

<detection>
```bash
gh auth status
```
- Exit code 0: gh is available and authenticated
- Exit code non-zero: gh not available or not authenticated
</detection>

## Search Command

```bash
gh search repos [query] [flags]
```

## Query Strategy

<approach>
1. **Topics + Language** (preferred when topics identifiable)
2. **Keywords only** (fallback)
</approach>

<topic_detection>
Infer topics from user query context:
- Framework names → topics (react, vue, express)
- Library names → topics (lodash, axios, moment)
- Concepts → topics (semver, validation, authentication)
</topic_detection>

<language_inference>
Extract programming language from:
- Explicit mention: "in TypeScript", "Python library"
- File extensions: ".ts", ".py", ".go"
- Context: "npm package" → JavaScript/TypeScript
</language_inference>

## Examples

<examples>
<example category="topic_language">
```bash
# Query: "semver validation in TypeScript"
gh search repos --topic=semver,validation --language=typescript --json fullName,stargazersCount,createdAt,updatedAt,description --limit 10
```
</example>

<example category="keyword">
```bash
# Query: "cli shell terminal"
gh search repos cli shell terminal --json fullName,stargazersCount,createdAt,updatedAt,description --limit 10
```
</example>

<example category="combined">
```bash
# Topics with additional keywords
gh search repos "release automation" --topic=semver,versioning --language=typescript --json fullName,stargazersCount,createdAt,updatedAt,description --limit 10
```
</example>
</examples>

## Output Format

```bash
--json fullName,stargazersCount,createdAt,updatedAt,description --limit 10
```

<example_output>
```json
[
  {"createdAt":"2020-03-17T21:23:36Z","description":"SEMVER validation Github Action","fullName":"rubenesp87/semver-validation-action","stargazersCount":8,"updatedAt":"2024-03-29T19:31:00Z"},
  {"createdAt":"2024-10-07T16:18:55Z","description":"An example to prove semverValidate Helm function","fullName":"lucabaggi/helm-semver-validation","stargazersCount":0,"updatedAt":"2024-10-07T16:24:06Z"}
]
```
</example_output>

## Result Processing

<process>
1. Get top 10 results from gh
2. Sort by `stargazersCount` descending
3. Return top 5 for DeepWiki queries
</process>

## Common Flags

| Flag | Purpose | Example |
|------|---------|---------|
| `--topic` | Filter by topics | `--topic=react,hooks` |
| `--language` | Filter by language | `--language=typescript` |
| `--owner` | Filter by owner | `--owner=facebook` |
| `--stars` | Min stars | `--stars=">100"` |
| `--sort` | Sort field | `--sort=stars` |
| `--order` | Sort order | `--order=desc` |
| `--limit` | Max results | `--limit=10` |
| `--json` | Output format | `--json fullName,stargazersCount` |
| `--archived` | Exclude archived | `--archived=false` |

## JSON Available Fields
 - createdAt
 - defaultBranch
 - description
 - forksCount
 - fullName
 - hasDownloads
 - hasIssues
 - hasPages
 - hasProjects
 - hasWiki
 - homepage
 - id
 - isArchived
 - isDisabled
 - isFork
 - isPrivate
 - language
 - license
 - name
 - openIssuesCount
 - owner
 - pushedAt
 - size
 - stargazersCount
 - updatedAt
 - url
 - visibility
 - watchersCount

## Error Handling

```yaml
IF gh auth status fails:
  → Fall back to search_tool or fetch_tool
IF gh search repos fails:
  → Fall back to search_tool or fetch_tool
```

## Permission Opt-Out

Users can deny `gh` tool permission in OpenCode to opt out of this search method. The skill will automatically fall back to web search tools.
