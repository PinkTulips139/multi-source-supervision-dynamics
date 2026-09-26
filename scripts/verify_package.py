"""Read-only public-package verification; never imports research implementations."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

STUDY = Path('studies/mlbd2026_wrong_label_organization')
SEEDS = [167174636, 1852328752, 1231418446, 1461753708]
ENDPOINTS = ('Secondary', 'LocalNLL', 'Primary', 'Complement')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def check_hashes(root):
    manifest = read_json(root / STUDY / 'manifests/evidence_manifest.json')
    seen = set()
    for item in manifest['files']:
        relative = item['destination']
        require(relative not in seen, 'Duplicate manifest path: ' + relative)
        seen.add(relative)
        path = (root / relative).resolve()
        require(path.is_relative_to(root.resolve()), 'Manifest path escapes repository')
        require(path.is_file() and not (root / relative).is_symlink(), 'Missing or linked artifact: ' + relative)
        payload = path.read_bytes()
        require(len(payload) == item['packaged_bytes'], 'Size mismatch: ' + relative)
        require(hashlib.sha256(payload).hexdigest() == item['packaged_sha256'], 'Hash mismatch: ' + relative)
        if item['transformation'] == 'byte-identical':
            require(item['packaged_sha256'] == item['source_sha256'], 'Source hash mismatch: ' + relative)
    return len(seen)


def heading_ids(text):
    ids = set()
    for line in text.splitlines():
        if re.match(r'^#{1,6} ', line):
            heading = re.sub(r'^#+\s+', '', line).strip().lower()
            heading = re.sub(r'[^\w\-\s]', '', heading).replace(' ', '-')
            ids.add(heading)
    return ids


def check_links(root):
    count = 0
    for path in root.rglob('*.md'):
        text = path.read_text(encoding='utf-8-sig')
        # Inline links/images used by this package. Code fences are not links.
        text = re.sub(r'```.*?```', '', text, flags=re.S)
        for match in re.finditer(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)', text):
            target = match.group(1).strip('<>')
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith('//'):
                continue
            linked = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
            require(linked.is_relative_to(root.resolve()), 'Link escapes repository: ' + path.name)
            require(linked.exists(), f'Broken link in {path.relative_to(root)}: {target}')
            if parsed.fragment and linked.suffix.lower() == '.md':
                require(unquote(parsed.fragment) in heading_ids(linked.read_text(encoding='utf-8-sig')),
                        f'Broken anchor in {path.relative_to(root)}: {target}')
            count += 1
    return count


def check_results(root):
    base = root / STUDY
    require(read_json(base / 'configs/SEED_ORDER.json')['seeds'] == SEEDS, 'Seed order differs')
    require(read_json(base / 'configs/CLINC_CONTRACT.json')['FINAL_CONFIRMATORY_SEEDS'] == SEEDS, 'CLINC seeds differ')
    require(read_json(base / 'configs/BANK_PACKAGE.json')['student']['seeds'] == SEEDS, 'BANK seeds differ')
    main = read_csv(base / 'results/TABLE_1_DATA.csv')
    source = read_csv(base / 'evidence/MAIN_MATRIX.csv')
    matrix = {(r['dataset'], r['learner'], r['endpoint']): r for r in source}
    expected = {(d, m, c) for d in ('CLINC150', 'BANKING77') for m in ('RoBERTa', 'XLNet') for c in ('R1', 'R2')}
    require(len(main) == 8 and {(r['dataset'], r['learner'], r['comparator']) for r in main} == expected, 'Main coverage')
    for row in main:
        require(row['n_training_seeds'] == '4', 'Main seed count')
        for endpoint in ENDPOINTS:
            original = matrix[(row['dataset'], row['learner'], endpoint)]
            for field in ('mean', 'signs'):
                require(row[endpoint + '_' + field] == original[row['comparator'] + '_' + field], 'Main display/source mismatch')
    seed_rows = read_csv(base / 'evidence/MAIN_SEEDS.csv')
    require(len(seed_rows) == 32, 'Main paired seed rows')
    for dataset, learner, comparator in expected:
        rows = [r for r in seed_rows if (r['dataset'], r['learner'], r['comparator']) == (dataset, learner, comparator)]
        require([int(r['seed']) for r in rows] == SEEDS, 'Main per-setting seed order')
    control = read_csv(base / 'results/CONTROL_TABLE_DATA.csv')
    require(len(control) == 4, 'Control setting count')
    require(sum(r['directional_status'] == 'BOTH_ENDPOINTS_FOUR_POSITIVE' for r in control) == 3, 'Control boundary')
    cx = next(r for r in control if (r['dataset'], r['learner']) == ('CLINC150', 'XLNet'))
    require(cx['directional_status'] == 'NON_UNANIMOUS', 'CLINC XLNet control counterexample missing')
    path_rows = read_csv(base / 'results/M3_RESULT_TABLE_DATA.csv')
    originals = read_csv(base / 'evidence/M3_TABLE.csv')
    require(len(path_rows) == len(originals) == 8, 'Path endpoint rows')
    for row, original in zip(path_rows, originals):
        require(all(row[key] == value for key, value in original.items()), 'Path display/source mismatch')
    cells = read_json(base / 'evidence/M3_MATRIX.json')['cells']
    allowed = read_json(base / 'configs/path_runtime/SIXTEEN_FIT_ALLOWLIST.json')['cells']
    expected_cells = [(s, p, c) for s in SEEDS for p in ('PI0', 'PI1') for c in ('REAL', 'CONTROL')]
    for collection in (cells, allowed):
        require([(r['seed'], r['order_id'], r['condition']) for r in collection] == expected_cells, 'Path cell identity/order')
        require(all(r['epochs'] == 20 and r['optimizer_steps'] == 1880 for r in collection), 'Path recipe')
    require(all(r['status'] == 'PASS' for r in cells), 'Path completion')
    status = read_json(base / 'evidence/PATH_EXECUTION_STATUS.json')
    require(status['fresh_fits'] == status['validated_fits'] == 16, 'Path fresh-fit count')
    summaries = read_csv(base / 'results/M3_SUMMARY_DATA.csv')
    signs = {r['endpoint']: r['I'] for r in summaries if r['statistic'] == 'sign_pattern'}
    require(signs == {'LocalNLL': '++++', 'Secondary': '+-++'}, 'Path sign boundaries')
    return {'main_comparisons': 8, 'main_paired_rows': 32, 'control_settings': 4, 'fresh_path_cells': 16}


def check_files(root):
    count = 0
    largest = ('', 0)
    patterns = {
        'token': r'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|hf_[A-Za-z0-9]{25,}|sk-[A-Za-z0-9_-]{25,})',
        'private key': r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',
        'Windows home': r'[A-Za-z]:[\\/](?:Users|Documents|Desktop|workspace|work|data|桌面)',
        'private machine': r'(?:/root/autodl-tmp/|root@\d)',
        'email': r'[\w.+-]{1,80}@[\w.-]{1,120}\.[A-Za-z]{2,20}',
    }
    # Pattern source contains literals by design; audit its syntax, not its own regex text.
    for path in root.rglob('*'):
        if '.git' in path.parts or '__pycache__' in path.parts:
            continue
        require(not path.is_symlink(), 'Symlink: ' + str(path.relative_to(root)))
        if not path.is_file():
            continue
        count += 1
        size = path.stat().st_size
        if size > largest[1]:
            largest = (path.relative_to(root).as_posix(), size)
        require(size < 10 * 1024 * 1024, 'Large public file: ' + str(path.relative_to(root)))
        if path.suffix in {'.py', '.md', '.json', '.csv', '.svg', '.tex'}:
            text = path.read_text(encoding='utf-8-sig')
            if path.suffix == '.py':
                ast.parse(text, filename=str(path))
            if path.relative_to(root).as_posix() != 'scripts/verify_package.py':
                for label, pattern in patterns.items():
                    require(not re.search(pattern, text), f'{label} review required: {path.relative_to(root)}')
            if path.suffix == '.svg':
                require('<script' not in text and '<foreignObject' not in text, 'Active SVG content')
                require(not re.search(r'(?:href|src)\s*=\s*[\x22\x27]https?://', text), 'External SVG dependency')
    return {'public_files': count, 'largest_file': largest}


def verify(root):
    root = root.resolve()
    return dict(status='PASS', imported_artifacts=check_hashes(root), local_links=check_links(root),
                results=check_results(root), files=check_files(root),
                training=False, inference=False, scientific_result_generation=False,
                scope='Packaged identity/static checks; no independent tensor-level reproduction')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root), indent=2))
    except (ValueError, OSError, KeyError, SyntaxError, StopIteration) as exc:
        print(json.dumps({'status': 'FAIL', 'reason': str(exc)}, indent=2))
        raise SystemExit(1) from exc


if __name__ == '__main__':
    main()
