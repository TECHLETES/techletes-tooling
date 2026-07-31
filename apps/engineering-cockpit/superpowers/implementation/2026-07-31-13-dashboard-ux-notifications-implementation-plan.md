# 13 — Dashboard UX, Generated API Client, Live Activity, and Notifications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `techletes-superpowers:subagent-driven-development` or `techletes-superpowers:executing-plans`. Backend subsystems 02–12 must have stable OpenAPI schemas first.

**Goal:** Deliver the authenticated three-pane cockpit UI, replayable event client, exact interaction controls, change/validation/delivery views, and privacy-safe notifications.

**Architecture:** Add one TanStack route under the inherited layout, use generated OpenAPI clients only through feature services, keep lifecycle truth in backend snapshots/events, and maintain one reconnectable WebSocket event stream per tab.

**Tech stack:** React 19, TypeScript strict mode, TanStack Router/Query, inherited component library/auth/i18n, `@tanstack/react-virtual`, Vitest + Testing Library, Playwright + axe.

## Global constraints

- Components never infer allowed lifecycle actions; use backend `allowed_actions`.
- No optimistic success for mutating commands.
- No raw HTML/ANSI rendering.
- No filesystem path/command input from the browser.
- Keep event cursor/preferences only in browser storage; no secrets/content.
- Every visible string uses i18n.

---

### Task 1: Establish frontend test and virtualization dependencies

**Files:**
- Modify: `apps/engineering-cockpit/frontend/package.json`
- Modify: `apps/engineering-cockpit/frontend/bun.lock`
- Create: `apps/engineering-cockpit/frontend/vitest.config.ts`
- Create: `apps/engineering-cockpit/frontend/src/test/setup.ts`

- [ ] Add the template-compatible versions of:

```text
@tanstack/react-virtual
vitest
jsdom
@testing-library/react
@testing-library/user-event
@testing-library/jest-dom
@axe-core/playwright
```

- [ ] Add scripts `test:unit`, `test:unit:watch`, and keep existing Playwright scripts.
- [ ] Configure DOM cleanup, matchers, QueryClient wrapper, router test wrapper, and mocked Notification/WebSocket utilities.
- [ ] Add one smoke component test proving the harness.
- [ ] Run `bun run typecheck` and `bun run test:unit`.
- [ ] Commit: `test: configure cockpit frontend tests`.

### Task 2: Generate and wrap stable backend clients

**Files:**
- Regenerate: `apps/engineering-cockpit/frontend/src/client/`
- Create: `apps/engineering-cockpit/frontend/src/services/CockpitRepositoryService.ts`
- Create: `apps/engineering-cockpit/frontend/src/services/CockpitTaskService.ts`
- Create: `apps/engineering-cockpit/frontend/src/services/CockpitInteractionService.ts`
- Create: `apps/engineering-cockpit/frontend/src/services/CockpitRecoveryService.ts`
- Consolidate/modify: service files created by subsystems 11/12
- Create: `apps/engineering-cockpit/frontend/src/services/__tests__/cockpitServices.test.ts`

- [ ] Run the template's generated-client command and commit generated changes.
- [ ] Wrap every cockpit API by domain; components cannot import generated functions directly.
- [ ] Require expected versions/turn IDs/head SHAs/review hashes/idempotency keys in service method signatures.
- [ ] Map API problem responses to a typed `CockpitApiError` preserving stable error code, HTTP status, diagnostic ID, and latest resource version where supplied.
- [ ] Preserve unknown backend enum values as explicit `unknown`, not `as` casts.
- [ ] Test request construction and 409/422/403/network error mapping.
- [ ] Commit: `feat: add typed cockpit frontend services`.

