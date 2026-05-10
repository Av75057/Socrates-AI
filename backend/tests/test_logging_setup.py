from __future__ import annotations

import json
import logging
import unittest

from app.logging_context import bind_log_context, reset_log_context
from app.logging_setup import JSONFormatter


class TestJSONFormatter(unittest.TestCase):
    def test_renders_required_fields(self) -> None:
        logger = logging.getLogger("test.json")
        formatter = JSONFormatter()
        token = bind_log_context(correlation_id="corr-1", session_id="sess-1")
        try:
            record = logger.makeRecord(
                "test.json",
                logging.INFO,
                __file__,
                1,
                "Turn started",
                args=(),
                exc_info=None,
                extra={"user_id": "u-1", "phase": "awaiting_answer"},
            )
            payload = json.loads(formatter.format(record))
        finally:
            reset_log_context(token)
        self.assertEqual(payload["event"], "Turn started")
        self.assertEqual(payload["correlation_id"], "corr-1")
        self.assertEqual(payload["session_id"], "sess-1")
        self.assertEqual(payload["user_id"], "u-1")
        self.assertEqual(payload["phase"], "awaiting_answer")


if __name__ == "__main__":
    unittest.main()
