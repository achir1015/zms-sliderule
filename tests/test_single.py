"""只能開一個：第一個程式拿到鎖時，第二個拿不到；第一個結束後就拿得到。"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLD = ("import sys, time; sys.path.insert(0, %r); from sr import single; "
        "print(single.acquire(0, sys.argv[1]), flush=True); time.sleep(6)" % HERE)


def test_single_instance(tmp_path):
    from sr import single
    lock = str(tmp_path / "instance.lock")
    p = subprocess.Popen([sys.executable, "-c", HOLD, lock], stdout=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == "True"          # 第一個程式拿到鎖
    t0 = time.time()
    assert single.acquire(wait=1.0, path=lock) is False    # 第二個：等 1 秒仍拿不到
    assert time.time() - t0 >= 0.9
    p.wait(timeout=20)                                       # 第一個結束 → 鎖自動解開
    assert single.acquire(wait=2.0, path=lock) is True
    single._handle.close()
    single._handle = None
