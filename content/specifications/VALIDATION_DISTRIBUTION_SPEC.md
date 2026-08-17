# Validation Specification

Specification version: 7

## Behavioral forward tests

At minimum, test:

1. a business request routes to the business template;
2. an implementation-ready request routes to the specification template;
3. an ordinary frontend task selects the frontend skill without user labels;
4. a complex cross-surface change produces a phase plan and only one executable phase;
5. explicit migration work selects the migration skill but still checks authorization;
6. a fully specified task does not trigger HITL;
7. each HITL case emits one decision request;
8. invalid `DECIDE` input remains paused;
9. valid `DECIDE` input resumes the exact blocked step.
