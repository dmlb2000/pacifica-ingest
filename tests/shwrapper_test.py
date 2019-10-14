#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Sh wrapper library."""
# pylint: disable=unused-import
try:
    import sh
except ImportError:
    import pbs

    class Sh(object):
        """Sh style wrapper."""

        def __getattr__(self, attr):
            """Return command object like sh."""
            return pbs.Command(attr)

        # pylint: disable=invalid-name
        @staticmethod
        def Command(attr):
            """Return command object like sh."""
            return pbs.Command(attr)
    sh = Sh()
