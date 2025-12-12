import unittest
from unittest.mock import MagicMock
import logging
import sys

sys.path.append("src")

from hoopland.tui.logging_handler import TextualLogHandler


class TestTextualLogHandler(unittest.TestCase):
    def test_emit_info(self):
        mock_rich_log = MagicMock()
        handler = TextualLogHandler(mock_rich_log)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        handler.emit(record)

        # Verify write called
        mock_rich_log.write.assert_called_once()
        args, _ = mock_rich_log.write.call_args
        self.assertIn("[green]", args[0])
        self.assertIn("Test message", args[0])

    def test_emit_error(self):
        mock_rich_log = MagicMock()
        handler = TextualLogHandler(mock_rich_log)

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=None,
        )

        handler.emit(record)

        mock_rich_log.write.assert_called_once()
        args, _ = mock_rich_log.write.call_args
        self.assertIn("[bold red]", args[0])
        self.assertIn("Error occurred", args[0])


if __name__ == "__main__":
    unittest.main()
