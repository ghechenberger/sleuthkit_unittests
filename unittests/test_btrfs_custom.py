#!/usr/bin/python3
################################################################################
# @file test_btrfs_custom.py
# @author Gerhard Hechenberger <gerhard.hechenberger@student.tuwien.ac.at>
# @date 2016-10-22
# @version 1.0
#
# @brief unit test module using custom btrfs image
# @details This test class represents a unit test using a custom btrfs image.
# It inherits its test functions from its parent and provides functions to run
# on its own or return a test suite to another script. The custom image have to
# consist of an IMAGE.img and a corresponding IMAGE.img.md5 file and have to be
# stated using its absolute or relative path in the parameters.
################################################################################

import unittest
import test_btrfs


class TestBtrfsCustom(test_btrfs.TestBtrfs):
    @classmethod
    def setUpClass(cls):
        super().setUpClassCustom(cls, "./btrfs_custom.img", True)
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClassCustom(cls, "./btrfs_custom.img", True)


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestBtrfsCustom)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
