# Commit-pinned devcontainer images

Every successful shared devcontainer publish also receives a 12-character source commit tag, for example:

```text
ghcr.io/techletes/devcontainer:c8f6df6bac0f
```

Use this tag in consuming repositories when you want the devcontainer to stay on the exact published build until the repository explicitly updates it.

The release workflow does not overwrite an existing commit tag. If the same commit is published again (for example by a semantic-version release after the main-branch publish), the existing commit tag is preserved while the other aliases are updated.

The GHCR retention policy still keeps only the three newest top-level images. A commit tag is therefore immutable while retained, but it is not retained forever: repositories pinned to a build older than the retention window must be updated before that image is pruned.
