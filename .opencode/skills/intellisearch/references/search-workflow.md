# Search Workflow

Tool detection and search strategy for finding GitHub repositories.

<critical_rules priority="highest">
<rule>NEVER use `site:github.com` with search tools - returns full URLs that get misparsed</rule>
<rule>Only fetch EXTERNAL search engines, NEVER github.com URLs</rule>
<rule>Cycle through engines on failure: Brave → DuckDuckGo → Google</rule>
</critical_rules>

## Tool Priority

```yaml
detection:
  IF gh auth status succeeds:
    → Use gh search repos (PREFERRED - direct API)
  ELSE IF search_tool exists:
    → Use search tool with keywords (NOT site:github.com)
  ELSE IF fetch_tool exists:
    → Use URI-based search with engine cycling
  ELSE:
    → Report: "No search capability available"
    → fallback to internal knowledge
```

## GitHub CLI (Preferred)

<detection>
```bash
gh auth status  # Exit 0 = available
```
</detection>

<search_patterns priority="try_in_order">
```bash
# 1. Full query with topics and language
gh search repos "{query}" --topic={topics} --language={lang} --json fullName,stargazersCount,createdAt,updatedAt,description --limit 10

# 2. Query with language only
gh search repos "{query}" --language={lang} --json fullName,stargazersCount,createdAt,updatedAt,description --limit 10

# 3. Topic-based search (no query string)
gh search repos --topic={topics} --language={lang} --json fullName,stargazersCount,createdAt,updatedAt,description --limit 10

# 4. Broader keyword search
gh search repos "{query}" --json fullName,stargazersCount,createdAt,updatedAt,description --limit 10
```
</search_patterns>

<process>
1. Infer topics from query (framework/library names → topics)
2. Infer language if mentioned
3. Sort by stargazersCount, return top 5
4. Skip to DeepWiki query
</process>

See @gh-cli.md for detailed syntax.

## Search Tool (Fallback #1)

<constraint>DO NOT use `site:github.com` - it returns full GitHub URLs that get misparsed as repos.</constraint>

<query_format>
```json
{ "query": "{technology} {feature} {language} library package" }
```
</query_format>

<example>
```json
{ "query": "typescript semver validation library npm package" }
```
</example>

<result_processing>
- Look for package names in snippets
- Find `github.com/owner/repo` references in descriptions
- Ignore navigation/ads
</result_processing>

## URI-Based Search (Fallback #2)

When only fetch tools available, cycle through engines:

| Priority | Engine | URL |
|----------|--------|-----|
| 1 | Brave | `https://search.brave.com/search?q={terms}` |
| 2 | DuckDuckGo | `https://duckduckgo.com/?q={terms}` |
| 3 | Google | `https://www.google.com/search?q={terms}` |

<error_handling>
```yaml
FOR each engine IN [brave, duckduckgo, google]:
  result = fetch(engine_url)
  IF success AND has_search_results:
    RETURN result
  CONTINUE
RETURN error: all engines failed
```
</error_handling>

<failure_causes>
- JavaScript redirects (Google)
- Captchas (DuckDuckGo)
- HTML parsing issues
</failure_causes>

<example>
```json
{
  "url": "https://search.brave.com/search?q=typescript%20semver%20validation%20library",
  "format": "markdown",
  "timeout": 10
}
```
</example>

## Query Construction

<keyword_based>
```
{technology} {feature} {language} library package
```
</keyword_based>

<examples>
- `react hooks typescript library`
- `semver validation nodejs package`
- `graph database python library`
</examples>

<result_extraction>
- Look for `github.com/owner/repo` in snippet descriptions
- Find package names that map to known repos
- Follow links in documentation references
</result_extraction>

## References

- @gh-cli.md - GitHub CLI syntax
- @google-search.md - Google operators
- @brave-search.md - Brave operators
- @ddg-search.md - DuckDuckGo operators
