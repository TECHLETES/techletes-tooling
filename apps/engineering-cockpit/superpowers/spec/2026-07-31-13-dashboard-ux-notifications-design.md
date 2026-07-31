# 13 — Dashboard UX, Generated API Client, Live Activity, and Notifications Specification

## Purpose

Define the browser experience for operating many repositories and Codex tasks from one cockpit. The UI must expose the precise backend state and allowed actions without becoming a second orchestration engine.

The dashboard is built on the current full-stack template's React, TanStack Router/Query, generated OpenAPI client, service-layer, authentication, component-library, and i18n conventions.

## UX principles

1. **One source of state:** lifecycle and allowed actions come from the backend.
2. **No fake progress:** show concrete phases and recent activity, not invented percentages or “almost done” claims.
3. **Attention first:** input, approvals, recovery, validation failure, and ready-for-review are visually distinct.
4. **Safe controls:** destructive or irreversible actions require exact confirmation and server-side revalidation.
5. **Reconnectable:** connection loss is shown separately from task state.
6. **Reviewable:** conversation, changes, validation, and delivery evidence stay linked to the same task.
7. **Accessible:** all operations work by keyboard and with assistive technology.
8. **Scalable locally:** dozens of tasks and long event streams remain responsive through virtualization and bounded data.

## Information architecture

Primary route:

```text
/cockpit
```

Selected task is encoded in the URL query (for MVP):

```text
/cockpit?repository=<uuid>&task=<uuid>&tab=activity
```

This makes links/bookmarks useful without requiring many nested route files. The server still authorizes every selected ID.

Desktop layout:

```text
+----------------------+---------------------------+-----------------------------------+
| Repositories         | Tasks                     | Selected task                     |
| search / diagnostics | filter / attention        | header + tabs + current control   |
|                      |                           | activity / agent / changes        |
|                      |                           | validation / delivery / runtime   |
+----------------------+---------------------------+-----------------------------------+
```

On narrow screens, panes become an accessible drill-down stack with a back control; no information is hidden only by hover.

## Repository pane

Shows:

- display name and GitHub full name;
- active/attention/ready task counts;
- static/active diagnostics state;
- trust status;
- refresh/validate control;
- add repository control for authorized users.

Blocked repositories show the most actionable diagnostic, with a link to full diagnostics. Local paths are shown only to users with permission and never included in browser notifications.

## Task list

Each row shows:

- title/source (manual, issue, preset);
- branch;
- concrete lifecycle label;
- attention icon;
- latest meaningful activity and timestamp;
- validation/PR badge where applicable;
- connection/recovery indicator;
- overlap warning.

Filters:

- repository;
- active/needs-input/needs-approval/recovery/ready/completed;
- source type;
- assigned owner;
- search title/issue/branch.

The UI receives a backend-derived `allowed_actions` set per task. Buttons are enabled from that set, not from duplicated frontend state-machine logic.

## Task creation

A drawer/dialog supports:

### Source

- free-text task;
- GitHub issue number with preview and snapshot hash;
- approved preset (dependency update, template sync, CI/review repair, analysis).

### Configuration

- repository;
- title;
- base branch from allowed list;
- execution profile;
- relevant child spec/implementation-plan paths when this is cockpit development;
- optional start immediately;
- closed-issue acknowledgement;
- repository trust/diagnostic blockers.

Before creation, show a concise execution summary:

```text
branch/worktree -> devcontainer -> app-server -> thread/turn
```

Do not expose or allow arbitrary host paths, executable commands, environment values, sandbox JSON, or credential settings in this form.

## Task detail header

Always visible:

- repository/title/source link;
- state and attention;
- branch/base/head;
- devcontainer/app-server connection status;
- latest validation and PR status;
- overlap/base-divergence warning;
- elapsed activity time and last event time;
- server connection banner when disconnected/recovering.

Controls are grouped by safety:

- routine: send follow-up, steer, validate, refresh;
- lifecycle: interrupt, stop, resume;
- delivery: commit, push, create/update draft PR;
- destructive/admin: force-stop, force-with-lease, cleanup/rebuild.

Only backend-allowed controls render enabled. Every command sends expected task/request version, exact turn/head/review snapshot where required, and an idempotency key.

## Tabs

### Activity

Chronological normalized events grouped by phase. High-frequency deltas render as consolidated entries. Users can filter by agent, command, Git, validation, delivery, warning, and audit.

The event list is virtualized. It retains event IDs and indicates replay/live boundary. Infrastructure diagnostics are separate from model conversation.

### Agent

Shows reconstructed agent messages, current turn, pending questions/approvals, and a response composer.

- follow-up composer only when no active turn;
- steering composer only when active and allowed;
- pending server requests take precedence;
- interruption/stop controls have exact semantics from subsystem 09;
- no generic “send” button that ambiguously decides follow-up versus steering.

### Changes

Shows status groups, diff statistics, file tree, bounded escaped unified diff, binary/oversized/generated markers, secret warnings, review snapshot freshness, and overlap evidence.

Path selection feeds explicit commit staging. Rendering never injects source HTML or terminal escapes.

### Validation

Shows profile selection, current/freshness status, step timeline, attempts, durations, exit status, bounded output tails, artifacts, changed paths from mutating steps, rerun/cancel controls, and authorized override flow.

### Delivery

Shows local commit, remote branch SHA, issue snapshot, PR title/link/draft state, checks, reviews, merge-state evidence, refresh timestamp, failed log/review-detail retrieval, and explicit push/PR/ready-for-review actions.

There is no merge or deploy button.

### Runtime

Shows safe repository/worktree/container/app-server/thread metadata, versions, diagnostics, resource conflicts, config/schema/skill/profile fingerprints, recovery evidence, and local log references.

