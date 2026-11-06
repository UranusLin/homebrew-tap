"""Pin the actual published Runloom binary; local archives produce unverified drafts."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OWNER = 'UranusLin'
TARGET = 'aarch64-apple-darwin'
MAX_BYTES = 64 * 1024 * 1024

def version_check(version):
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?', version):
        raise ValueError('expected canonical release version without v prefix')

def url_for(version):
    version_check(version)
    return f'https://github.com/{OWNER}/runloom/releases/download/v{version}/runloom-{version}-{TARGET}.tar.gz'

def download(url, limit):
    request = urllib.request.Request(url, headers={'User-Agent':'Runloom-Tap-Updater/1'})
    with urllib.request.urlopen(request, timeout=60) as response:
        if not response.geturl().startswith('https://'):
            raise ValueError('refusing non-HTTPS redirect')
        data = response.read(limit+1)
    if len(data)>limit: raise ValueError('release download too large')
    return data

def verify(data, checksum, version):
    version_check(version)
    name=f'runloom-{version}-{TARGET}.tar.gz'
    match=re.fullmatch(r'([a-f0-9]{64})  '+re.escape(name)+r'\n?',checksum)
    digest=hashlib.sha256(data).hexdigest()
    if not match or match.group(1)!=digest:raise ValueError('release checksum mismatch')
    base=name[:-7]
    expected={'bin/runloom','bin/runloom-node','LICENSE','THIRD_PARTY_NOTICES.md','RELEASE.md','install.py','BUILD.json'}
    contents={}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r|gz') as archive:
        total=0
        for count,member in enumerate(archive,1):
            total+=member.size
            if count>20 or total>MAX_BYTES:raise ValueError('oversized bundle')
            path=PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or path.parts[0]!=base or not (member.isfile() or member.isdir()):
                raise ValueError('unsafe bundle member')
            if member.isdir():continue
            relative=str(path.relative_to(base))
            if relative not in expected or relative in contents:raise ValueError('unexpected bundle member')
            contents[relative]=archive.extractfile(member).read()
    if set(contents)!=expected:raise ValueError('incomplete bundle')
    metadata=json.loads(contents['BUILD.json'])
    if metadata['version']!=version or metadata['target']!=TARGET or not re.fullmatch('[a-f0-9]{40}',metadata['source_commit']):
        raise ValueError('build identity mismatch')
    if set(metadata['sha256'])!=expected-{'BUILD.json'}:raise ValueError('invalid build hash manifest')
    for name,wanted in metadata['sha256'].items():
        if hashlib.sha256(contents[name]).hexdigest()!=wanted:raise ValueError('bundle file checksum mismatch')
    return digest,metadata

def render(version, digest):
    return '''class Runloom < Formula
  desc "AI work continuity with scoped sessions, checkpoints, and execution control"
  homepage "https://github.com/UranusLin/runloom"
  url "URL"
  version "VERSION"
  sha256 "DIGEST"
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
'''.replace('URL',url_for(version)).replace('VERSION',version).replace('DIGEST',digest)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version',required=True)
    p.add_argument('--archive',type=Path,help='local draft only; cannot claim remote asset validation')
    p.add_argument('--check',action='store_true',help='verify published asset against committed pin without editing')
    a=p.parse_args();url=url_for(a.version)
    if a.check and a.archive:p.error('--check requires the published asset')
    if a.archive:
        if a.archive.stat().st_size>MAX_BYTES:raise ValueError('archive too large')
        data=a.archive.read_bytes();checksum=Path(str(a.archive)+'.sha256').read_text()
    else:
        checksum=download(url+'.sha256',2048).decode('ascii');data=download(url,MAX_BYTES)
    digest,metadata=verify(data,checksum,a.version)
    formula=render(a.version,digest)
    record={'version':a.version,'url':url,'sha256':digest,'source_commit':metadata['source_commit'],
            'target':TARGET,'remote_verified':a.archive is None}
    if a.check:
        if (ROOT/'Formula/runloom.rb').read_text()!=formula or json.loads((ROOT/'release.json').read_text())!=record:
            raise ValueError('published asset differs from committed formula/metadata; update pin before publishing tap')
    else:
        (ROOT/'Formula/runloom.rb').write_text(formula)
        (ROOT/'release.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))

if __name__=='__main__':main()
