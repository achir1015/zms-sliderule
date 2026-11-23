import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SR_NO_VOICE", "1")
from sr.database import DB  # noqa: E402
from sr.dbserver import LocalDatabaseServer  # noqa: E402
from sr.settings import Settings, find_mariadb  # noqa: E402

TEST_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_db")


@pytest.fixture(scope="session")
def server():
    os.environ["SR_DATA_DIR"] = TEST_ROOT
    st = Settings(port=3488, password="test-pw-123", database="sr_test", mariadb_bin=find_mariadb(),
                  datadir=os.path.join(TEST_ROOT, "mariadb"))
    srv = LocalDatabaseServer(st)
    srv.start()
    yield st
    srv.stop()


@pytest.fixture()
def db(server):
    d = DB(server)
    c = d.connect(use_db=False)
    with c.cursor() as cur:
        cur.execute("DROP DATABASE IF EXISTS sr_test")
    c.close()
    d.prepare()
    yield d
    d.close()


@pytest.fixture()
def biz(db):
    from sr.biz import Biz
    b = Biz(db)
    b.create_first_admin("admin", "管理員", "admin123")
    b.login("admin", "admin123")
    return b
