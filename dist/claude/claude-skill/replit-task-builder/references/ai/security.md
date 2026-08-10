# Security Instruction Object

Read for authentication, authorization, sensitive data, uploads, logging, mutations, integrations, or security review.

## Responsibility

Own security guidance for identity, authorization, object/tenant scope, sensitive data handling, input validation, uploads, logging, mutations, integrations, leakage prevention, and security review findings.

## Activation

Use this object when the selected workflow touches authentication, authorization, sensitive data, uploads, external input, logging, mutations, integrations, security review, or any public contract with leakage risk.

## Inputs

- Actor, identity source, permissions, resource/object scope, tenant scope, sensitive fields, and allowed transitions.
- Approved write/read paths, current auth/logging/validation patterns, and explicit security requirements.
- Requested review dimensions, reproduction evidence, and accepted risk decisions when auditing.

## Must Not

- Treat UI visibility as enforcement, weaken validation/audit/isolation, add bypasses, expose secrets, or rely on client-supplied authority.
- Use unknown services, new credentials, unsafe execution, untrusted paths/SQL/commands, or protected/config changes without explicit authority.
- Report unsupported security conclusions without evidence and confidence.

## Rules

- Default deny when identity, permission, tenant/object scope, ownership, or transition is missing.
- Derive identity/roles server-side; UI visibility and route guards are usability only.
- Validate all external input and allowlist writable/sortable fields, paths, and transitions.
- Return only fields required for the caller; do not reveal unauthorized record existence through errors, counts, or fallbacks.
- Never expose/log passwords, hashes, tokens, cookies, authorization headers, connection strings, secrets, recovery values, stacks, SQL, or unnecessary personal/financial data.
- Do not construct SQL, commands, code, or paths from untrusted input; do not render unsafe HTML.
- Use existing authentication, sanitization, redacted logging, audit, and integration patterns; add no bypass, credential, dependency, or unknown service.

Uploads require existing approved storage, size/type/extension/metadata validation, generated safe names, traversal prevention, no execution, and object-scope checks for upload/download.

Sensitive mutations require current-state validation, action and object permission, field restrictions, allowed transition, duplicate/replay handling when relevant, and preserved auditability.

## Workflow

1. Identify identity source, permission boundary, tenant/object ownership, sensitive fields, and transition rules.
2. Enforce default deny and server-side authority at route, service, data, and response boundaries.
3. Validate/allowlist all external inputs and outputs; redact logs and errors.
4. Verify allowed, denied, malformed, stale, cross-scope, sensitive-field, upload, and leakage cases as applicable.
5. For audits, separate confirmed findings, risks, evidence gaps, and accepted risk.

## Output Evidence

For findings report severity (`Critical`, `High`, `Medium`, `Low`), approved-path evidence, impact, reproduction conditions, and safe recommendation. Stop for requested bypasses, secret/config changes, protected/unknown services, unsafe execution, or weakened validation/audit/isolation.
