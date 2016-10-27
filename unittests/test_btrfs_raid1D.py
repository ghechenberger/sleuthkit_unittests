#!/usr/bin/python3
################################################################################
# @file test_btrfs_raid1D.py
# @author Gerhard Hechenberger <gerhard.hechenberger@student.tuwien.ac.at>
# @date 2016-10-17
# @version 1.0
#
# @brief unit test module using an btrfs image with raid 1
# @details This test class represents a unit test using a btrfs image with
# raid 1 enabled for data only. It inherits its test functions from its
# parent and provides functions to run on its own or return a test suite to
# another script.
################################################################################

import unittest
import test_btrfs


class BtrfsRaid1D(test_btrfs.TestBtrfs):
    @classmethod
    def setUpClass(cls):
        super().setUpClassCustom(cls, "btrfs_raid1D")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClassCustom(cls, "btrfs_raid1D")


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(BtrfsRaid1D)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
