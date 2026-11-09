# How We Checked the curl Model (D4)

Writing a rule into the model is not enough. We also wanted proof that curl really behaves
that way. So for every rule and side effect in [curl.yaml](curl.yaml), we ran curl's
`configure` with a combination that breaks it. Then we looked at two things:

- the **exit code**: did `configure` stop (exit 1) or carry on (exit 0)?
- the **summary** at the end: what was really built?

All checks were done on `curl-8_17_0`, on two machines:

| Machine | Details |
|---|---|
| Linux | Ubuntu 24.04.5, gcc 13.3, OpenSSL 3.0.13, no LDAP libraries installed |
| macOS | Apple Silicon, Homebrew OpenSSL 3.5.9, LDAP libraries that come with macOS |

You can repeat all checks yourself with one command (from the repository root):

```sh
bash scripts/verify_curl_constraints.sh
```

On Linux, all 13 checks passed ([latest results](../results/verification/summary.md)).

## Results

The "Behaviour" column shows how `configure` reacts when the rule is broken:

- **error** means it stops.
- **silent** means it finishes but leaves something out.
- **effect** means a side effect on parts of curl outside our model.

| Rule | What we asked for | What `configure` did | Exit | Behaviour |
|---|---|---|---|---|
| C1: LDAPS needs LDAP | `--disable-ldap --enable-ldaps` (macOS) | Printed *"LDAP needs to be enabled to support LDAPS"*. Summary: `LDAPS: no` | 0 | silent |
| C2: a TLS choice is required | no TLS option (Linux) | *"select TLS backend(s) or disable TLS with --without-ssl."* | 1 | error |
| C3: HSTS needs TLS | `--without-ssl --enable-hsts` (Linux) | Printed *"disables HSTS due to lack of SSL"*. Summary: `HSTS: no` | 0 | silent |
| C4: HSTS needs HTTP | `--disable-http --enable-hsts` (Linux) | Printed `checking whether to support HSTS... yes`, yet the summary says `HSTS: no` | 0 | silent and misleading |
| C5: alt-svc needs HTTP | `--disable-http --enable-alt-svc` (Linux) | Printed `checking whether to support alt-svc... yes`, yet the summary says `Alt-svc: no` | 0 | silent and misleading |
| C6: form API needs MIME | `--disable-mime --enable-form-api` (Linux) | *"MIME support needs to be enabled in order to enable form API support"* | 1 | error |
| C6, form API left at default | `--disable-mime` (Linux) | `checking whether to support the form API... no` | 0 | silent |
| LDAP libraries missing | `--enable-ldap` without LDAP libraries (Linux) | *"couldn't detect the LDAP libraries"* | 1 | error |
| "No TLS" and "OpenSSL" together | `--without-ssl --with-openssl` (Linux) | *"--without-ssl has been set together with an explicit option to use an ssl library"* | 1 | error |
| E1: no TLS | `--without-ssl` (Linux) | No https, ftps, gophers, imaps, pop3s, smtps, smbs or wss. smb is also gone | 0 | effect |
| E2: no HTTP | `--disable-http` (Linux) | No http, https, rtsp, ipfs, ipns, ws or wss | 0 | effect |
| E3: no FTP | `--disable-ftp`, then `runtests.pl 100` (macOS) | ftp and ftps gone. Test 100: *"SKIPPED: curl lacks ftp server support"* | 0 | effect |

## What we learned

These are exactly the hidden behaviours our project is looking for. Each of them would
fool a tester, or an AI, who trusts `configure`'s messages instead of checking what was
really built.

### Silent rules are common

5 of the 6 rules can be broken without the build failing: C1, C3, C4, C5, and C6 when
the form API is left at its default. Only C2 always stops the build. In every silent
case, the build succeeds but does not contain what was asked for.

### configure sometimes says the opposite of what it does

With `--disable-http --enable-hsts`, `configure` prints *"HSTS... yes"* and then leaves
HSTS out anyway. The same happens with alt-svc. For MQTT it is the other way round: by
default `configure` prints *"checking whether to support mqtt... no"*, but MQTT is built
and appears in `curl --version`.

### The same rule can be loud or silent

Turning MIME off while explicitly asking for the form API stops `configure` with an
error. Turning MIME off and not mentioning the form API drops the form API without a
word. Whether you get an error depends on how you asked.

### Defaults depend on the machine

The same options produced a curl *with* LDAP on macOS and *without* LDAP on Linux. With
brotli it was the other way round. That is why some defaults are written as `auto` in the
model.

### Configuration decides which tests run

Turning a protocol off removes it from the build, and curl's test runner then skips every
test that needs it. This connects the model directly to the coverage measurements in D6.
