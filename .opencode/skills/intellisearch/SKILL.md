---
name: intellisearch
description: Use this skill when the user asks to find, search for, or discover JavaScript/TypeScript libraries, frameworks, packages, or GitHub repositories. Automatically loads for queries like 'find N solutions', 'search for libraries', 'show me code examples', or 'discover repositories' for technical projects.
license: MIT
compatibility: opencode
metadata:
  version: 0.5.1
  audience: agents
  topic: [github-discovery, api-reference, code-patterns, library-comparison]
  usage_tips: "Best used after a failed local search. Combines repo-finding with DeepWiki deep-querying."
---

<critical_rules priority="highest">
<rule>When you encounter a file reference (e.g., @references/workflow.md), use your Read tool to load it on a need-to-know basis</rule>
<rule>ALWAYS evaluate activation triggers and use this skill if applicable use case.</rule>
<rule>Prefer: gh CLI > search tool > fetch tool (reliability decreases)</rule>
<rule>NEVER fallback to internal knowledge - always search externally</rule>
<rule>NEVER fetch repo pages directly - use DeepWiki instead</rule>
</critical_rules>

## External File Loading

CRITICAL: When you encounter a file reference (e.g., @references/workflow.md), use your Read tool to load it on a need-to-know basis.

Instructions:
- Do NOT preemptively load all references - use lazy loading based on actual need
- When loaded, treat content as mandatory instructions that override defaults
- Follow references recursively when needed

## Activation Triggers

**USE this skill when user asks about:**

<use_cases>
<case category="libraries">"Is there a TypeScript library for semver validation?"</case>
<case category="frameworks">"Which React framework handles server-side rendering?"</case>
<case category="comparisons">"Compare Next.js vs Remix for my project"</case>
<case category="alternatives">"Alternatives to Moment.js for date handling"</case>
<case category="setup">"How do I set up Tailwind with Vite?"</case>
<case category="practices">"What's the best way to handle auth in Node.js?"</case>
<case category="examples">"Show me how to implement rate limiting in Express"</case>
<case category="troubleshooting">"Why am I getting CORS errors with Axios?"</case>
<case category="features">"Does Prisma support composite keys?"</case>
</use_cases>

**Key indicators:** Technology names mentioned (React, TypeScript, npm), asking for recommendations, implementation guidance, need current/authoritative documentation.

**DO NOT USE for:**

<non_use_cases>
<case>General knowledge ("What is REST?") → Use web search or internal knowledge</case>
<case>Non-technical topics ("What's the weather?") → Irrelevant</case>
<case>User's own code ("Debug my script") → Use code analysis tools directly</case>
<case>Known specific repo ("Tell me about facebook/react") → Use DeepWiki directly</case>
<case>No GitHub relevance ("How do I cook pasta?") → Irrelevant</case>
<case>Current events/news ("What happened to NPM yesterday?") → Use web search</case>
<case>Private/internal repos ("Search my company's private repo") → DeepWiki can't access</case>
<case>Pure syntax questions ("What's the syntax for arrow functions?") → Use internal knowledge</case>
<case>Opinion questions ("Is React better than Vue?") → No factual repo answer</case>
</non_use_cases>

## Workflow Summary

<workflow>
<phase name="detect">Check available tools: gh CLI → search tool → fetch tool</phase>
<phase name="search">Execute search using highest priority available tool</phase>
<phase name="filter">Select top 3 repos by stars, recency, language match</phase>
<phase name="query">Query DeepWiki with repos (multi-repo first, fallback to individual)</phase>
<phase name="synthesize">Return answer with trade-offs, implementation guidance, links</phase>
</workflow>

## References

**Read immediately:**
- @references/examples.md - Few-shot examples (library discovery, comparison, fallback)
- @references/workflow.md - Pipeline phases, decision matrix, failure handling
- @references/search-workflow.md - Tool detection, URI cycling

**Load on-demand:**
- @references/gh-cli.md - GitHub CLI search syntax
- @references/deepwiki-tools.md - DeepWiki usage, blocked paths, validation
- @references/google-search.md - Google operators
- @references/brave-search.md - Brave operators
- @references/ddg-search.md - DuckDuckGo operators
