"""test_api.py — Web 项目测试（Task 4 新增 /health 后需全部通过）"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_items
from api import list_api, create_api

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py")


def run_server(port):
    proc = subprocess.Popen(
        [sys.executable, SERVER, str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)
    return proc


def test_list_api():
    r = list_api()
    assert r["count"] == 2
    assert r["items"][0]["name"] == "apple"


def test_create_api():
    item = create_api({"name": "cherry", "price": 5.0})
    assert item["id"] == 3
    assert item["name"] == "cherry"


def test_db_has_items():
    assert len(get_items()) >= 2


def test_health_route_exists():
    """新增 GET /health 接口：必须存在，且返回 ok"""
    import server
    assert hasattr(server, "HEALTH_RESPONSE"), "server.py 需要定义 HEALTH_RESPONSE"
    assert server.HEALTH_RESPONSE["status"] == "ok"


def test_health_via_http():
    proc = run_server(18080)
    try:
        with urllib.request.urlopen("http://127.0.0.1:18080/health", timeout=5) as resp:
            data = json.loads(resp.read())
        assert data["status"] == "ok", f"status != ok: {data}"
        assert data["version"] == "1.0", f"version != 1.0: {data}"
    finally:
        proc.terminate()
        proc.wait()


def test_404_unknown():
    proc = run_server(18081)
    try:
        try:
            urllib.request.urlopen("http://127.0.0.1:18081/unknown", timeout=5)
            code = 200
        except urllib.error.HTTPError as e:
            code = e.code
        assert code == 404, f"expected 404, got {code}"
    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    tests = [test_list_api, test_create_api, test_db_has_items,
             test_health_route_exists, test_health_via_http, test_404_unknown]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    sys.exit(1 if failed else 0)