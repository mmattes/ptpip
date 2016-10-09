#!/usr/bin/env python
# -*- coding: utf-8 -
import pytest
from ptpip.ptpip import PtpIpConnection


@pytest.fixture(scope="module")
def ptpip():
    return PtpIpConnection()
