#!/usr/bin/python3
################################################################################
# @file test_btrfs_lzo.py
# @author Gerhard Hechenberger <gerhard.hechenberger@student.tuwien.ac.at>
# @date 2016-10-17
# @version 1.0
#
# @brief unit test module using an lzo compressed btrfs image
# @details This test class represents a unit test using an lzo compressed btrfs
# image. It inherits its test functions from its parent and provides
# functions to run on its own or return a test suite to another script.
################################################################################

import unittest
import test_btrfs


class BtrfsLzo(test_btrfs.TestBtrfs):
    @classmethod
    def setUpClass(cls):
        super().setUpClassCustom(cls, "btrfs_lzo")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClassCustom(cls, "btrfs_lzo")


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(BtrfsLzo)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
