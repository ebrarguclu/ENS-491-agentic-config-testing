#!/usr/bin/env bash
#
# verify_curl_constraints.sh
#
# Re-checks every constraint and effect in models/curl.yaml by running curl's
# `configure` with option combinations that break each rule, then comparing the
# exit code and output with what the model says should happen.
#
# Usage (from the repository root):
#   1. Clone and prepare curl once (see systems/README.md):
#        git clone --depth 1 --branch curl-8_17_0 https://github.com/curl/curl.git systems/curl
#        (cd systems/curl && autoreconf -fi)
#   2. Run:
#        bash scripts/verify_curl_constraints.sh
#
# Takes a few minutes (one `configure` run per check). Logs are written to
# results/verification/. At the end the script re-runs a default `configure`,
# so the curl tree is left in its normal state.
#
# Works on Linux and macOS (on macOS it uses Homebrew's openssl@3).

set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CURL_DIR="${CURL_DIR:-$REPO_ROOT/systems/curl}"
LOG_DIR="$REPO_ROOT/results/verification"

if [ ! -x "$CURL_DIR/configure" ]; then
  echo "error: $CURL_DIR/configure not found."
  echo "Clone curl into systems/curl and run 'autoreconf -fi' first (see systems/README.md)."
  exit 2
fi

# TLS flag: plain --with-openssl on Linux, Homebrew openssl@3 on macOS
if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
  OPENSSL_PREFIX="$(brew --prefix openssl@3)"
  export PKG_CONFIG_PATH="$OPENSSL_PREFIX/lib/pkgconfig"
  TLS="--with-openssl=$OPENSSL_PREFIX"
else
  TLS="--with-openssl"
fi
BASE="--without-libpsl"

mkdir -p "$LOG_DIR"
SUMMARY="$LOG_DIR/summary.md"
{
  echo "# Constraint verification"
  echo
  echo "- Date: $(date '+%Y-%m-%d %H:%M')"
  echo "- Machine: $(uname -sm)"
  echo "- curl: $(cd "$CURL_DIR" && git describe --tags 2>/dev/null || echo unknown)"
  echo
  echo "| Check | configure options | Expected | Observed exit | Result |"
  echo "|---|---|---|---|---|"
} > "$SUMMARY"

PASS=0
FAIL=0

# check ID EXPECTED_EXIT PATTERN DESCRIPTION -- configure options...
#   PATTERN: extended regex that must appear in the configure output
check() {
  local id="$1" want_exit="$2" pattern="$3" desc="$4"
  shift 5
  local log="$LOG_DIR/$id.log"
  (cd "$CURL_DIR" && ./configure $BASE "$@" > "$log" 2>&1)
  local got_exit=$?
  local result="PASS"
  [ "$got_exit" -eq "$want_exit" ] || result="FAIL (exit)"
  grep -Eq "$pattern" "$log" || result="FAIL (output)"
  report "$id" "$*" "$desc" "$got_exit" "$result"
}

# check_protocol ID WORD PRESENT|ABSENT DESCRIPTION -- configure options...
#   Looks at the "Protocols:" line of the configure summary.
check_protocol() {
  local id="$1" word="$2" want="$3" desc="$4"
  shift 5
  local log="$LOG_DIR/$id.log"
  (cd "$CURL_DIR" && ./configure $BASE "$@" > "$log" 2>&1)
  local got_exit=$?
  local protocols
  protocols="$(grep -E '^ +Protocols:' "$log")"
  local result="PASS"
  [ "$got_exit" -eq 0 ] || result="FAIL (exit)"
  if [ "$want" = "ABSENT" ]; then
    echo "$protocols" | grep -qw "$word" && result="FAIL ($word present)"
  else
    echo "$protocols" | grep -qw "$word" || result="FAIL ($word missing)"
  fi
  report "$id" "$*" "$desc" "$got_exit" "$result"
}

report() {
  local id="$1" args="${2:-(none)}" desc="$3" got_exit="$4" result="$5"
  printf '%-14s %-6s %s\n' "$id" "${result%% *}" "$desc"
  echo "| $id | \`${args}\` | $desc | $got_exit | $result |" >> "$SUMMARY"
  case "$result" in PASS) PASS=$((PASS + 1)) ;; *) FAIL=$((FAIL + 1)) ;; esac
}

echo "Running configure checks in $CURL_DIR (logs: $LOG_DIR)"
echo

# ---- constraints (models/curl.yaml) ------------------------------------------
check C1 0 "LDAP needs to be enabled to support LDAPS" \
  "ldaps without ldap: continues, LDAPS silently off" -- \
  $TLS --disable-ldap --enable-ldaps

check C2 1 "select TLS backend" \
  "no TLS choice: stops with an error" --

check C3 0 "disables HSTS due to lack of SSL" \
  "hsts without TLS: continues, HSTS silently off" -- \
  --without-ssl --enable-hsts

check C4 0 "HSTS: +no" \
  "hsts without http: continues, HSTS silently off" -- \
  $TLS --disable-http --enable-hsts

check C5 0 "Alt-svc: +no" \
  "alt-svc without http: continues, alt-svc silently off" -- \
  $TLS --disable-http --enable-alt-svc

check C6 1 "MIME support needs to be enabled" \
  "form-api requested without mime: stops with an error" -- \
  $TLS --disable-mime --enable-form-api

check C6-default 0 "whether to support the form API\.\.\. no" \
  "mime off, form-api default: continues, form-api silently off" -- \
  $TLS --disable-mime

check TLS-conflict 1 "without-ssl has been set together" \
  "--without-ssl with --with-openssl: stops with an error" -- \
  --without-ssl $TLS

# ---- effects --------------------------------------------------------------
check_protocol E1 https ABSENT "no TLS: https not built" -- \
  --without-ssl

check_protocol E2 rtsp ABSENT "no HTTP: rtsp not built" -- \
  $TLS --disable-http

check_protocol E3 ftp ABSENT "no FTP: ftp not built" -- \
  $TLS --disable-ftp

# ---- finding: misleading MQTT message ------------------------------------
check MQTT-msg 0 "whether to support mqtt\.\.\. no" \
  "default build: configure prints 'mqtt... no'" -- \
  $TLS
check_protocol MQTT-built mqtt PRESENT "default build: mqtt is built anyway" -- \
  $TLS

echo
echo "Passed: $PASS   Failed: $FAIL"
{
  echo
  echo "**Passed: $PASS, failed: $FAIL**"
} >> "$SUMMARY"
echo "Summary written to $SUMMARY"

# leave the curl tree in its default configuration
echo "Restoring default configuration..."
(cd "$CURL_DIR" && ./configure $BASE $TLS > "$LOG_DIR/restore.log" 2>&1)

[ "$FAIL" -eq 0 ]
