# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the OpenTimelineIO project

import sys
import shutil
import tempfile
import unittest
import pytest

import opentimelineio as otio


class TestCoreFunctions(unittest.TestCase):
    
    @pytest.fixture()
    def dir():
        return tempfile.mkdtemp()
    
    def test_deserialize_json_from_file_errors(self):
        """Verify that the bindings return the correct errors based on the errno"""
        if sys.version_info[0] < 3:
            excType = OSError
        else:
            excType = FileNotFoundError  # noqa: F821

        with self.assertRaises(excType) as exc:
            otio.core.deserialize_json_from_file('non-existent-file-here')
        assert (exc.exception, excType)


    @unittest.skipUnless(not sys.platform.startswith("win"), "requires non Windows sytem")  # noqa
    def test_serialize_json_to_file_errors_non_windows(self):
        """Verify that the bindings return the correct errors based on the errno"""
        if sys.version_info[0] < 3:
            excType = OSError
        else:
            excType = IsADirectoryError  # noqa: F821

        with self.assertRaises(excType) as exc:
            otio.core.serialize_json_to_file({}, tempfile.mkdtemp())
        assert (exc.exception, excType)


    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_serialize_json_to_file_errors_windows(self):
        """Verify that the bindings return the correct errors based on the errno"""
        if sys.version_info[0] < 3:
            excType = OSError
        else:
            excType = PermissionError  # noqa: F821

        with self.assertRaises(excType) as exc:
            otio.core.serialize_json_to_file({}, dir())
        assert (exc.exception, excType)
def myTestCoreFunctions():
    return 
