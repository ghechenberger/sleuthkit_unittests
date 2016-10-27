#!/usr/bin/python3
################################################################################
# @file test_btrfs.py
# @author Gerhard Hechenberger <gerhard.hechenberger@student.tuwien.ac.at>
# @date 2016-10-17
# @version 1.0
#
# @brief unit test module for all tests
################################################################################

import unittest
import test_btrfs_standard
import test_btrfs_zlib
import test_btrfs_lzo
import test_btrfs_mixed
import test_btrfs_nofeature
import test_btrfs_nodemin
import test_btrfs_nodemax
import test_btrfs_noextref
import test_btrfs_noskinny
import test_btrfs_noholes
import test_btrfs_raid0DM
import test_btrfs_raid1D
import test_btrfs_raid1DM
import test_btrfs_ext2_btrfs
import test_btrfs_ext3_btrfs
import test_btrfs_ext4_btrfs

allsuite = unittest.TestSuite([
    test_btrfs_standard.suite(),
    test_btrfs_zlib.suite(),
    test_btrfs_lzo.suite(),
    test_btrfs_mixed.suite(),
    test_btrfs_nofeature.suite(),
    test_btrfs_nodemin.suite(),
    test_btrfs_nodemax.suite(),
    test_btrfs_noextref.suite(),
    test_btrfs_noskinny.suite(),
    test_btrfs_noholes.suite(),
    test_btrfs_raid0DM.suite(),
    test_btrfs_raid1D.suite(),
    test_btrfs_raid1DM.suite(),
    test_btrfs_ext2_btrfs.suite(),
    test_btrfs_ext3_btrfs.suite(),
    test_btrfs_ext4_btrfs.suite()
    ])

unittest.TextTestRunner(verbosity=2).run(allsuite)
