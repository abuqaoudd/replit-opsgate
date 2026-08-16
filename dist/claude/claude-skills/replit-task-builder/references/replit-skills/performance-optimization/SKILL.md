---
name: performance-optimization
description: Measure and improve a bounded frontend or Replit-backend performance problem such as slow rendering, repeated requests, large lists, N+1 queries, excessive payloads, or slow endpoints. Use only with a reproducible metric and behavior-preserving target; do not perform speculative optimization.
---

# Performance Optimization

Automatically select internal mode `PERFORMANCE_OPTIMIZATION`. This selects procedure, not authority.

1. Read `../../../replit.md`, the active profile's business file under `../../../ai/` (e.g. `metco.md` for the `metco` profile), if it has one, `../../../ai/{testing}.md`, and relevant frontend/backend/database references.
2. Remain read-only for measurement or implement a bounded fix only when explicitly requested. Define scenario, data scale, baseline metric, target, and correctness constraints.
3. Trace the request/render/query path and measure before editing using approved tools and safe data.
4. Rank proven bottlenecks; select the smallest owner-level change. Reuse caching/query/list patterns and preserve contracts, authorization, ordering, and freshness.
5. Do not add dependencies/config, weaken validation, fetch unbounded data, or trade correctness/security for speed.
6. Measure with the same method and scale; verify functional, permission, error, and stale/refresh behavior.
7. Report baseline, change, after metric, variance/limitations, regressions, and remaining bottlenecks.

Stop when measurement requires production/protected access, unknown services, schema/index changes without migration authorization, or an unclear performance target.
