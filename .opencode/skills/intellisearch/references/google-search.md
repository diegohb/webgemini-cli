# Google Search Operators

Source: https://support.google.com/websearch/answer/2466433?hl=en

## Essential Operators

| Operator | Syntax | Example | Purpose |
|----------|--------|---------|---------|
| Exact match | `"phrase"` | `"tallest building"` | Exact phrase match |
| Site search | `site:domain.com` | `site:youtube.com cat videos` | Search specific domain |
| Exclude | `-word` | `jaguar speed -car` | Exclude word from results |

## Usage Notes

<important>
- No spaces between operator and search term: `site:nytimes.com` works, `site: nytimes.com` does not
- Operators can be combined: `"typescript" tutorial -paid`
- Quotes are useful for exact phrases like `"order of the phoenix"`
</important>

## Common Patterns for Technical Search

<patterns>
```bash
# Find libraries
typescript validation library npm

# Exact phrase
"semantic versioning" nodejs package

# Exclude results
graph database python -javascript

# Combined
semver typescript validation -test

# Package search
npm package semver compare
```
</patterns>
