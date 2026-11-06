"""用仓库内的数据、图标和模板重建可离线使用的单文件页面。仅需 Python 标准库。"""
import base64
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(name):
    return json.loads((ROOT / name).read_text('utf-8'))


def render():
    data = copy.deepcopy(read_json('data/mainline.json'))
    recheck = read_json('data/independent-check.json')
    fresh = read_json('data/latest-update.json')
    assert recheck['summary']['differences'] == 0
    assert fresh['matchesCurrentStatisticsChain']
    assert fresh['latestEndCode'] == data['audit']['hotUpdate']['lastEndCode']
    data['audit']['independentRecheck'] = recheck['summary']
    data['audit']['latestOnlineCheck'] = fresh
    data['theme18Files'] = recheck['theme18Files']
    for tower in data['towers']:
        tower['description'] = tower['description'].replace('短暂定身', '短时间定身')
    icons = {t['id']: 'data:image/png;base64,' + base64.b64encode(
        (ROOT / f"assets/towers/{t['id']}.png").read_bytes()).decode('ascii') for t in data['towers']}
    template = (ROOT / 'web/template.html').read_text('utf-8')
    values = {
        '__PATCH_COUNT__': str(fresh['patchCount']),
        '__UPDATE_BYTES__': f"{fresh['downloadBytes']:,}",
        '__END_CODE__': fresh['latestEndCode'],
        '__CHECKED_AT__': fresh['checkedAt'].replace('T', ' ').replace('+08:00', '（北京时间）'),
        '__DATA__': json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'),
        '__ICONS__': json.dumps(icons, separators=(',', ':')),
    }
    for token, value in values.items():
        template = template.replace(token, value)
    return template


if __name__ == '__main__':
    output = ROOT / 'index.html'
    output.write_text(render(), 'utf-8', newline='\n')
    print(f'Built {output.name}: {output.stat().st_size:,} bytes')
