#!/usr/bin/env bash
set -euo pipefail

BENCH_DIR="${BENCH_DIR:-$HOME/frappe-bench}"
MODE="${MODE:-clean}"
TEST_SITE="${TEST_SITE:-farm-management-v15-test.local}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"

bench_cmd() {
	(
		cd "$BENCH_DIR/sites"
		../env/bin/python -m frappe.utils.bench_helper frappe "$@"
	)
}

assert_v15() {
	local app="$1"
	local branch
	branch="$(git -C "$BENCH_DIR/apps/$app" branch --show-current)"
	if [[ "$branch" != "version-15" ]]; then
		echo "$app must be on version-15, found: $branch" >&2
		exit 1
	fi
}

assert_v15 frappe
assert_v15 erpnext

if [[ "$MODE" == "upgrade" ]]; then
	if [[ ! -d "$BENCH_DIR/sites/$TEST_SITE" ]]; then
		echo "Upgrade test site does not exist: $TEST_SITE" >&2
		exit 1
	fi
	bench_cmd --site "$TEST_SITE" migrate
	bench_cmd --site "$TEST_SITE" migrate
	bench_cmd --site "$TEST_SITE" set-config allow_tests true
	bench_cmd --site "$TEST_SITE" run-tests --module farm_management.tests.test_repository_contracts
	bench_cmd --site "$TEST_SITE" execute farm_management.tests.runtime_smoke.run
	bench_cmd --site "$TEST_SITE" run-tests --app farm_management --skip-test-records
	exit 0
fi

if [[ "$MODE" != "clean" ]]; then
	echo "MODE must be clean or upgrade" >&2
	exit 1
fi
if [[ -d "$BENCH_DIR/sites/$TEST_SITE" ]]; then
	echo "Refusing to overwrite existing site: $TEST_SITE" >&2
	exit 1
fi

new_site_args=(new-site "$TEST_SITE" --admin-password "$ADMIN_PASSWORD")
if [[ -n "${DB_ROOT_PASSWORD:-}" ]]; then
	new_site_args+=(--db-root-password "$DB_ROOT_PASSWORD")
fi
bench_cmd "${new_site_args[@]}"
bench_cmd --site "$TEST_SITE" install-app erpnext
bench_cmd --site "$TEST_SITE" install-app farm_management
bench_cmd --site "$TEST_SITE" migrate
bench_cmd --site "$TEST_SITE" migrate
bench_cmd --site "$TEST_SITE" set-config allow_tests true
bench_cmd --site "$TEST_SITE" run-tests --module farm_management.tests.test_repository_contracts
bench_cmd --site "$TEST_SITE" execute farm_management.tests.runtime_smoke.run
bench_cmd --site "$TEST_SITE" run-tests --app farm_management --skip-test-records

echo "ERPNext v15 clean-install test passed on $TEST_SITE"