### Task 3: Add i18n namespace and stable terminology

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/locales/en/cockpit.json`
- Create: `apps/engineering-cockpit/frontend/src/locales/nl/cockpit.json`
- Modify: `apps/engineering-cockpit/frontend/src/i18n.ts` or the exact template i18n registration module
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/i18nKeys.ts`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/__tests__/i18n.test.ts`

- [ ] Add keys for all lifecycle states, attention states, actions, errors, tabs, forms, confirmations, notifications, and connection states.
- [ ] Keep technical terms consistent; do not translate stop/force-stop into the same copy.
- [ ] Add a test that every English key exists in Dutch and no component uses hardcoded user-facing cockpit strings.
- [ ] Commit: `feat: add cockpit interface translations`.

### Task 4: Implement the event-stream client

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/events/CockpitEventClient.ts`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/events/models.ts`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/events/cursorStore.ts`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/events/__tests__/CockpitEventClient.test.ts`

**Interfaces:**

```typescript
class CockpitEventClient {
  connect(options: ConnectOptions): void
  subscribeTaskIds(taskIds: string[]): void
  close(): void
  onEvent(listener: (event: CockpitEventPublic) => void): () => void
  onConnection(listener: (state: ConnectionState) => void): () => void
}
```

- [ ] Implement authenticated URL construction, hello parsing, instance-ID comparison, replay/live ID ordering, dedupe, gap detection, heartbeat, 1013 retry with jitter, retention-reset callback, and clean close.
- [ ] Store only last fully applied event ID and server instance ID under versioned keys.
- [ ] Never mark cursor applied until all listeners/query updates succeed.
- [ ] Test browser offline, fragmented/reordered mock frames, duplicate, gap, instance change, retention reset, slow-close retry, auth close, and manual close.
- [ ] Commit: `feat: add replayable cockpit event client`.

### Task 5: Integrate events with TanStack Query

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/events/CockpitEventProvider.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/events/queryUpdates.ts`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/events/useCockpitConnection.ts`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/events/__tests__/queryUpdates.test.tsx`

- [ ] Mount one provider inside the authenticated layout.
- [ ] Update task list/detail caches for lifecycle/attention events; append activity pages by ID; invalidate authoritative detail on terminal/state/delivery/validation events.
- [ ] Coalesce message/output delta updates on animation frame/short timer.
- [ ] On server instance change or retention reset, refetch repository/task snapshots before resuming cursor.
- [ ] Expose connection/recovering/draining state separately from task state.
- [ ] Test no refetch per delta, terminal refresh, task switch, and provider unmount.
- [ ] Commit: `feat: connect cockpit events to query cache`.

### Task 6: Add the cockpit route and responsive shell

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/routes/_layout/cockpit.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/CockpitPage.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/CockpitShell.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/useCockpitSearch.ts`
- Modify: the inherited authenticated navigation component to add Cockpit link
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/__tests__/CockpitShell.test.tsx`

- [ ] Define typed search params `repository`, `task`, and `tab` with safe defaults.
- [ ] Build desktop three-pane layout and narrow-screen drill-down with semantic landmarks/headings.
- [ ] Preserve selected IDs/tab in URL and handle unauthorized/deleted selections by clearing safely.
- [ ] Add connection/recovery banner region.
- [ ] Test keyboard pane navigation, query deep link, responsive mode, and auth route protection.
- [ ] Commit: `feat: add cockpit dashboard shell`.

