# Spec: Frontend translation setup

## Goal

Add a maintainable multi language setup to the React + TypeScript frontend using `i18next`, `react-i18next` and JSON translation files.

The goal is to replace hardcoded frontend strings with translation keys, while keeping the setup simple, type safe and compatible with automatic key extraction.

## Context

The frontend is built with:

- React
- TypeScript
- Vite
- Bun

Current situation:

- UI strings are hardcoded in English
- No central translation system exists yet

Target usage in components:

```tsx
const { t } = useTranslation();

return <span>{t('settings.account.description')}</span>;
````

## Requirements

### Translation library

Use the following packages:

```bash
bun add i18next react-i18next i18next-browser-languagedetector
bun add -d i18next-cli
```

Use:

* `i18next` as the translation engine
* `react-i18next` for React integration
* `i18next-browser-languagedetector` for browser language detection
* `i18next-cli` for extracting and syncing translation keys

### Translation file format

Use JSON translation files.

Required structure:

```txt
public/
  locales/
    en/
      translation.json
    nl/
      translation.json
```

Start with these locales:

* `en`
* `nl`

Use English as the fallback language.

### I18n setup

Create:

```txt
src/
  i18n/
    i18n.ts
```

`src/i18n/i18n.ts` must:

* Initialize `i18next`
* Register `initReactI18next`
* Register `i18next-browser-languagedetector`
* Load the JSON resources for `en` and `nl`
* Set `fallbackLng` to `en`
* Set `supportedLngs` to `['en', 'nl']`
* Set `defaultNS` to `translation`
* Set `interpolation.escapeValue` to `false`

Import the i18n setup once in the frontend entrypoint, for example in `src/main.tsx`:

```ts
import './i18n/i18n';
```

## Key conventions

Use explicit dotted keys.

Good:

```tsx
t('settings.account.description')
t('common.save')
t('auth.login.title')
```

Avoid using English text as keys.

Bad:

```tsx
t('Manage your account details')
```

Avoid dynamic keys when possible, because extraction tools may not detect them reliably.

Bad:

```tsx
t(`settings.tabs.${tab}`)
```

Better:

```ts
const tabLabels = {
  profile: 'settings.tabs.profile',
  security: 'settings.tabs.security',
  billing: 'settings.tabs.billing',
} as const;

t(tabLabels[tab]);
```

Use interpolation for values:

```tsx
t('users.invite.success', { email })
```

Example translation:

```json
{
  "users": {
    "invite": {
      "success": "Invitation sent to {{email}}."
    }
  }
}
```

Use i18next pluralization for counts:

```tsx
t('projects.count', { count: projects.length })
```

Example translation:

```json
{
  "projects": {
    "count_one": "{{count}} project",
    "count_other": "{{count}} projects"
  }
}
```

## Extraction setup

Create `i18next.config.ts` in the frontend root.

Suggested config:

```ts
import { defineConfig } from 'i18next-cli';

export default defineConfig({
  locales: ['en', 'nl'],
  defaultLocale: 'en',
  extract: {
    input: ['src/**/*.{ts,tsx}'],
    output: 'src/locales/{{language}}/{{namespace}}.json',
  },
});
```

The extraction command should scan all TypeScript and TSX files and update the locale JSON files.

## Package scripts

Add these scripts to `package.json`:

```json
{
  "scripts": {
    "i18n:extract": "i18next-cli extract",
    "i18n:extract:watch": "i18next-cli extract --watch",
    "i18n:sync": "i18next-cli sync",
    "i18n:types": "i18next-cli types",
    "i18n:status": "i18next-cli status",
    "i18n:check": "i18next-cli extract --ci && i18next-cli status"
  }
}
```

## Type safety

Add i18next TypeScript resource typing.

Create:

```txt
src/@types/i18next.d.ts
```

Example:

```ts
import 'i18next';
import en from '@/locales/en/translation.json';

declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'translation';
    resources: {
      translation: typeof en;
    };
  }
}
```

Make sure this type file is included by the TypeScript configuration.

## Migration instructions

The coding agent must migrate hardcoded frontend strings incrementally.

For each touched component:

1. Import `useTranslation`
2. Add `const { t } = useTranslation();`
3. Replace user facing hardcoded strings with `t('...')`
4. Use clear dotted keys based on feature and component context
5. Run the extraction command
6. Fill the English translation value
7. Add the Dutch translation value where obvious
8. Leave unclear Dutch translations as the English value temporarily if needed

Do not translate:

* API field names
* Internal enum values
* Log messages intended only for developers
* Test selectors
* CSS class names
* Route paths unless they are displayed to the user

Translate:

* Button labels
* Page titles
* Form labels
* Placeholder text
* Empty states
* Error messages shown to users
* Success messages shown to users
* Navigation labels
* Table headers
* Tooltip text

## Validation

Before finishing the implementation, run:

```bash
bun run i18n:extract
bun run i18n:types
bun run i18n:status
bun run typecheck
```

If the project does not have `typecheck`, use the existing TypeScript validation command.

The final implementation should satisfy:

* The app still starts with `bun dev`
* Existing UI behavior remains unchanged
* Translation files exist for English and Dutch
* New translation keys are extracted into JSON files
* Components use `useTranslation`
* No obvious user facing hardcoded English strings remain in migrated components

## Out of scope

Do not add a translation management platform yet.

Do not add backend translation support yet.

Do not translate database values or API responses unless they are explicitly frontend UI labels.

Do not introduce multiple namespaces yet unless the app already has a clear need for it. Start with `translation.json`.
