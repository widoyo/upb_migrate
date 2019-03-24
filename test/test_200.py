from paste.tests.fixture import TestApp
from node.tools import *
from main import app


class TestMain():
    def test_url_ok(self):
        middleware = []
        testApp = TestApp()
