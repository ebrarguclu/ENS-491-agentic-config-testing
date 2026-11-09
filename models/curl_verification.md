# Verification of the curl Model

Every constraint and effect in [`curl.yaml`](curl.yaml) was confirmed by running curl's
`configure` with a combination of options that breaks the rule, and checking the exit
code and the configuration summary. Version: `curl-8_17_0`.

Environments:

- **Linux:** Ubuntu 24.04.5, gcc 13.3, OpenSSL 3.0.13, no LDAP libraries installed.
- **macOS:** Apple Silicon, Homebrew OpenSSL 3.5.9, system LDAP libraries.

## Results

| Rule | What we asked for | What configure did | Exit | Behaviour |
|---|---|---|---|---|
| C1 ldaps → ldap | `--disable-ldap --enable-ldaps` (macOS) | Printed *"LDAP needs to be enabled to support LDAPS"*, summary `LDAPS: no` | 0 | silent |
| C2 TLS required | no TLS option (Linux) | *"select TLS backend(s) or disable TLS with --without-ssl."* | 1 | error |
| C3 hsts → TLS | `--without-ssl --enable-hsts` (Linux) | Printed *"disables HSTS due to lack of SSL"*, summary `HSTS: no` | 0 | silent |
| C4 hsts → http | `--disable-http --enable-hsts` (Linux) | Printed `checking whether to support HSTS... yes`, but summary `HSTS: no` | 0 | silent, misleading |
| C5 alt-svc → http | `--disable-http --enable-alt-svc` (Linux) | Printed `checking whether to support alt-svc... yes`, but summary `Alt-svc: no` | 0 | silent, misleading |
| C6 form-api → mime | `--disable-mime --enable-form-api` (Linux) | *"MIME support needs to be enabled in order to enable form API support"* | 1 | error |
| C6, default | `--disable-mime` (Linux) | `checking whether to support the form API... no` | 0 | silent |
| ldap libraries | `--enable-ldap`, no LDAP libraries (Linux) | *"couldn't detect the LDAP libraries"* | 1 | error |
| TLS conflict | `--without-ssl --with-openssl` (Linux) | *"--without-ssl has been set together with an explicit option to use an ssl library"* | 1 | error |
| E1 no TLS | `--without-ssl` (Linux) | No https, ftps, gophers, imaps, pop3s, smtps, smbs, wss; no smb | 0 | effect |
| E2 no HTTP | `--disable-http` (Linux) | No http(s), rtsp, ipfs, ipns, ws, wss | 0 | effect |
| E3 no FTP | `--disable-ftp` + `runtests.pl 100` (macOS) | ftp and ftps gone; test 100 *"SKIPPED: curl lacks ftp server support"* | 0 | effect |

## Findings worth noting

These are exactly the kind of hidden behaviour our project targets. Each one would mislead
a tester, or an AI, that relies on configure's messages instead of its actual result.

1. **Silent constraints are common.** 5 of the 6 constraints are silent in at least
   one situation (C1, C3, C4, C5, and C6 when form-api is left at its default). Only
   C2 always stops the build. The build
   succeeds but does not contain what was requested.
2. **configure sometimes reports the opposite of what it does.**
   - With `--disable-http --enable-hsts`, configure prints *"HSTS... yes"* and then
     disables HSTS anyway. The same happens for alt-svc.
   - For MQTT, configure prints *"checking whether to support mqtt... no"* by default,
     but MQTT is built in and listed by `curl --version`.
3. **The same constraint can fail loudly or silently.** form-api without mime stops
   configure only if form-api was requested explicitly. Left at its default, form-api is
   quietly dropped.
4. **Defaults depend on the machine.** The same command produced a curl with LDAP on
   macOS and without LDAP on Linux, and a curl with brotli on Linux but not on macOS.
   This is why some defaults are `auto` in the model.
5. **Configuration decides which tests run.** Disabling a protocol removes it from the
   build, and the test runner skips every test that needs it. This links the model
   directly to the coverage measurements in D6.
