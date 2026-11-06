"""浏览器检查离线页面，并生成 README 使用的真实截图。需要 playwright。"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / 'docs/images'
    out.mkdir(parents=True, exist_ok=True)
    errors, requests, checks = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1080}, device_scale_factor=1)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: requests.append(request.url))
        page.goto((ROOT / 'index.html').as_uri(), wait_until='load')
        assert page.locator('.tower-row').count() == 67
        assert page.evaluate('() => [...document.images].every(i => i.complete && i.naturalWidth > 0)')
        assert not page.evaluate('() => document.documentElement.scrollWidth > innerWidth')
        page.screenshot(path=str(out / 'overview.png'))
        checks.append('67座炮塔及图标离线加载正常')
        page.locator('[data-view="matrix"]').click()
        assert page.locator('.matrix tbody tr').count() == 67
        page.locator('#explore').scroll_into_view_if_needed()
        page.screenshot(path=str(out / 'matrix.png'))
        checks.append('67×18主题矩阵正常')
        page.locator('[data-view="list"]').click()
        page.locator('#search').fill('小水母')
        page.locator('.tower-row .tower-name').click()
        page.locator('#detail [data-stages="267"][data-theme="0"]').click()
        assert [int(s) for s in page.locator('#modal .level-pill').all_text_contents()] == [17, 27, 87, 99, 107, 120]
        page.locator('#modal').screenshot(path=str(out / 'jellyfish-levels.png'))
        page.locator('#modal [data-evidence="18:107"]').click()
        assert '223, 239, 232, 205, 267' in page.locator('#modal').inner_text()
        assert '小水母' in page.locator('#modal').inner_text()
        page.locator('#modal').screenshot(path=str(out / 'level-evidence.png'))
        checks.append('小水母6关及107关官方配置追溯正常')
        page.locator('#closeModal').click()
        page.locator('#reset').click()
        page.evaluate('() => selectTower(248)')
        page.locator('#detail [data-theme="15"]').click()
        assert '本主题无可建造关卡（0 关）' in page.locator('#modal').inner_text()
        page.locator('#closeModal').click()
        checks.append('登场后的零值主题可点开查看')
        page.evaluate('() => selectTower(201)')
        with page.expect_download() as event:
            page.locator('#exportAll').click()
        assert event.value.path().stat().st_size > 1000
        checks.append('CSV导出正常')
        page.locator('#toast').evaluate('(e) => e.classList.remove("show")')
        page.set_viewport_size({'width': 390, 'height': 844})
        page.evaluate('() => window.scrollTo(0,0)')
        assert not page.evaluate('() => document.documentElement.scrollWidth > innerWidth')
        page.screenshot(path=str(out / 'mobile.png'))
        checks.append('390px手机布局无横向溢出')
        assert not errors, errors
        assert not any(url.startswith(('http:', 'https:')) for url in requests)
        checks.append('无JavaScript错误，无外网请求')
        browser.close()
    result = {'status': 'passed', 'checks': checks, 'pageErrors': errors, 'networkRequests': 0}
    (ROOT / 'data/browser-check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
