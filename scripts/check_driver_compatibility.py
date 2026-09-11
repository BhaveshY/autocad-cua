"""Check a trusted candidate's metadata without starting MCP or sending app input."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from runtime import ROOT, driver_path

ANNOTATIONS = {'description', 'title', 'examples', '$comment'}


def clean(value):
    if isinstance(value, dict):
        return {k: ({name: clean(schema) for name, schema in v.items()}
                    if k in {'properties', 'patternProperties', '$defs', 'definitions'}
                    else v if k in {'default', 'const', 'enum'} else clean(v))
                for k, v in value.items() if k not in ANNOTATIONS}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


def differences(before, after, path='schema'):
    """Allow optional additions, fewer required fields and wider enums; flag other changes."""
    before, after = clean(before), clean(after)
    if not isinstance(before, dict) or not isinstance(after, dict):
        return [] if before == after else [path + ': changed constraint']
    errors = []
    for key in sorted(set(before) | set(after)):
        old, new = before.get(key), after.get(key)
        here = path + '.' + key
        if key == 'properties':
            if not isinstance(old or {}, dict) or not isinstance(new or {}, dict):
                errors.append(here + ': invalid properties')
                continue
            for name, schema in (old or {}).items():
                if name not in (new or {}):
                    errors.append(here + '.' + name + ': removed parameter')
                else:
                    errors.extend(differences(schema, new[name], here + '.' + name))
        elif key == 'required':
            added = set(new or []) - set(old or [])
            if added:
                errors.append(here + ': new required fields ' + ', '.join(sorted(added)))
        elif key == 'enum':
            if new is not None and (old is None or any(v not in new for v in old)):
                errors.append(here + ': narrowed accepted values')
        elif old != new:
            errors.append(here + ': changed constraint/default')
    return errors


def read_cli(driver, *args):
    result = subprocess.run([str(driver), *args], capture_output=True, text=True,
                            encoding='utf-8', timeout=10, check=True)
    return result.stdout


def inspect_candidate(driver, baseline, expected_sha256=None):
    digest = hashlib.sha256(driver.read_bytes()).hexdigest()
    if expected_sha256 and digest != expected_sha256.lower():
        raise ValueError('Candidate checksum differs; executable was not run.')
    manifest = json.loads(read_cli(driver, 'manifest'))
    help_text = read_cli(driver, '--help')
    errors = []
    commands = {c['name']: c for c in manifest['subcommands']}
    if 'mcp' not in commands:
        errors.append('Missing mcp command')
    else:
        flags = {a['name'] for a in commands['mcp'].get('args', [])}
        if '--direct' not in flags:
            errors.append('Missing --direct launch flag')
    if not re.search(r'(?<![\w-])--no-overlay(?![\w-])', help_text):
        errors.append('Missing --no-overlay launch flag')
    for name, schema in baseline['tools'].items():
        try:
            text = read_cli(driver, 'describe', name)
            actual = json.loads(text.split('input_schema:', 1)[1].strip())
            errors.extend(differences(schema, actual, name))
        except (subprocess.SubprocessError, ValueError, IndexError) as error:
            errors.append(name + ': metadata unavailable (' + type(error).__name__ + ')')
    return {'candidate_version': manifest.get('binary_version'), 'sha256': digest,
            'input_contract_matches': not errors, 'differences': errors,
            'live_app_behavior_verified': False, 'installed_driver_changed': False,
            'next': 'Run a disposable app check before adopting this candidate.' if not errors
                    else 'Review the listed changes; keep the currently pinned driver.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver', nargs='?', help='Trusted candidate EXE; defaults to the verified bundled driver.')
    parser.add_argument('--sha256', help='Expected candidate checksum, checked before execution.')
    args = parser.parse_args()
    try:
        driver = Path(args.driver).resolve() if args.driver else Path(driver_path())
        baseline = json.loads((ROOT / 'source/driver-contract.json').read_text(encoding='utf-8'))
        report = inspect_candidate(driver, baseline, args.sha256)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as error:
        report = {'input_contract_matches': False, 'error': str(error),
                  'live_app_behavior_verified': False, 'installed_driver_changed': False}
    print(json.dumps(report, indent=2))
    return 0 if report['input_contract_matches'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
