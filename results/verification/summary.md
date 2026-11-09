# Constraint verification

- Date: 2026-11-09 12:18
- Machine: Linux x86_64
- curl: curl-8_17_0

| Check | configure options | Expected | Observed exit | Result |
|---|---|---|---|---|
| C1 | `--with-openssl --disable-ldap --enable-ldaps` | ldaps without ldap: continues, LDAPS silently off | 0 | PASS |
| C2 | `(none)` | no TLS choice: stops with an error | 1 | PASS |
| C3 | `--without-ssl --enable-hsts` | hsts without TLS: continues, HSTS silently off | 0 | PASS |
| C4 | `--with-openssl --disable-http --enable-hsts` | hsts without http: continues, HSTS silently off | 0 | PASS |
| C5 | `--with-openssl --disable-http --enable-alt-svc` | alt-svc without http: continues, alt-svc silently off | 0 | PASS |
| C6 | `--with-openssl --disable-mime --enable-form-api` | form-api requested without mime: stops with an error | 1 | PASS |
| C6-default | `--with-openssl --disable-mime` | mime off, form-api default: continues, form-api silently off | 0 | PASS |
| TLS-conflict | `--without-ssl --with-openssl` | --without-ssl with --with-openssl: stops with an error | 1 | PASS |
| E1 | `--without-ssl` | no TLS: https not built | 0 | PASS |
| E2 | `--with-openssl --disable-http` | no HTTP: rtsp not built | 0 | PASS |
| E3 | `--with-openssl --disable-ftp` | no FTP: ftp not built | 0 | PASS |
| MQTT-msg | `--with-openssl` | default build: configure prints 'mqtt... no' | 0 | PASS |
| MQTT-built | `--with-openssl` | default build: mqtt is built anyway | 0 | PASS |

**Passed: 13, failed: 0**
