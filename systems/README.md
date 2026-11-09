# systems/

Source code of the system under study. The source itself is **not committed** (see
`.gitignore`); each teammate clones it locally at the pinned version so everyone works on
exactly the same code.

## curl (selected system)

```sh
# from the repository root
git clone --depth 1 --branch curl-8_17_0 https://github.com/curl/curl.git systems/curl
cd systems/curl
autoreconf -fi
./configure --with-openssl --without-libpsl
make -j"$(nproc)"
make -C tests
cd tests && perl runtests.pl 1 to 100
```

Why curl and why this version: [docs/selection.md](../docs/selection.md).
Build notes and timings: [docs/candidates.md](../docs/candidates.md#build-check-curl).
