import { defineConfig } from "@hey-api/openapi-ts"

function normalizeMethodName(name: string) {
  const trimmed = name.replace(/^[^-./_]+[-./_]/, "")
  const normalized = trimmed.replace(/[-./_]+([a-zA-Z0-9])/g, (_match, char) =>
    char.toUpperCase(),
  )

  return normalized.charAt(0).toLowerCase() + normalized.slice(1)
}

export default defineConfig({
  input: "./openapi.json",
  output: "./src/client/generated",

  plugins: [
    "@hey-api/typescript",
    "@hey-api/client-axios",
    {
      name: "@hey-api/sdk",
      operations: {
        container: "class",
        containerName: "{{name}}Service",
        methods: "static",
        methodName: normalizeMethodName,
        nesting: "id",
        strategy: "byTags",
      },
    },
    {
      name: "@hey-api/schemas",
      type: "json",
    },
  ],
})
