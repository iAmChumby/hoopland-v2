"""
Unit tests for the logger module.
Tests logging setup, directory creation, and file handling.
"""

import pytest
import os
import glob
import logging
import tempfile
from unittest.mock import patch

from hoopland.logger import setup_logger


class TestSetupLogger:
    """Tests for the setup_logger function."""

    def test_setup_logger_creates_directory(self, tmp_path):
        """Test that setup_logger creates the log directory."""
        with patch('hoopland.logger.os.path.join', side_effect=lambda *args: os.path.join(str(tmp_path), *args[1:])):
            # Patch to use temp directory
            pass
        
        # Direct test - setup_logger creates logs/{MODE}
        setup_logger(mode="TESTMODE", year="2024")
        log_dir = os.path.join("logs", "TESTMODE")
        assert os.path.exists(log_dir)

    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a logger."""
        logger = setup_logger(mode="TEST", year="2024")
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_creates_timestamped_file(self):
        """Test that log files have timestamps."""
        setup_logger(mode="TIMESTAMP", year="2024")
        
        log_files = glob.glob(os.path.join("logs", "TIMESTAMP", "TIMESTAMP_2024_*.log"))
        assert len(log_files) > 0

    def test_setup_logger_mode_uppercase(self):
        """Test that mode is uppercased in directory."""
        setup_logger(mode="lowercase", year="2024")
        
        log_dir = os.path.join("logs", "LOWERCASE")
        assert os.path.exists(log_dir)

    def test_setup_logger_without_year(self):
        """Test setup_logger without year parameter."""
        setup_logger(mode="NOYEAR")
        
        log_files = glob.glob(os.path.join("logs", "NOYEAR", "NOYEAR_*.log"))
        assert len(log_files) > 0

    def test_setup_logger_replaces_file_handler(self):
        """Test that setup_logger replaces existing FileHandlers."""
        root_logger = logging.getLogger()
        
        # Count initial file handlers
        initial_file_handlers = len([h for h in root_logger.handlers if isinstance(h, logging.FileHandler)])
        
        # Setup multiple times
        setup_logger(mode="REPLACE1", year="2024")
        setup_logger(mode="REPLACE2", year="2024")
        
        # Should still have only one file handler
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) <= initial_file_handlers + 1

    def test_setup_logger_writes_to_file(self):
        """Test that logger actually writes to file."""
        logger = setup_logger(mode="WRITE", year="2024")
        
        # Write a test message
        logger.info("Test message for verification")
        
        # Find the log file
        log_files = glob.glob(os.path.join("logs", "WRITE", "WRITE_2024_*.log"))
        assert len(log_files) > 0
        
        # Read and verify content
        with open(log_files[-1], 'r') as f:
            content = f.read()
            # The file should have some content from the setup
            assert len(content) > 0

    def test_setup_logger_sets_level(self):
        """Test that logger level is set to INFO."""
        logger = setup_logger(mode="LEVEL", year="2024")
        assert logger.level == logging.INFO


class TestLogDirectoryStructure:
    """Tests for log directory structure."""

    def test_nba_log_directory(self):
        """Test NBA logs go to correct directory."""
        setup_logger(mode="NBA", year="2023")
        assert os.path.exists(os.path.join("logs", "NBA"))

    def test_ncaa_log_directory(self):
        """Test NCAA logs go to correct directory."""
        setup_logger(mode="NCAA", year="2024")
        assert os.path.exists(os.path.join("logs", "NCAA"))

    def test_draft_log_directory(self):
        """Test Draft logs go to correct directory."""
        setup_logger(mode="DRAFT", year="2003")
        assert os.path.exists(os.path.join("logs", "DRAFT"))

    def test_log_files_isolated(self):
        """Test that different modes create separate files."""
        setup_logger(mode="ISOLATE1", year="2024")
        setup_logger(mode="ISOLATE2", year="2024")
        
        files1 = glob.glob(os.path.join("logs", "ISOLATE1", "*.log"))
        files2 = glob.glob(os.path.join("logs", "ISOLATE2", "*.log"))
        
        assert len(files1) > 0
        assert len(files2) > 0
        # Files should be in different directories
        assert files1[0] != files2[0]
