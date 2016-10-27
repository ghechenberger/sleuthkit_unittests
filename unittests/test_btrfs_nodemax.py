#!/usr/bin/python3
################################################################################
# @file test_btrfs_nodemax.py
# @author Gerhard Hechenberger <gerhard.hechenberger@student.tuwien.ac.at>
# @date 2016-10-17
# @version 1.0
#
# @brief unit test module using an btrfs image with maximal inode size
# @details This test class represents a unit test using a btrfs image with
# maximal inode size. It inherits its test functions from its parent and
# provides functions to run on its own or return a test suite to another script.
################################################################################

import unittest
import test_btrfs


class BtrfsNodeMax(test_btrfs.TestBtrfs):
    @classmethod
    def setUpClass(cls):
        super().setUpClassCustom(cls, "btrfs_nodemax")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClassCustom(cls, "btrfs_nodemax")


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(BtrfsNodeMax)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
