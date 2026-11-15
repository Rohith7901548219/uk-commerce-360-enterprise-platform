from pathlib import Path
from urllib.parse import urlparse

import httpx
from streamlit.testing.v1 import AppTest


def test_all_dashboard_pages_with_real_fixture_backend(client, monkeypatch):
    import streamlit as st

    st.cache_data.clear()

    def local_get(url, params=None, **kwargs):
        return client.get(urlparse(url).path, params=params)

    monkeypatch.setattr(httpx, "get", local_get)
    app = AppTest.from_file(Path("app/dashboard.py").resolve(), default_timeout=45).run()
    assert not app.exception
    assert len(app.metric) >= 7
    pages = app.sidebar.radio[0].options
    for name in pages[1:]:
        app.sidebar.radio[0].set_value(name).run()
        assert not app.exception, f"{name}: {list(app.exception)}"
