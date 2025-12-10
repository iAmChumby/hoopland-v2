
import logging
from textual.widgets import RichLog

class TextualLogHandler(logging.Handler):
    """
    A logging handler that writes logs to a Textual RichLog widget.
    """
    def __init__(self, rich_log: RichLog):
        super().__init__()
        self.rich_log = rich_log
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))

    def emit(self, record):
        try:
            msg = self.format(record)
            
            # Apply styling based on level
            if record.levelno >= logging.ERROR:
                style = "bold red"
            elif record.levelno >= logging.WARNING:
                style = "yellow"
            elif record.levelno >= logging.INFO:
                style = "green"
            else:
                style = "dim"
                
            self.rich_log.write(f"[{style}]{msg}[/]")
            
        except Exception:
            self.handleError(record)
