# DuckDuckGo Search Operators

Source: https://duckduckgo.com/duckduckgo-help-pages/results/syntax

## Basic Operators

| Operator | Syntax | Example | Purpose |
|----------|--------|---------|---------|
| Exact match | `"phrase"` | `"cats and dogs"` | Exact phrase match |
| Semantic similar | `~"phrase"` | `~"cats and dogs"` | Semantically similar results (experimental) |
| Include more | `term +term2` | `cats +dogs` | More emphasis on term |
| Exclude | `term -term2` | `cats -dogs` | Exclude term from results |

## File & Site Operators

| Operator | Syntax | Example | Purpose |
|----------|--------|---------|---------|
| File type | `filetype:type` | `cats filetype:pdf` | Specific file type |
| Site search | `site:domain.com` | `dogs site:example.com` | Search specific site |
| Exclude site | `-site:domain.com` | `cats -site:example.com` | Exclude specific site |

## Page Location Operators

| Operator | Syntax | Example | Purpose |
|----------|--------|---------|---------|
| In title | `intitle:term` | `intitle:dogs` | Term in page title |
| In URL | `inurl:term` | `inurl:cats` | Term in page URL |

## Navigation Operators

| Operator | Syntax | Example | Purpose |
|----------|--------|---------|---------|
| Go to first | `\term` | `\futurama` | Navigate to first result |
| Bang shortcut | `!site term` | `!a blink182` | Search on other site directly |
| Safe search on | `!safeon` | `term !safeon` | Enable safe search |
| Safe search off | `!safeoff` | `term !safeoff` | Disable safe search |

## Supported File Types

<file_types>
- `pdf` - PDF documents
- `doc` / `docx` - Word documents
- `xls` / `xlsx` - Excel spreadsheets
- `ppt` / `pptx` - PowerPoint presentations
- `html` - HTML files
</file_types>

## Usage Notes

<important>
- If no results found with advanced syntax, related results may be shown
- Bang shortcuts search other sites' search engines (subject to that site's policies)
- Thousands of bang shortcuts available (see: https://duckduckgo.com/bang)
- Note: Some advanced syntax may not work correctly on all queries
</important>

## Common Patterns for Technical Search

<patterns>
```bash
# Find libraries
typescript validation library

# Exact phrase
"semantic versioning" npm package

# File type filter
"readme" filetype:md tutorial

# Title search
intitle:react hooks typescript

# Combined
semver validation -test intitle:library

# Package search
nodejs graph database library
```
</patterns>
