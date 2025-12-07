from ebf_core.fileutil.path_norm import norm_path

def test_none_returns_none(tmp_path):
    assert norm_path(None, base=tmp_path) is None

def test_empty_str_returns_none(tmp_path):
    assert norm_path("", base=tmp_path) is None

def test_tilde_and_rel_resolve(tmp_path, monkeypatch):
    home = tmp_path / "home"; home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    base = tmp_path / "cfg"; base.mkdir()
    p = norm_path("~/x.txt", base=base)
    assert p == home / "x.txt"

    q = norm_path("icons/a.ico", base=base)
    assert q == (base / "icons" / "a.ico").resolve()
