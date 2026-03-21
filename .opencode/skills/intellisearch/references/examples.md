# Few-Shot Examples

Real-world patterns for IntelliSearch skill execution.

## Example 1: Library Discovery

**Query:** "Find a TypeScript library for semantic versioning validation"

<execution>
<step name="search" tool="gh search repos">
CMD: `gh search repos "semver validation typescript" --language=typescript --json fullName,stargazersCount,createdAt,updatedAt,description --limit 10`
RESULT: [npm/node-semver: 4.5K★, mattfarina/semver: 892★, ...]
</step>

<step name="filter" action="Top 3 by stars">
SELECTED: [npm/node-semver, mattfarina/semver, ieee802js/node-semver]
</step>

<step name="query" tool="DeepWiki_ask_question">
PAYLOAD: {
  repoName: ["npm/node-semver", "mattfarina/semver", "ieee802js/node-semver"],
  question: "Which is best for TypeScript semver validation?"
}
</step>

<step name="synthesize">
OUTPUT: npm/node-semver recommended (most stars, active maintenance, TypeScript typings included)
</step>
</execution>

---

## Example 2: Framework Comparison

**Query:** "Compare React state management libraries: Zustand vs Jotai vs Valtio"

<execution>
<step name="search" tool="gh search repos (parallel)">
CMDS:
- `gh search repos "zustand" --json fullName,stargazersCount,createdAt,updatedAt --limit 5`
- `gh search repos "jotai" --json fullName,stargazersCount,createdAt,updatedAt --limit 5`
- `gh search repos "valtio" --json fullName,stargazersCount,createdAt,updatedAt --limit 5`
RESULT: [pmndrs/zustand: 47K★, pmndrs/jotai: 18K★, pmndrs/valtio: 7K★]
</step>

<step name="filter" action="Exact matches only">
SELECTED: [pmndrs/zustand, pmndrs/jotai, pmndrs/valtio]
</step>

<step name="query" tool="DeepWiki_ask_question">
PAYLOAD: {
  repoName: ["pmndrs/zustand", "pmndrs/jotai", "pmndrs/valtio"],
  question: "Compare these React state management libraries: API design, performance, bundle size, learning curve"
}
</step>

<step name="synthesize">
OUTPUT: Zustand (simplest API, largest), Jotai (atomic, smallest), Valtio (proxy-based, mutable patterns)
</step>
</execution>

---

## Example 3: Fallback Chain

**Query:** "Is there a browser-based WebGL physics engine?"

<execution>
<step name="search" tool="gh search repos" status="failed">
CMD: `gh search repos "webgl physics engine browser" --language=javascript --limit 10`
ERROR: gh CLI not authenticated
</step>

<step name="fallback" tool="google_search">
PAYLOAD: {query: "webgl physics engine javascript npm github"}
RESULT: Snippets mentioning cannon-es, ammo.js, Oimo.js
</step>

<step name="extract" action="owner/repo patterns">
EXTRACTED: [pmndrs/cannon-es, kripken/ammo.js, lo-th/Oimo.js]
</step>

<step name="filter" action="Top 3 by relevance">
SELECTED: [pmndrs/cannon-es, kripken/ammo.js, lo-th/Oimo.js]
</step>

<step name="query" tool="DeepWiki_ask_question">
PAYLOAD: {
  repoName: ["pmndrs/cannon-es", "kripken/ammo.js", "lo-th/Oimo.js"],
  question: "Which is best for browser WebGL physics with Three.js integration?"
}
</step>

<step name="synthesize">
OUTPUT: cannon-es recommended (ES modules, maintained fork of cannon.js, Three.js examples available)
</step>
</execution>
