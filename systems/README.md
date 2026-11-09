# systems/

This is where the program we study, curl, lives on your own computer. We do **not**
upload curl's code to our repository (the `.gitignore` file blocks it). Each of us
downloads the same fixed version, `curl-8_17_0`, so we all work on identical code.

## Download and build curl

Run these commands from the repository root.

On **Linux**:

```sh
git clone --depth 1 --branch curl-8_17_0 https://github.com/curl/curl.git systems/curl
cd systems/curl
autoreconf -fi                                 # prepare the build files
./configure --with-openssl --without-libpsl    # choose the options
make -j"$(nproc)"                              # compile
make -C tests                                  # build the test tools
cd tests && perl runtests.pl 1 to 100          # run tests 1 to 100
```

On **macOS** (Homebrew), use OpenSSL 3. The default `openssl` package is version 4,
which does not work with this version of curl:

```sh
brew install autoconf automake libtool pkg-config openssl@3
git clone --depth 1 --branch curl-8_17_0 https://github.com/curl/curl.git systems/curl
cd systems/curl
autoreconf -fi
export PKG_CONFIG_PATH="$(brew --prefix openssl@3)/lib/pkgconfig"
./configure --with-openssl=$(brew --prefix openssl@3) --without-libpsl
make -j4
make -C tests
cd tests && perl runtests.pl 1 to 100
```

On **Windows**, use WSL and follow the Linux steps.

If everything worked, `./src/curl --version` (run inside `systems/curl`) prints curl's
version and the protocols it supports.

More background:

- why curl and why this version: [docs/selection.md](../docs/selection.md)
- build times and tips: [docs/candidates.md](../docs/candidates.md#build-check-curl)
