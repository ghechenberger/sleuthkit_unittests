#!/usr/bin/python3
################################################################################
# @file test_btrfs_noextref.py
# @author Gerhard Hechenberger <gerhard.hechenberger@student.tuwien.ac.at>
# @date 2016-10-17
# @version 1.0
#
# @brief unit test module using an btrfs image without option "extref"
# @details This test class represents a unit test using a btrfs image with
# option "extref" disabled. It inherits its test functions from its parent and
# provides functions to run on its own or return a test suite to another script.
################################################################################

import unittest
import test_btrfs


class BtrfsExtref(test_btrfs.TestBtrfs):
    @classmethod
    def setUpClass(cls):
        super().setUpClassCustom(cls, "btrfs_noextref")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClassCustom(cls, "btrfs_noextref")


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(BtrfsExtref)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
