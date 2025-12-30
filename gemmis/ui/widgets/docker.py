"""
Docker Widget - Real-time container status
"""

from textual.app import ComposeResult
from textual.widgets import DataTable, Static
from ...tools.docker_ops import list_containers

class DockerStatus(Static):
    """Docker Container List"""

    def compose(self) -> ComposeResult:
        yield DataTable(cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("ID", "Name", "Image", "Status", "Ports")
        self.refresh_containers()
        self.set_interval(3.0, self.refresh_containers)

    def refresh_containers(self) -> None:
        table = self.query_one(DataTable)

        result = list_containers(all=True)
        if "error" in result:
            # Maybe show error label?
            return

        current_row = table.cursor_row
        table.clear()

        for c in result.get("containers", []):
            ports = str(c.get("ports", ""))[:20]
            table.add_row(
                c["id"],
                c["name"],
                c["image"][:20],
                c["status"],
                ports,
                key=c["id"]
            )

        if current_row is not None and current_row < table.row_count:
             table.move_cursor(row=current_row)
