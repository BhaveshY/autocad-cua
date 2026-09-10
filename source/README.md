# Cua observation patch

Upstream: https://github.com/trycua/cua at tag `cua-driver-rs-v0.25.0`, commit `45d78fe` (resolve the tag before building). `autocad-observation.patch` modifies Windows observation only: bounded UIA traversal, exact HWND lookup, and discovery of visible untitled owned palettes/native menus. Upstream input delivery code is unchanged.

Apply the patch in that checkout and build from `libs/cua-driver/rust` with the Windows MSVC Rust toolchain:

```text
git apply PATH_TO/autocad-observation.patch
cargo build -p cua-driver --release --locked
```

The redistributed executable is identified by SHA-256 in `../runtime.json`. A rebuild is a new candidate: validate its hash, target identity, background behavior and drawing results before adopting it. Do not silently replace the pinned binary.

Cua is MIT licensed; its notice is in `../licenses/CUA-MIT.txt`. Dependency notices are supplied in `../licenses/dependencies/` where available from the build's resolved source packages.
