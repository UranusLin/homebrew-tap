"""Exercise real Homebrew against a local release, without linking or changing services."""
import argparse,json,os
from pathlib import Path
import shutil,subprocess,tempfile,uuid
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[1];archive=a.archive.resolve()
if subprocess.run(['brew','list','--versions','runloom'],capture_output=True,text=True).stdout.strip():
    raise SystemExit('Runloom already installed by brew; refusing to alter it')
with tempfile.TemporaryDirectory(prefix='runloom-tap-test-') as tmp:
    temp=Path(tmp);checkout=temp/'tap';(checkout/'Formula').mkdir(parents=True)
    record=json.loads((root/'release.json').read_text())
    source=(root/'Formula/runloom.rb').read_text()
    (checkout/'Formula/runloom.rb').write_text(source.replace(record['url'],archive.as_uri()))
    for command in (['git','init','-b','main'],['git','add','.'],['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','local release fixture']):
        subprocess.run(command,cwd=checkout,check=True,capture_output=True)
    tap='runloom-validation/fixture-'+uuid.uuid4().hex[:10];formula=tap+'/runloom'
    env={**os.environ,'HOMEBREW_NO_AUTO_UPDATE':'1','HOMEBREW_NO_INSTALL_CLEANUP':'1','HOMEBREW_NO_ANALYTICS':'1','HOMEBREW_NO_AUTOREMOVE':'1','XDG_CONFIG_HOME':str(temp/'config')}
    def brew(*args,check=True):
        print('brew '+' '.join(args),flush=True)
        return subprocess.run(['brew',*args],env=env,check=check,timeout=180)
    tapped=False
    try:
        brew('tap',tap,str(checkout));tapped=True
        commands=subprocess.check_output(['brew','commands'],text=True,env=env)
        if 'trust' in commands.split():brew('trust','--formula',formula)
        brew('install','--build-from-source','--skip-link',formula)
        brew('test','--force',formula)
        print(json.dumps({'pass':True,'real_homebrew_install':True,'brew_test':True,'remote_download':False,'services_changed':False}),flush=True)
    finally:
        if tapped:
            installed=subprocess.run(['brew','list','--versions','runloom'],capture_output=True,text=True,env=env)
            if installed.stdout.strip():brew('uninstall','--formula',formula)
            brew('untap',tap)
