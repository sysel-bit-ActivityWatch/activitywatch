#!/usr/bin/env python3
"""Export an allowlisted, reproducible multiuser patch set without local data."""
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATCHES = [
    ('.', '01-package-rebuild', ['Makefile']),
    ('aw-server', '02-server-connections', ['aw_server/server.py', 'tests/test_database_connections.py']),
    ('awatcher', '03-watcher-retry', ['watchers/src/watchers.rs']),
    ('awatcher', '04-watcher-username', ['watchers/src/report_client.rs']),
    ('aw-watcher-afk', '05-afk-username', ['aw_watcher_afk/afk.py']),
    ('aw-watcher-window', '06-window-username', ['aw_watcher_window/main.py']),
    ('aw-watcher-input', '07-input-username', ['src/aw_watcher_input/main.py']),
    ('aw-server/aw-webui', '08-user-selector', [
        'src/util/bucketUser.ts', 'src/stores/activity.ts', 'src/stores/buckets.ts',
        'src/views/activity/Activity.vue', 'test/unit/store/buckets.test.node.ts',
        'test/unit/store/activityMultidevice.test.node.ts']),
    ('.', '09-multiuser-deployment', [
        'scripts/multiuser/' + name for name in (
            'activitywatch-server.service', 'activitywatch-session.desktop',
            'start-session-watcher', 'install.sh', 'README.md', 'CONTRIBUTING.md',
            'export_sources.py')]),
]
APPLY = '''#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description="Validate/apply the multiuser patch set")
parser.add_argument('checkout', type=Path)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
base = Path(__file__).resolve().parent
manifest = json.loads((base / 'manifest.json').read_text())
# Validate ALL repositories and patches before changing any checkout.
for repo, entry in manifest['repositories'].items():
    cwd = args.checkout / repo
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=cwd, text=True).strip()
    if actual != entry['revision']:
        raise SystemExit(f"Revision mismatch for {repo}: expected {entry['revision']}, got {actual}")
    paths = [str(base / path) for path in entry['patches']]
    subprocess.run(['git', 'apply', '--check', *paths], cwd=cwd, check=True)
if not args.check:
    for repo, entry in manifest['repositories'].items():
        paths = [str(base / path) for path in entry['patches']]
        subprocess.run(['git', 'apply', *paths], cwd=args.checkout / repo, check=True)
print('All patches validated.' if args.check else 'All patches applied; no commits created.')
'''


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(ROOT / repo), *args])


def main():
    manifest = {'format': 1, 'repositories': {}}
    output = ROOT / 'dist/activitywatch-multiuser-sources.zip'
    output.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temp, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for repo, label, paths in PATCHES:
            entry = manifest['repositories'].setdefault(repo, {
                'revision': git(repo, 'rev-parse', 'HEAD').decode().strip(),
                'upstream': git(repo, 'remote', 'get-url', 'origin').decode().strip(),
                'patches': [],
            })
            chunks = []
            for name in paths:
                data = (ROOT / repo / name).read_bytes()
                archive.writestr('sources/' + (repo + '/' if repo != '.' else '') + name, data)
                tracked = subprocess.run(['git', '-C', str(ROOT / repo), 'ls-files', '--error-unmatch', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
                if tracked:
                    chunks.append(git(repo, 'diff', '--binary', 'HEAD', '--', name))
                else:
                    # Make a proper new-file git patch, retaining executable mode.
                    scratch = Path(temp) / label
                    scratch.mkdir(exist_ok=True)
                    subprocess.run(['git', 'init', '-q', str(scratch)], check=True)
                    dest = scratch / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
                    dest.chmod((ROOT / repo / name).stat().st_mode & 0o777)
                    subprocess.run(['git', 'add', '--', name], cwd=scratch, check=True)
                    chunks.append(subprocess.check_output(['git', 'diff', '--cached', '--binary', '--', name], cwd=scratch))
            patch = 'patches/' + label + '.patch'
            archive.writestr(patch, b''.join(chunks))
            entry['patches'].append(patch)
        archive.writestr('manifest.json', json.dumps(manifest, indent=2) + '\n')
        archive.writestr('apply.py', APPLY)
        archive.writestr('README.md', (ROOT / 'scripts/multiuser/CONTRIBUTING.md').read_bytes())
    print(output)


if __name__ == '__main__':
    main()