### Task 7: Build repository list, onboarding, and diagnostics

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/repositories/RepositoryPane.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/repositories/AddRepositoryDialog.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/repositories/RepositoryDiagnosticsDrawer.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/repositories/__tests__/*.test.tsx`

- [ ] List/search repositories with task counts, trust, and diagnostics badges.
- [ ] Add repository by approved path through backend form; do not expose arbitrary command/config fields.
- [ ] Display static/active diagnostics, safe remediation, refresh, and permission-gated path detail.
- [ ] Block task creation from repositories with hard diagnostics/trust failure.
- [ ] Test add success/errors, diagnostics refresh, local-path permission, and keyboard/focus behavior.
- [ ] Commit: `feat: manage cockpit repositories`.

### Task 8: Build task creation flow

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/tasks/CreateTaskDialog.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/tasks/IssueSourceStep.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/tasks/TaskExecutionSummary.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/tasks/__tests__/CreateTaskDialog.test.tsx`

- [ ] Implement manual/issue/preset source selection.
- [ ] Issue source previews immutable snapshot and requires closed-issue acknowledgement.
- [ ] Restrict base/profile/preset to backend allowed values.
- [ ] For cockpit child implementation, select exact committed spec/plan references.
- [ ] Show branch/worktree/devcontainer/app-server/thread-turn execution summary.
- [ ] Create with idempotency key; no optimistic task status.
- [ ] Test all source types, changed issue hash, blocked diagnostics, invalid profile, duplicate submit, and focus management.
- [ ] Commit: `feat: create cockpit tasks from dashboard`.

### Task 9: Build virtualized task list and attention filters

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/tasks/TaskPane.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/tasks/TaskRow.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/tasks/TaskFilters.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/tasks/__tests__/TaskPane.test.tsx`

- [ ] Render lifecycle, attention, branch, latest meaningful activity, validation/PR, connection/recovery, and overlap.
- [ ] Use `@tanstack/react-virtual` after threshold and paginate backend results.
- [ ] Add filters/search with URL/local non-sensitive preference as appropriate.
- [ ] Keep status accessible by text/icon, not color only.
- [ ] Test 100+ tasks, keyboard selection, live update, filter, deleted task, and screen-reader labels.
- [ ] Commit: `feat: show cockpit task attention list`.

### Task 10: Build task header and exact action controls

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/TaskDetail.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/TaskHeader.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/TaskActions.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/ConfirmationDialog.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/__tests__/TaskActions.test.tsx`

- [ ] Render metadata/status and only enable controls in backend `allowed_actions`.
- [ ] Pass exact task version, turn/head/review/request references and idempotency key.
- [ ] Group routine/lifecycle/delivery/destructive actions.
- [ ] Add typed confirmations for force-stop, force-with-lease, rebuild, and cleanup.
- [ ] Handle 409 by refetching and explaining stale state; network-unknown offers idempotent retry.
- [ ] Test every allowed-action combination and no merge/deploy controls.
- [ ] Commit: `feat: control cockpit task lifecycle`.

### Task 11: Build activity and agent panels

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/ActivityPanel.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/AgentPanel.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/AgentMessage.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/TurnComposer.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/__tests__/ActivityAgent.test.tsx`

- [ ] Virtualize/paginate activity, group by phase, and filter event categories.
- [ ] Reconstruct agent messages from normalized final/delta events without raw protocol display.
- [ ] Render separate follow-up and steering composer based on allowed action; pending requests suppress ambiguous send.
- [ ] Add interrupt/stop/resume semantics and latest activity indicator without percentage.
- [ ] Test long history, replay/live boundary, interleaved messages, steering/completion race response, and keyboard operation.
- [ ] Commit: `feat: display live cockpit activity and agent turns`.

### Task 12: Build clarification and approval experience

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/interactions/AttentionQueue.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/interactions/ProtocolRequestCard.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/interactions/ProtocolRequestDialog.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/interactions/__tests__/ProtocolRequestDialog.test.tsx`

- [ ] Render grouped questions/options/free text and command/file-change safe summaries/diff references.
- [ ] Keep approve/reject visually and semantically distinct.
- [ ] Submit exact request version and disable while answering.
- [ ] On stale 409, refresh and announce resolution by another actor/tab.
- [ ] Implement focus trap/return, live-region status, and no countdown/auto action.
- [ ] Test every request kind, required answers, invalid option, rejection, duplicate tab, connection loss, and accessibility.
- [ ] Commit: `feat: answer codex requests from dashboard`.

### Task 13: Build changes, validation, and commit panels

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/ChangesPanel.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/DiffViewer.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/ValidationPanel.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/CommitDialog.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/__tests__/ReviewValidationCommit.test.tsx`

- [ ] Render changed-file groups, stats, selected file, escaped virtualized diff, binary/oversized/generated/sensitive markers, snapshot freshness, and overlap.
- [ ] Render validation profiles/steps/attempts/log tails/artifacts/mutation/freshness with run/cancel/rerun/override controls.
- [ ] Commit dialog selects exact paths, displays current gate/snapshot, accepts user-approved message, and explains hooks/signing.
- [ ] Test path selection, stale diff/validation, sensitive warning, hook/signing failure, subset commit, and no unsafe source rendering.
- [ ] Commit: `feat: review validate and commit cockpit changes`.

### Task 14: Build delivery and runtime panels

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/DeliveryPanel.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/ChecksList.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/RuntimePanel.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/__tests__/DeliveryRuntime.test.tsx`

- [ ] Render issue snapshot/change indicator, local/remote SHAs, push/force, draft PR content/status, checks/reviews/merge evidence, failed detail preview, and ready/draft controls.
- [ ] There is no merge/deploy UI.
- [ ] Render permission-gated safe runtime versions/IDs/fingerprints/resource conflicts/recovery/log references.
- [ ] Test head divergence, rate limit, unknown check status, changes requested, force confirmation, sensitive path hiding, and recovery evidence.
- [ ] Commit: `feat: show cockpit delivery and runtime evidence`.

### Task 15: Add privacy-safe browser notifications

**Files:**
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/notifications/NotificationService.ts`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/notifications/NotificationSettings.tsx`
- Create: `apps/engineering-cockpit/frontend/src/features/cockpit/notifications/__tests__/NotificationService.test.ts`

- [ ] Request permission only from explicit settings action.
- [ ] Trigger only on durable whitelisted event types and dedupe by event ID.
- [ ] Use generic safe title/body; no prompt, diff, command output, local path, account detail, or issue comment.
- [ ] Click navigates/focuses exact task/request.
- [ ] Sound preference off by default and no repeated poll/delta storm.
- [ ] Test granted/denied/default, duplicate, click, hidden/visible tab policy, sensitive payload, and unsupported browser.
- [ ] Commit: `feat: notify cockpit attention events`.

### Task 16: Add open-in-editor control

**Files:**
- Create: `apps/engineering-cockpit/backend/api/routes/cockpit_editor.py`
- Create: `apps/engineering-cockpit/backend/cockpit/editor/service.py`
- Modify: `apps/engineering-cockpit/backend/api/main.py`
- Create: `apps/engineering-cockpit/frontend/src/services/CockpitEditorService.ts`
- Modify: `apps/engineering-cockpit/frontend/src/features/cockpit/task-detail/TaskActions.tsx`
- Create: backend/frontend tests.

- [ ] Backend accepts only task ID, resolves registered worktree, executes fixed `code <path>` or returns a safely encoded supported URI.
- [ ] No browser path/executable argument.
- [ ] Test WSL `code` missing, unauthorized task, cleaned worktree, path with spaces, and success.
- [ ] Treat failure as diagnostics; never affect task state.
- [ ] Commit: `feat: open task worktrees in editor`.

### Task 17: Accessibility, responsive, and failure-state audit

**Files:**
- Create: `apps/engineering-cockpit/frontend/e2e/cockpit-accessibility.spec.ts`
- Create: `apps/engineering-cockpit/frontend/e2e/cockpit-responsive.spec.ts`
- Modify affected cockpit components.

- [ ] Run axe on shell, task dialog, request dialog, diff/validation/delivery panels.
- [ ] Complete core workflow keyboard-only.
- [ ] Test narrow/mobile drill-down, reduced motion, 200% zoom, and color-independent statuses.
- [ ] Test browser offline, socket reconnect, backend recovering/draining, API unknown outcome, task recovery required.
- [ ] Fix all critical/serious axe findings and document justified exceptions.
- [ ] Commit: `test: harden cockpit accessibility and responsiveness`.

### Task 18: Full Playwright cockpit flow

**Files:**
- Create: `apps/engineering-cockpit/frontend/e2e/cockpit-flow.spec.ts`
- Create: `apps/engineering-cockpit/frontend/e2e/cockpit-reconnect.spec.ts`

- [ ] Drive fake external adapters through repository add, manual/issue task, two concurrent tasks, events, request resolution, follow-up/steer/interrupt/stop/resume, validation/review/commit, push/draft PR/status, backend restart/recovery, retention reset, and cleanup-ready state.
- [ ] Assert no separate terminal is needed and no merge/deploy control exists.
- [ ] Run against desktop and narrow viewport projects.
- [ ] Commit: `test: cover cockpit dashboard workflow`.

### Task 19: Complete subsystem verification

```bash
cd apps/engineering-cockpit/frontend
bun run generate-client
bun run typecheck
bun run lint
bun run test:unit
bun run test:e2e -- cockpit-flow.spec.ts cockpit-reconnect.spec.ts cockpit-accessibility.spec.ts cockpit-responsive.spec.ts
```

- [ ] Verify generated route tree/client/i18n files are current and committed.
- [ ] Commit: `test: verify cockpit dashboard`.

## Exit criteria

Subsystem 13 is complete when a developer can operate two concurrent tasks from one accessible reconnectable dashboard; all controls use backend-allowed actions and exact versions/IDs; questions, diffs, gates, and PR evidence are integrated; and browser notifications are useful without exposing sensitive task content.
