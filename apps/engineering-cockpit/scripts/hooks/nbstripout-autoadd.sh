#!/usr/bin/env bash
set -e

# Run nbstripout on all files passed by pre-commit. When invoked without
# filenames, process every tracked notebook so repository-owned outputs cannot
# remain in a notebook merely because its parent directory is excluded from
# other pre-commit hooks.
if (($# == 0)); then
    notebooks=()
    while IFS= read -r -d '' notebook; do
        [[ -f "${notebook}" ]] || continue
        notebooks+=("${notebook}")
    done < <(git ls-files -z -- '*.ipynb')
    set -- "${notebooks[@]}"
fi

if (($# > 0)); then
    nbstripout "$@"
fi

# Re-add any modified .ipynb files to the index
modified=$(git ls-files -m '*.ipynb') || true

if [ -n "$modified" ]; then
  echo "🔁 Re-staging modified notebooks:"
  echo "$modified"
  while IFS= read -r notebook; do
    [ -n "$notebook" ] && git add -- "$notebook"
  done <<< "$modified"
fi
