import hashlib
import io
import json
import tarfile
import unittest
from update_formula import verify,render,url_for,TARGET

VERSION='0.1.0-alpha.1'
class Tests(unittest.TestCase):
    def bundle(self,version=VERSION,extra=None):
        contents={name:b'fixture' for name in ('bin/runloom','bin/runloom-node','LICENSE','THIRD_PARTY_NOTICES.md','RELEASE.md','install.py')}
        metadata={'version':version,'target':TARGET,'source_commit':'a'*40,'sha256':{k:hashlib.sha256(v).hexdigest() for k,v in contents.items()}}
        contents['BUILD.json']=json.dumps(metadata).encode()
        if extra:contents[extra]=b'unsafe'
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode='w:gz') as archive:
            for name,data in contents.items():
                info=tarfile.TarInfo(f'runloom-{VERSION}-{TARGET}/'+name);info.size=len(data)
                archive.addfile(info,io.BytesIO(data))
        data=stream.getvalue();checksum=hashlib.sha256(data).hexdigest()+f'  runloom-{VERSION}-{TARGET}.tar.gz\n'
        return data,checksum
    def test_correct_release_and_no_service_hooks(self):
        data,checksum=self.bundle();digest,meta=verify(data,checksum,VERSION)
        formula=render(VERSION,digest)
        self.assertIn('UranusLin/runloom/releases/download/v'+VERSION,formula)
        self.assertNotIn('service do',formula);self.assertNotIn('def post_install',formula)
        self.assertEqual(meta['source_commit'],'a'*40)
    def test_checksum_corruption(self):
        data,checksum=self.bundle()
        with self.assertRaises(ValueError):verify(data+b'corrupt',checksum,VERSION)
    def test_wrong_embedded_version(self):
        data,checksum=self.bundle(version='9.0.0')
        with self.assertRaises(ValueError):verify(data,checksum,VERSION)
    def test_traversal_and_extra_payload(self):
        for path in ('../escape','unexpected'):
            with self.subTest(path=path):
                data,checksum=self.bundle(extra=path)
                with self.assertRaises(ValueError):verify(data,checksum,VERSION)
    def test_version_url_injection(self):
        for value in ('../private','0.1.0"','v0.1.0','0.1.0;echo bad'):
            with self.assertRaises(ValueError):url_for(value)
    def test_checksum_wrong_filename(self):
        data,checksum=self.bundle()
        with self.assertRaises(ValueError):verify(data,checksum.replace('.tar.gz','.zip'),VERSION)
if __name__=='__main__':unittest.main()
