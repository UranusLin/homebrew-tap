class Runloom < Formula
  desc "AI work continuity with scoped sessions, checkpoints, and execution control"
  homepage "https://github.com/UranusLin/runloom"
  url "https://github.com/UranusLin/runloom/releases/download/v0.1.0-alpha.1/runloom-0.1.0-alpha.1-aarch64-apple-darwin.tar.gz"
  version "0.1.0-alpha.1"
  sha256 "73685164c986eea020678815f82e5e64e6a448b77bca74f496d5951ba298e6b5"
  license "MIT"

  depends_on arch: :arm64
  depends_on macos: :sonoma

  def install
    bin.install "bin/runloom", "bin/runloom-node"
    pkgshare.install "BUILD.json"
    doc.install "RELEASE.md", "THIRD_PARTY_NOTICES.md"
  end

  def caveats
    <<~EOS
      Developer preview. No service is installed or restarted automatically.
      Runloom manages existing work: stop admission and back up state before
      switching a running node to a new binary. Do not use brew services restart.
      Keep active daemons on a fixed version path and pin this formula while
      they run. Homebrew upgrades/cleanup are not Runloom state migrations.
      Build identity: #{pkgshare}/BUILD.json
    EOS
  end

  test do
    assert_equal "runloom #{version}", shell_output("#{bin}/runloom --version").strip
    assert_equal "runloom-node #{version}", shell_output("#{bin}/runloom-node --version").strip
    db = testpath/"metadata.db"
    system bin/"runloom", "--db", db, "init"
    assert_equal [], JSON.parse(shell_output("#{bin}/runloom --db #{db} list --workspace fixture"))
  end
end
