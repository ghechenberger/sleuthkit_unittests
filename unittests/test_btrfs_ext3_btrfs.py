#!/usr/bin/python3
################################################################################
# @file test_btrfs_ext3_btrfs.py
# @author Gerhard Hechenberger <gerhard.hechenberger@student.tuwien.ac.at>
# @date 2016-10-1
# @version 1.0
#
# @brief unit test module using an btrfs image converted from ext3
# @details This test class represents a unit test using a btrfs image converted
# from ext3. It inherits its test functions from its parent and provides
# functions to run on its own or return a test suite to another script.
################################################################################

import unittest
import test_btrfs


class BtrfsExt3Btrfs(test_btrfs.TestBtrfs):
    @classmethod
    def setUpClass(cls):
        super().setUpClassCustom(cls, "ext3_btrfs")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClassCustom(cls, "ext3_btrfs")


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(BtrfsExt3Btrfs)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
