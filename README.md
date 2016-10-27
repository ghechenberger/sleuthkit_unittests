# TSK Btrfs unit tests
This repository contains unit tests written in Python to test a novel Btrfs implementation in the Digital Forensic toolkit TSK (The Sleuth Kit). They were developed as part of my bachelor's thesis.

Requirements:
* Linux with btrfs-tools installed (4.0 or higher)
* TSK with Btrfs support (provided by this [pull request](https://github.com/sleuthkit/sleuthkit/pull/413))

Most important files:
* test_btrfs_all.py: This script executes all existing unit test cases (this can really take some time!)
* test_btrfs_MODULE.py: These files contain the different unit test classes and can be executed separately.
* testimage.py: This script can be used stand-alone to create various test images. It is also used by the unit tests.
