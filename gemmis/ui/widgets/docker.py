"""
Docker Widget for Gemmis TUI
"""
from textual.app import ComposeResult
from textual.widgets import Static, DataTable, Log
from textual.containers import Vertical
from textual.message import Message

from ...tools.docker_ops import list_containers, get_container_logs

class ContainerSelected(Message):
    """Event sent when a Docker container is selected."""
    def __init__(self, container_id: str) -> None:
        super().__init__()
        self.container_id = container_id

class ContainerList(Static):
    """A widget to display a list of Docker containers."""

    def compose(self) -> ComposeResult:
        yield DataTable(id="container-list")

    def on_mount(self) -> None:
        """Set up the table and start the worker."""
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Name", "Image", "Status")
        self.set_interval(5.0, self.update_container_list) # docker_status worker
        self.update_container_list()

    def update_container_list(self) -> None:
        """Worker to refresh the container list."""
        table = self.query_one(DataTable)
        result = list_containers(all=True)
        if "error" in result:
            return
        containers = result.get("containers", [])

        cursor_row = table.cursor_row

        table.clear()
        for c in containers:
            table.add_row(c['id'][:12], c['name'], c['image'], c['status'], key=c['id'])

        if cursor_row < len(table.rows):
            table.move_cursor(row=cursor_row)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle container selection."""
        self.post_message(ContainerSelected(event.row_key.value))

class LogViewer(Static):
    """A widget to display container logs."""

    def __init__(self):
        super().__init__(id="log-viewer")

    def compose(self) -> ComposeResult:
        yield Log(id="log-content", highlight=True)

    def update_logs(self, container_id: str) -> None:
        """Update the log viewer with logs from the selected container."""
        log_widget = self.query_one(Log)
        log_widget.clear()
        logs = get_container_logs(container_id)
        if "error" in logs:
            log_widget.write(logs["error"])
        else:
            log_widget.write(logs["logs"])

class Docker(Static):
    """The main Docker widget, containing the container list and log viewer."""

    def compose(self) -> ComposeResult:
        yield ContainerList()
        yield LogViewer()

    def on_container_selected(self, message: ContainerSelected) -> None:
        """Update the log viewer when a container is selected."""
        log_viewer = self.query_one(LogViewer)
        log_viewer.update_logs(message.container_id)
