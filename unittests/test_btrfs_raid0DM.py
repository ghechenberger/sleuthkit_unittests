#!/usr/bin/python3
################################################################################
# @file test_btrfs_raid0DM.py
# @author Gerhard Hechenberger <gerhard.hechenberger@student.tuwien.ac.at>
# @date 2016-10-17
# @version 1.0
#
# @brief unit test module using an btrfs image with raid 0
# @details This test class represents a unit test using a btrfs image with
# raid 0 enabled for data and meta data. It inherits its test functions from its
# parent and provides functions to run on its own or return a test suite to
# another script.
################################################################################

import unittest
import test_btrfs


class BtrfsRaid0DM(test_btrfs.TestBtrfs):
    @classmethod
    def setUpClass(cls):
        super().setUpClassCustom(cls, "btrfs_raid0DM")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClassCustom(cls, "btrfs_raid0DM")


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(BtrfsRaid0DM)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
