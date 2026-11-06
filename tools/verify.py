"""复核发布快照的关号、统计、图标、文档链接及页面可重复构建。仅需 Python 标准库。"""
import collections
import csv
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

from build import ROOT, read_json, render


def main():
    data = read_json('data/mainline.json')
    check = read_json('data/independent-check.json')
    fresh = read_json('data/latest-update.json')
    assert len(data['towers']) == 67 and len(data['themes']) == 18
    assert len(data['levels']) == 1660 and len(data['evidence']) == 1687
    assert {t['id'] for t in data['towers']} == set(range(201, 268))
    assert fresh['matchesCurrentStatisticsChain']
    assert data['audit']['hotUpdate']['lastEndCode'] == fresh['latestEndCode']
    assert check['summary']['differences'] == 0
    counted = collections.defaultdict(set)
    seen_keys = set()
    for e in data['evidence']:
        key = (e['theme'], e['key'])
        assert key not in seen_keys
        seen_keys.add(key)
        ids = set(e['rawTowerlist']) & set(range(201, 268))
        assert ids == set(e['configTowerIds']) == set(e['towerIds'])
        assert ids == set(e['rawConfig']['towerlist']) & set(range(201, 268))
        for tid in ids:
            counted[tid, e['theme']].add(e['level'])
    for theme in data['themes']:
        ls = [r for r in data['levels'] if r['theme'] == theme['no']]
        assert {r['level'] for r in ls} == set(range(1, theme['levels'] + 1))
        for row in ls:
            union = {tid for i in row['evidence'] for tid in data['evidence'][i]['towerIds']}
            assert union == set(row['towerIds'])
    for tower in data['towers']:
        assert tower['total'] == sum(tower['counts'])
        assert tower['firstTheme'] == next(n for n, c in enumerate(tower['counts'], 1) if c)
        for n in range(1, 19):
            assert tower['levels'][n - 1] == sorted(counted[tower['id'], n])
            assert tower['counts'][n - 1] == len(counted[tower['id'], n])
    assert sum(t['total'] for t in data['towers']) == sum(len(r['towerIds']) for r in data['levels'])
    mapping = {r['id']: r for r in read_json('data/icon-mapping.json')['towers']}
    assert {tid: mapping[tid]['resource'] for tid in (204, 258, 262)} == {204: 'AirBottle', 258: 'Missile', 262: 'Like'}
    for tid, row in mapping.items():
        assert hashlib.sha256((ROOT / f'assets/towers/{tid}.png').read_bytes()).hexdigest() == row['iconSha256']
    html = (ROOT / 'index.html').read_text('utf-8')
    assert html == render(), 'index.html 与当前模板/数据不同，请先运行 tools/build.py'
    assert not any(w in html for w in ('暂定', '待补全', '待核实', '未核准'))
    assert not re.search(r'__(?:DATA|ICONS|PATCH_COUNT|END_CODE|CHECKED_AT|UPDATE_BYTES)__', html)
    assert not re.search(r'<script[^>]+src=', html, re.I)
    rows18 = check['theme18Files']
    assert len(rows18) == len({r['mapSha256'] for r in rows18}) == 120
    assert next(t for t in data['towers'] if t['id'] == 267)['levels'][17] == [17, 27, 87, 99, 107, 120]
    for doc in ROOT.rglob('*.md'):
        if '.git' in doc.parts:
            continue
        text = doc.read_text('utf-8')
        links = re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text)
        links += re.findall(r'<img[^>]+src=["\']([^"\']+)', text)
        for link in links:
            if link.startswith(('http:', 'https:', '#', 'mailto:')):
                continue
            assert (doc.parent / unquote(link.split('#', 1)[0])).exists(), (doc.name, link)
    with (ROOT / 'data/tower-counts.csv').open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    assert len(rows) == 68
    by_id = {t['id']: t for t in data['towers']}
    for row in rows[1:]:
        tower = by_id[int(row[0])]
        assert row[2] == str(tower['total'])
        assert row[3:21] == [str(c) if n >= tower['firstTheme'] else '' for n, c in enumerate(tower['counts'], 1)]
    print(json.dumps({'status': 'passed', 'levels': 1660, 'configs': 1687, 'towers': 67, 'themeCells': 1206,
                      'iconsChecked': 67, 'hotUpdate': fresh['latestEndCode'], 'reproducibleBuild': True}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
