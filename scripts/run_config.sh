#!/usr/bin/env bash
#
# run_config.sh: build curl with one configuration, run its tests, save the results.
#
# Usage (from anywhere):
#   scripts/run_config.sh <configuration-file> [tests to run]
#
# Examples:
#   scripts/run_config.sh models/configs/no-ftp.yaml 1 to 100    # tests 1 to 100
#   scripts/run_config.sh models/configs/no-ftp.yaml             # all tests
#
# Results go to results/<configuration-name>/ (an earlier run with that name is replaced):
#   config.yaml        the configuration that was used
#   build.log          output of configure and make
#   tests.log          output of curl's test runner
#   curl_version.txt   `curl --version` of the curl that was really built
#   summary.json       build result and passed/failed/skipped counts
#
# Exit code: 0 = built and no test failed, 1 = build failed or a test failed,
# 2 = could not start (bad arguments, missing setup).
#
# First-time setup: see scripts/README.md.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CURL_DIR="${CURL_DIR:-$REPO_ROOT/systems/curl}"
MODEL="$REPO_ROOT/models/curl.yaml"
PYTHON="$REPO_ROOT/.venv/bin/python"
TOOLS="$REPO_ROOT/scripts/config_tools.py"
JOBS="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)"

# ---- 1. check the input and the setup ----------------------------------------
if [ "$#" -lt 1 ]; then
  sed -n '3,10p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
fi
CONFIG="$1"
shift
TEST_ARGS=("$@")

[ -f "$CONFIG" ] || { echo "error: configuration file not found: $CONFIG"; exit 2; }
[ -d "$CURL_DIR/.git" ] || { echo "error: curl not found in $CURL_DIR (see systems/README.md)"; exit 2; }
[ -x "$PYTHON" ] || { echo "error: $PYTHON not found (see 'First-time setup' in scripts/README.md)"; exit 2; }

# ---- 2. clean up the machine's environment -----------------------------------
# XAMPP ships a pkg-config with broken paths, which makes the build fail. Hide it for
# this script only. Nothing outside this script is changed.
PATH="$(echo "$PATH" | tr ':' '\n' | grep -vi xampp | paste -sd: -)"
export PATH

# On macOS, Homebrew's plain `openssl` is version 4, which curl 8.17.0 cannot use.
OPENSSL_FLAG="--with-openssl"
if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
  OPENSSL_PREFIX="$(brew --prefix openssl@3)"
  [ -d "$OPENSSL_PREFIX" ] || { echo "error: run 'brew install openssl@3' first"; exit 2; }
  export PKG_CONFIG_PATH="$OPENSSL_PREFIX/lib/pkgconfig"
  OPENSSL_FLAG="--with-openssl=$OPENSSL_PREFIX"
fi

# ---- 3. turn the configuration into configure flags --------------------------
FLAGS_OUTPUT="$("$PYTHON" "$TOOLS" flags "$MODEL" "$CONFIG")" || exit 2
NAME="$(echo "$FLAGS_OUTPUT" | sed -n 's/^name=//p')"

# libpsl is not one of our options, but configure stops if it is missing.
FLAGS=(--without-libpsl)
while IFS= read -r flag; do
  case "$flag" in
    name=*) ;;
    --with-openssl) FLAGS+=("$OPENSSL_FLAG") ;;
    *) FLAGS+=("$flag") ;;
  esac
done <<< "$FLAGS_OUTPUT"

RESULTS="$REPO_ROOT/results/$NAME"
mkdir -p "$RESULTS"
rm -f "$RESULTS/build.log" "$RESULTS/tests.log" "$RESULTS/curl_version.txt" "$RESULTS/summary.json"
cp "$CONFIG" "$RESULTS/config.yaml"
BUILD_LOG="$RESULTS/build.log"

echo "Configuration: $NAME"
echo "Flags:         ${FLAGS[*]}"

# ---- 4. build ----------------------------------------------------------------
CONFIGURE_EXIT=""
MAKE_EXIT=""
TESTS_BUILD_EXIT=""
RUNTESTS_EXIT=""
TEST_SECONDS=""
SECONDS=0

# Remove the previous build, so nothing from another configuration is left behind.
[ -f "$CURL_DIR/Makefile" ] && (cd "$CURL_DIR" && make distclean) >/dev/null 2>&1
if [ ! -x "$CURL_DIR/configure" ]; then
  echo "Preparing the build files (autoreconf)..."
  (cd "$CURL_DIR" && autoreconf -fi) >> "$BUILD_LOG" 2>&1
fi

echo "[1/3] configure..."
(cd "$CURL_DIR" && ./configure "${FLAGS[@]}") >> "$BUILD_LOG" 2>&1
CONFIGURE_EXIT=$?

if [ "$CONFIGURE_EXIT" -eq 0 ]; then
  echo "[2/3] make..."
  (cd "$CURL_DIR" && make -j"$JOBS") >> "$BUILD_LOG" 2>&1
  MAKE_EXIT=$?
fi
if [ "$MAKE_EXIT" = "0" ]; then
  (cd "$CURL_DIR" && make -j"$JOBS" -C tests) >> "$BUILD_LOG" 2>&1
  TESTS_BUILD_EXIT=$?
  "$CURL_DIR/src/curl" --version > "$RESULTS/curl_version.txt" 2>&1
fi
BUILD_SECONDS=$SECONDS

# ---- 5. run the tests --------------------------------------------------------
if [ "$TESTS_BUILD_EXIT" = "0" ]; then
  echo "[3/3] Running tests: ${TEST_ARGS[*]:-all}..."
  SECONDS=0
  # -a: keep going after a failed test. -n: do not use valgrind.
  (cd "$CURL_DIR/tests" && perl runtests.pl -a -n ${TEST_ARGS[@]+"${TEST_ARGS[@]}"}) \
    > "$RESULTS/tests.log" 2>&1
  RUNTESTS_EXIT=$?
  TEST_SECONDS=$SECONDS
else
  echo "Build failed, see $BUILD_LOG"
fi

# ---- 6. write summary.json ---------------------------------------------------
"$PYTHON" "$TOOLS" summary "$RESULTS" \
  --name "$NAME" \
  --machine "$(uname -sm)" \
  --curl-source "$(git -C "$CURL_DIR" describe --tags 2>/dev/null || echo unknown)" \
  --date "$(date '+%Y-%m-%d %H:%M')" \
  --flags="${FLAGS[*]}" \
  --test-args="${TEST_ARGS[*]:-}" \
  --configure-exit "$CONFIGURE_EXIT" \
  --make-exit "$MAKE_EXIT" \
  --tests-build-exit "$TESTS_BUILD_EXIT" \
  --runtests-exit "$RUNTESTS_EXIT" \
  --build-seconds "$BUILD_SECONDS" \
  --test-seconds "$TEST_SECONDS"
