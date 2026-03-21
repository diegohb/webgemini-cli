# Search Pipeline & Decision Points

Detailed workflow for repository discovery and analysis.

<critical_rules priority="highest">
<rule>NEVER fetch github.com URLs - use DeepWiki instead</rule>
<rule>Limit to 5-10 repository candidates before filtering</rule>
<rule>Select only TOP 3 repos for DeepWiki queries</rule>
<rule>Max 3 repos per DeepWiki call</rule>
</critical_rules>

## Pipeline Phases

```yaml
phases:
  - name: TOOL_DETECTION
    priority: [gh_cli, search_tool, fetch_tool]
    constraint: NEVER fetch github.com URLs

  - name: REPOSITORY_DISCOVERY
    actions: [execute_search, extract_owner_repo, validate_format]
    constraint: limit 5-10 candidates

  - name: CANDIDATE_FILTERING
    sort: [stars_DESC, recency, language_match]
    constraint: SELECT_TOP_3

  - name: DEEPWIKI_QUERY
    strategy: [multi_repo_first, fallback_individual]
    constraint: max 3 repos per call

  - name: ANSWER_SYNTHESIS
    format: [overview, trade_offs, implementation, links]
    constraint: include_comparison_recommendations
```

## Decision Matrix

| Condition | Action |
|-----------|--------|
| `gh` CLI available | Use `gh search repos` with JSON output |
| No `gh`, search tool exists | Query external search engine |
| No search tool | Fetch external search engine URL |
| Multi-repo DeepWiki fails | Query repos individually |
| All DeepWiki queries fail | Report repos found but not indexed |

## Tool Selection Strategy

<priority_order>
1. gh CLI (Preferred) - Direct API access, structured JSON, topic/language filtering
2. Search Tool (Fallback #1) - Query external engines, NO `site:github.com` operator
3. Fetch Tool (Fallback #2) - URI-based search with engine cycling
</priority_order>

See @search-workflow.md for detailed tool usage.

## Repository Extraction

<validation_rules>
<pattern type="standard">`github\.com/([\w-]+)/([\w.-]+)` → Example: `github.com/npm/node-semver`</pattern>
<pattern type="pages">`([\w-]+)\.github\.io/([\w.-]+)` → Example: `npm.github.io/semver`</pattern>
<constraint>Owner: alphanumeric, `-`, `_` only</constraint>
<constraint>Repo: alphanumeric, `-`, `_`, `.` only</constraint>
<constraint>Owner NOT in blocked list (see @deepwiki-tools.md)</constraint>
</validation_rules>

## Candidate Filtering

Select **top 3 repositories** before DeepWiki query.

<prioritization>
1. Stars - Higher count = community validation
2. Recency - Recent commits = active maintenance
3. Language match - Prefer repos matching query language
</prioritization>

**Do not query DeepWiki for repos you won't recommend.**

## DeepWiki Query Strategy

<query_format>
<multi_repo>Try first: `repoName=["owner1/repo1", "owner2/repo2"]` (2+ items)</multi_repo>
<single_repo>Fallback: `repoName="owner/repo"` (string)</single_repo>
<forbidden>Never: `repoName=["owner/repo"]` (single-item array fails)</forbidden>
</query_format>

<efficiency_rules>
- Query max 3 repos per request
- If multi-repo fails, query top candidate only (not all individually)
</efficiency_rules>

See @deepwiki-tools.md for detailed usage.

## Answer Synthesis

<output_format>
1. Best options with trade-offs
2. Specific implementation guidance
3. Code examples if available
4. Repository links
</output_format>

**Efficiency:** If you found more than 3 repos, prioritize by: stars > recency > language match. Only include details for your top 3 candidates.

## Failure Handling

| Failure | Action |
|---------|--------|
| gh CLI not available | Fall back to search tool |
| Search tool not available | Fall back to fetch tool + URI cycling |
| URI search fails (captcha/redirect) | Try next engine in cycle |
| All URI searches fail | Report: "Unable to search - no working search method" |
| DeepWiki multi-repo fails | Query repos individually |
| DeepWiki single repo fails | Try next repo in list |
| All DeepWiki queries fail | Report: "Repos found but not indexed by DeepWiki" |
