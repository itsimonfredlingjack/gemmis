from unittest.mock import patch
from gemmis.app import GemmisApp

async def test_sidebar_snapshot(snapshot):
    with patch("gemmis.app.GemmisApp.init_memory"), \
         patch("gemmis.app.GemmisApp.load_chat_history"), \
         patch("gemmis.ui.widgets.sidebar.SystemStats.set_interval"), \
         patch("gemmis.ui.widgets.sidebar.OllamaModels.on_mount"):
        app = GemmisApp()
        async with app.run_test() as pilot:
            sidebar = pilot.app.query_one("Sidebar")
            snapshot.assert_match(str(sidebar), "sidebar_layout.txt")
