#!/bin/bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

declare -a SERVICES=(
  "frontend-dev|5173|${repo_root}/frontend|bun run dev"
  "backend-dev|8000|${repo_root}/backend|./scripts/run-dev.sh"
  "worker-dev|-|${repo_root}/backend|./scripts/start-worker.sh"
)

ensure_codex_link() {
  if [[ -d /host-home/.codex ]]; then
    local container_codex_dir="${HOME}/.codex"
    local host_codex_dir="/host-home/.codex"

    if [[ -L "${container_codex_dir}" || -e "${container_codex_dir}" ]]; then
      return 0
    fi

    ln -s "${host_codex_dir}" "${container_codex_dir}"
    echo "Linked ${container_codex_dir} to ${host_codex_dir}."
  fi
}

pid_file() {
  echo "/tmp/$1.pid"
}

log_file() {
  echo "${repo_root}/logs/$1.log"
}

is_port_open() {
  local port="$1"
  ss -ltnH "sport = :${port}" 2>/dev/null | grep -q .
}

is_pid_alive() {
  local pid="$1"
  kill -0 "${pid}" >/dev/null 2>&1
}

service_is_running() {
  local name="$1"
  local port="$2"
  local pid

  if [[ -f "$(pid_file "${name}")" ]]; then
    pid="$(<"$(pid_file "${name}")")"
    if [[ -n "${pid}" ]] && is_pid_alive "${pid}"; then
      return 0
    fi
  fi

  if [[ "${port}" == "-" ]]; then
    return 1
  fi

  is_port_open "${port}"
}

start_service() {
  local name="$1"
  local port="$2"
  local workdir="$3"
  local command="$4"
  local command_prefix=""
  local pid_path
  local log_path

  pid_path="$(pid_file "${name}")"
  log_path="$(log_file "${name}")"

  if service_is_running "${name}" "${port}"; then
    echo "${name} already running on port ${port}."
    return 0
  fi

  rm -f "${pid_path}"
  mkdir -p "$(dirname "${log_path}")"

  if [[ "${name}" == "frontend-dev" ]]; then
    # Bind Vite to all container interfaces so the forwarded port is reachable
    # from the host browser at localhost:5173.
    command_prefix="env FRONTEND_HOST=http://0.0.0.0:5173 "
  fi

  # Detach the dev process from the post-attach shell so container attach
  # teardown does not send SIGHUP to Vite/FastAPI.
  nohup setsid bash -lc "cd \"${workdir}\" && exec ${command_prefix}${command}" </dev/null >"${log_path}" 2>&1 &
  echo $! >"${pid_path}"
  echo "Started ${name}; log: ${log_path}"
}

stop_service() {
  local name="$1"
  local port="$2"
  local pid_path
  local pid
  local attempts=0

  pid_path="$(pid_file "${name}")"

  if [[ ! -f "${pid_path}" ]]; then
    if [[ "${port}" != "-" ]] && is_port_open "${port}"; then
      echo "${name} port ${port} is open, but no pid file found."
    else
      echo "${name} not running."
    fi
    return 0
  fi

  pid="$(<"${pid_path}")"
  if [[ -z "${pid}" ]]; then
    rm -f "${pid_path}"
    echo "${name} pid file empty; removed stale file."
    return 0
  fi

  if ! is_pid_alive "${pid}"; then
    rm -f "${pid_path}"
    echo "${name} not running; removed stale pid file."
    return 0
  fi

  echo "Stopping ${name}..."
  kill "${pid}" >/dev/null 2>&1 || true

  while is_pid_alive "${pid}" && [[ "${attempts}" -lt 20 ]]; do
    sleep 0.5
    attempts=$((attempts + 1))
  done

  if is_pid_alive "${pid}"; then
    echo "Force killing ${name}..."
    kill -9 "${pid}" >/dev/null 2>&1 || true
  fi

  rm -f "${pid_path}"
  echo "${name} stopped."
}

wait_for_service() {
  local name="$1"
  local port="$2"
  local max_attempts="${3:-60}"
  local attempt=1

  echo "Waiting for ${name} on ${port}..."
  while [[ "${attempt}" -le "${max_attempts}" ]]; do
    if is_port_open "${port}"; then
      echo "${name} ready on ${port}."
      return 0
    fi
    sleep 1
    attempt=$((attempt + 1))
  done

  echo "${name} did not become ready."
  tail -n 50 "$(log_file "${name}")" 2>/dev/null || true
  return 1
}

start_all() {
  ensure_codex_link
  export DEVCONTAINER_COMPOSE_SERVICES="${DEVCONTAINER_COMPOSE_SERVICES:-1}"

  for service in "${SERVICES[@]}"; do
    IFS='|' read -r name port workdir command <<<"${service}"
    start_service "${name}" "${port}" "${workdir}" "${command}"
  done

  for service in "${SERVICES[@]}"; do
    IFS='|' read -r name port _workdir _command <<<"${service}"
    if [[ "${port}" != "-" ]]; then
      wait_for_service "${name}" "${port}"
    fi
  done
}

stop_all() {
  for service in "${SERVICES[@]}"; do
    IFS='|' read -r name port _workdir _command <<<"${service}"
    stop_service "${name}" "${port}"
  done
}

restart_all() {
  stop_all
  start_all
}

status_all() {
  for service in "${SERVICES[@]}"; do
    IFS='|' read -r name port _workdir _command <<<"${service}"
    if service_is_running "${name}" "${port}"; then
      echo "${name}: running"
    else
      echo "${name}: stopped"
    fi
  done
}

case "${1:-start}" in
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  restart)
    restart_all
    ;;
  status)
    status_all
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
