#!/usr/bin/env python3
import sys
import pytest
sys.path.append('../dragon_node')
import const
import iguana
from logger import logger

@pytest.fixture
def setup_iguana():
    yield iguana.Iguana("main")

