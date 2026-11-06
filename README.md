# Runloom Homebrew Tap

Homebrew distribution for [Runloom](https://github.com/UranusLin/runloom), an MIT
AI work continuity core. Apple Silicon macOS 14+ binary preview; no GUI or bundled
Claude/Codex credentials. Installation does not register or restart a service.

**Preparation status:** the initial pin was generated from a locally validated
alpha archive. Runloom's public Release must exist and the formula must be refreshed
from that actual asset before this tap is advertised as installable. See
`release.json`: `remote_verified` must be `true`. Local and CI builds may have
different checksums even at the same source commit. Do not copy a local checksum
onto a separately built GitHub artifact.

## Install (after publication)

```sh
brew install UranusLin/tap/runloom
runloom --version
runloom-node --version
```

Recent Homebrew versions may ask for explicit third-party formula trust. Review
`Formula/runloom.rb` before granting it; trust the formula rather than every future
item in the tap. No `brew services` configuration is provided in this preview.
See Runloom's release guide for foreground startup and state compatibility.

## Upgrade carefully

Use `brew pin runloom` while a node/worker uses its installed binaries. A service
must use a fixed version path rather than the moving `opt` symlink. Before an
upgrade, stop admission, finish/inspect workers and back up the full state. Then
unpin, upgrade with automatic cleanup disabled, verify the new binary and migrate
under your own service-management procedure. Homebrew does not provide Runloom
schema rollback. Do not remove an old keg while any process still depends on it.
`brew uninstall runloom` removes the package, not your separately stored node data.

## Repository and publishing order

Create **empty** GitHub repositories under **UranusLin**:

1. `runloom`: upload the clean `runloom-public` checkout, not the private source repo.
2. `homebrew-tap`: upload this independent checkout after the release pin is verified.

Do not initialize either remote with a README/license/gitignore; these already
exist locally. Ensure your GitHub credentials can write to UranusLin, rather than
assuming the active company account has permission.

After uploading Runloom and passing hosted CI, create/push `v0.1.0-alpha.1`.
The Runloom workflow creates a draft prerelease. Inspect it, then publish the
prerelease so the binary archive and matching checksum are publicly downloadable.
From this tap checkout run:

```sh
python3 scripts/update_formula.py --version 0.1.0-alpha.1
python3 scripts/update_formula.py --version 0.1.0-alpha.1 --check
git diff -- Formula/runloom.rb release.json
git add Formula/runloom.rb release.json
git commit -m "Pin published Runloom alpha release"
```

Then upload this repo as `UranusLin/homebrew-tap`; its CI checks the live artifact
before installing and testing it. A draft Release or an unverified local pin will
not pass this gate. This is a third-party tap, not a homebrew/core submission.
No remote repository or release is created by these scripts.

## Local validation

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
```

`update_formula.py --archive PATH --version VERSION` validates a local bundle and
creates a **draft** pin. Never publish that pin without the remote refresh above.
The updater checks the archive checksum, allowed members, per-file hashes, target,
version and source commit format. Checksums do not replace publisher signatures.

## Validation recorded locally

Six updater verification tests pass. Homebrew formula style and GitHub workflow
syntax checks pass. The exact local alpha archive was installed with real
Homebrew in a temporary tap, without linking it into PATH; `brew test --force`
passed both binary version checks and metadata init/list. The temporary package
and tap were removed. This does not verify downloading the future GitHub Release
or hosted CI.

Repeat with `python3 scripts/smoke_local.py /path/to/release.tar.gz`. It refuses to
run if Runloom is already installed by brew, keeps trust in temporary config,
disables automatic update/cleanup/autoremove, and does not configure services.
Homebrew may populate its shared caches and Ruby tooling during testing.
