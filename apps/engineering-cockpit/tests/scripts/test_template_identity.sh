#!/usr/bin/env bash
set -euo pipefail

grep -Fx 'PROJECT_NAME="Techletes Engineering Cockpit"' .env.template
grep -Fx 'STACK_NAME=engineering-cockpit' .env.template
