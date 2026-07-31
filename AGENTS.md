# Workspace Routing

## SOS Contador First

This workspace contains a local skill at:

- `./sos-contador-api/SKILL.md`

For any request involving SOS Contador operations, open and use that skill first before considering any other approach.

If the prompt names a contribuyente informally, such as `empresa demo`, resolve it through the local SOS skill before running the business query. Do not guess the target CUIT from memory.

Examples that must route to the local SOS skill first:

- "Conectate a mi cuenta de SOS Contador"
- "Dame el listado de recibos"
- "Dame el detalle del recibo 51"
- "Listá cobranzas"
- "Traé ventas, pagos, clientes o productos de SOS Contador"

## Browser Rule

Do not use Playwright, browser-profile inspection, cookie reuse, or browser-session takeover for standard SOS Contador data tasks.

Use Playwright only when:

- the user explicitly asks to debug the SOS web UI itself, or
- the local SOS skill explicitly indicates that both the public API and the direct HTTP `web-session` fallback are insufficient for the requested task.

## Local Credentials

Assume the standard private credential source is:

- `<SOS_CONTADOR_HOME>/.env.local`, defaulting to `~/.sos-contador/.env.local`

If that file is present, do not ask for credentials again.
If credentials or a default CUIT are missing, ask one short follow-up and stop there.

## Public Skill Hygiene

This skill is intended to be developed locally, tested with real SOS Contador accounts, and later shared publicly so other SOS Contador users can connect their own agents to the API.

Public skill files must stay generic and portable:

- Do not add real user, client, provider, person, company, CUIT, email, address, account ID, invoice ID, receipt ID, browser path, or machine-specific path to `SKILL.md`, `scripts/`, `references/`, `agents/`, examples, schemas, tests, or any other file intended to ship with the skill.
- Use placeholders in documentation, such as `<cuit_trabajo>`, `<cliente_nombre>`, `<id_venta>`, `<usuario@example.com>`, or clearly fake demo names such as `Empresa Demo S.R.L.`.
- Tests may use deterministic fake values only. Do not copy real API payloads, real PDFs, real export rows, or real customer names into committed fixtures.
- Store local captures, real exports, draft caches, profiles, PDFs, screenshots, and troubleshooting notes that mention real entities only under `<SOS_CONTADOR_HOME>/local/`, outside this repository.
- If a real case teaches a new rule, copy only the generalized rule into public docs and move the concrete evidence to the private runtime home.

## Manual Terminal API Mode

When the user says they want to access SOS Contador manually from the terminal, without local scripts, or based only on the Postman API documentation, switch to manual terminal guidance.

Rules for that mode:

- Do not use `scripts/sos_contador_api.py` or any local helper command.
- Do not auto-load `.env.local`; the user will type credentials, CUIT, and IDs manually.
- Guide the user one terminal command at a time and wait for confirmation before continuing.
- Prefer PowerShell `Invoke-RestMethod` for JSON API requests.
- Keep a running record of correct methods, failed methods, and useful API findings in `./sos-contador-api/references/manual-terminal-api.md`.
- Use the public API flow from the Postman documentation first: `POST /login`, then `GET /cuit/credentials/:idcuit`, then the relevant business endpoint.

## Local Export Storage

For durable SOS Contador downloads and exports, do not leave files in temp folders, the repository root, or ad-hoc locations.

Store them under:

- `<SOS_CONTADOR_HOME>/local/exports/<cuit_trabajo>/<artifact_kind>/<YYYY>/<MM>/`

Rules:

- Use the `CUIT de trabajo` as the primary folder key.
- Use stable artifact folders such as `plan_de_cuentas`, `ventas`, `cobranzas`, `clientes`, `productos`, or `compras`.
- Prefix filenames with the export date in ISO format, for example `2026-04-10-plan-de-cuentas-<cuit_trabajo>.json`.
- When useful, save the raw export plus a normalized companion file such as `.csv`, `.md`, or `.meta.json`.
- Keep these exports under the private runtime home so they cannot be committed from this repository.

## Output Format

For SOS Contador responses that show a set of records, prefer a Markdown table by default.

Examples:

- receipt lists
- cobranza lists
- ventas lists
- client or product search results

Use prose instead of a table only when:

- the response is a single detailed record, or
- the dataset is too wide for a readable table

For normal user-facing SOS Contador queries, do not add technical commentary about whether the result came from `api` or `web-session`.

Mention transport details only when:

- the user explicitly asks how the data was obtained,
- the task is debugging or improving the skill itself, or
- the transport choice materially affects the meaning, completeness, or reliability of the result.

For SOS Contador sales queries phrased as `facturas` or `facturas emitidas`, do not assume that the user wants to exclude credit notes or debit notes when those documents also exist in the same filtered period.

If matching notes exist, ask one short follow-up before finalizing the answer:

- whether to show only invoices, or
- invoices plus credit/debit notes

If the user chooses to include those notes, return a single combined table for the period instead of separate lists.

## Multi-Document Receipt Rule

For SOS Contador document-driven receipt work, do not assume that multiple files belong to the same recibo.

Use a single `cobro draft --source ... --source ...` only when the files are complementary pieces of one business document, for example:

- front/back scans of the same order
- continuation pages of the same exported PDF
- annexes that complete the same receipt

If the files show different order numbers, fechas, invoice references, totals, or cheque sets, split them into separate drafts and create one receipt per group.

If a draft preview merges multiple independent orders into one recibo, stop that path and rerun the workflow with one draft per document group before writing anything.

## Repository Safety

- `<SOS_CONTADOR_HOME>/.env.local` is private and must remain outside the repository.
- `./sos-contador-api/.env.local.example` is the public setup template that should be committed.
- Keep this file generic and portable; do not add machine-specific paths or user-specific secrets.
- Keep real-world examples out of public skill files; use `<SOS_CONTADOR_HOME>/local/` for anything concrete from local client work.

## Code Review And Security Tools

- Use `security-best-practices` for explicit security review and whenever changes touch authentication, `.env` loading, API sessions, CUIT-scoped data, local exports, PDF handling, or public skill portability.
- Use `autoreview` as closeout for non-trivial code or skill changes after focused tests/manual checks. Treat findings as advisory and verify each one against the real code path before editing.
- If `autoreview` requires approval because it will send an isolated code bundle to an external reviewer, explicitly request the user's authorization. Do not skip, replace, or downgrade `autoreview` solely because that approval is required; if authorization is denied, report the review as incomplete.
- Use `clawpatch` only for deliberate repo maintenance audits or when the user asks for a findings backlog. Start with `clawpatch status`, `clawpatch map`, `clawpatch review --limit <n>` and `clawpatch report`; `clawpatch fix --finding <id>` requires a clean worktree and explicit confirmation.
- Do not run these tools for ordinary SOS data queries, local exports, or docs-only edits unless review is requested.