Sensitive host paths/account details are permission-gated and not copied by default.

## Clarification and approval UI

Pending requests appear:

- inline at the top of Agent tab;
- in the global attention queue;
- optionally as a modal/drawer when selected;
- through browser notification when enabled.

Requirements:

- exact question labels/options/free-text rules;
- command approval shows argv summary, cwd, network/escalation reason;
- file-change approval shows affected paths/diff reference;
- approve/reject actions are visually distinct;
- focus is trapped correctly in modal and returns to trigger;
- resolving state disables duplicate submission;
- stale/two-tab 409 refreshes the request and explains what happened.

No countdown implies auto-approval. Pending duration is informational.

## Event WebSocket client

One connection per browser tab:

1. load last applied event ID from durable browser storage;
2. connect authenticated WebSocket;
3. process hello and compare `serverInstanceId`;
4. if instance changed, refetch snapshots;
5. apply replay/live events strictly by ID;
6. deduplicate IDs;
7. detect gaps and reconnect/replay;
8. store cursor only after application to state/query cache;
9. handle 1013 with exponential backoff and jitter;
10. handle retention reset by snapshot reload.

The socket client updates TanStack Query caches or invalidates targeted queries. It does not refetch every message delta. Terminal/summary events trigger authoritative detail refreshes.

## REST client and service layer

OpenAPI remains generated from backend schemas. Components do not call generated functions directly. Domain services under `frontend/src/services/` expose:

- repositories/diagnostics;
- tasks/controls;
- interactions;
- events/snapshots;
- review/validation/commit;
- issues/delivery;
- recovery/cleanup.

Services preserve expected-version/head/request/snapshot fields and return typed errors. No `any` casts around new/unknown enum values.

## Connection and error states

Separate banners/states:

- browser offline;
- WebSocket reconnecting;
- backend draining/recovering;
- task process disconnected;
- task recovery required;
- API command outcome unknown.

A network error after a mutating command uses its idempotency key for retry; the UI never optimistically marks the command successful.

Errors show stable code, concise message, and diagnostic reference. Raw stderr/stack traces are hidden by default.

## Notifications

Use the browser Notification API only after explicit user opt-in.

Notify on durable transition events:

- clarification required;
- approval required;
- recovery required;
- validation failed;
- task ready for review;
- PR checks/review ready or failed/action required.

Rules:

- deduplicate by event ID;
- no prompt, source diff, command output, local path, account detail, or secret in notification body;
- clicking focuses/navigates to exact task/request;
- optional sound disabled by default;
- no notification storm for repeated poll/heartbeat/delta events;
- notification permission denial does not affect task execution.

## Open in editor

An explicit action opens the known task worktree in VS Code Remote WSL. Prefer a backend command using the registered path and fixed `code` executable, or a carefully encoded `vscode-remote` URI. The browser never supplies an arbitrary path. Failure is diagnostic only.

## i18n and copy

All visible strings use the template's i18n structure. Initial languages follow the template's supported locales. Stable technical terms remain consistent:

- task;
- worktree;
- devcontainer;
- turn;
- interrupt;
- stop;
- resume;
- force-stop;
- validation;
- draft pull request;
- recovery required.

Do not label force-stop as ordinary stop or `READY_FOR_REVIEW` as merged/done.

## Accessibility

- WCAG 2.2 AA target;
- keyboard navigation for panes/tabs/lists/dialogs;
- semantic headings/landmarks;
- status changes announced through restrained live regions;
- icons always have text/accessible labels;
- color is not the only status signal;
- focus management for incoming requests and reconnect errors;
- reduced-motion support;
- virtualized lists preserve screen-reader context.

## Performance

- virtualize event/task lists above configured thresholds;
- paginate history and diffs;
- avoid rendering raw terminal streams;
- coalesce query-cache updates;
- lazy-load heavy diff/log panels;
- cancel stale REST requests on task switch;
- preserve selected task/tab in URL.

## Security

- rely on inherited authenticated session and backend authorization;
- escape all model/Git/GitHub/log text;
- no dangerous HTML rendering;
- no secrets in local storage; only event cursor and non-sensitive UI preferences;
- typed confirmations for destructive controls;
- no browser-provided filesystem path or command;
- external links use safe target/rel behavior.

## Testing strategy

Component/service tests:

- generated-client wrappers and typed error mapping;
- event ID ordering/dedupe/gap/reconnect/retention reset;
- task allowed-actions behavior;
- clarification/approval forms and stale resolution;
- safe diff/log rendering;
- destructive confirmations;
- notification dedupe/privacy;
- accessibility checks.

Playwright:

- repository onboarding and diagnostics;
- manual/issue task creation;
- two concurrent tasks;
- live events with browser close/reopen;
- clarification/approval;
- follow-up/steer/interrupt/stop/resume;
- validation/review/commit;
- push/draft PR/CI status;
- backend instance restart/recovery;
- slow socket/replay reset;
- responsive and keyboard-only flows.

## Acceptance criteria

- A developer can create and control multiple tasks without opening separate terminals.
- UI never invents lifecycle state or progress.
- Event replay and server-instance change are visible and correct.
- Questions/approvals are clear, accessible, and resolve exactly once.
- Changes, validation, and delivery evidence are reviewable in one task context.
- Destructive controls are separated and confirmed.
- Notifications are useful, private, and deduplicated.
- Core workflows pass keyboard/accessibility and responsive tests.

## Research basis

- [Techletes full-stack template frontend conventions](https://github.com/TECHLETES/full-stack-template)
- [TanStack Router](https://tanstack.com/router/latest)
- [TanStack Query](https://tanstack.com/query/latest)
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [MDN Notifications API](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
