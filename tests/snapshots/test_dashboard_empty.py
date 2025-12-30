from unittest.mock import patch
from gemmis.app import GemmisApp
from gemmis.ui.widgets.dashboard import Dashboard

async def test_dashboard_snapshot(snapshot):
    with patch("gemmis.app.GemmisApp.init_memory"), \
         patch("gemmis.app.GemmisApp.load_chat_history"), \
         patch("gemmis.ui.widgets.dashboard.Dashboard.set_interval"):
        app = GemmisApp()
        async with app.run_test() as pilot:
            dashboard = pilot.app.query_one(Dashboard)
            snapshot.assert_match(str(dashboard), "dashboard_empty.txt")
