#!/usr/bin/python3
################################################################################
# @file test_btrfs.py
# @author Gerhard Hechenberger <gerhard.hechenberger@student.tuwien.ac.at>
# @date 2016-10-22
# @version 1.0
#
# @brief super class, providing all functions for btrfs unit tests
# @details This class servers as parent for all other btrfs unit test classes.
# It provides custom set-up and tear-down methods to prepare the testing
# environment an implements all test methods, used to test the file data, the
# file meta data and the structure of the image.
################################################################################

import unittest
import subprocess
import os
import sys
import shutil
import testimage
import textparser


class TestBtrfs(unittest.TestCase):
    # options to be changed by the user
    # mount path for the test images
    mpath = "/mnt/loop"
    # directory where the created images are stored
    ipath = "images"
    # directory where the recovered files are stored, created before and deleted after test
    rec_dir = ".files"
    # keep the images after the tests finished (takes some space, but speeds up additional test runs
    keep_images = False
    # ignore all files associated with the backup created while converting ext to btrfs
    ignore_ext_backup = True
    # ignore snapshotted subvolumes (as intended) in TSK
    fix_subvols = True
    # ignore the zero-size of directories, subvolumes and snapshots in TSK
    fix_size = True
    
    fac = testimage.ImageFactory(True)
    parser = textparser.TextParser(ignore_ext_backup, fix_subvols)

    loopdev = None

    tsk = set()
    stat = set()

    ##
    # prepare everything before the tests are started
    # @details This function creates and mounts a new test image (or uses
    # a given custom image). Then it reads the image metadata using the TSK
    # tools fls and ils and the Linux tool stat. Finally, all files are
    # recovered to a directory.
    #
    # @param imagetype type of the test image to use
    # @param custom flag to indicate a custom image
    # @return None
    #
    def setUpClassCustom(self, imagetype, custom=False):
        # create directory for image files
        if not os.path.exists(self.ipath):
            try:
                os.mkdir(self.ipath)
            except OSError as e:
                print(e, file=sys.stderr)
                raise testimage.ImageCreationError("could not create image directory")

        if custom:
            print("using custom image", imagetype)
            self.files = (imagetype, imagetype + ".md5")
            self.ipath = None
        else:
            print("creating image ...")
            self.files = self.fac.create(imagetype, imagedir=self.ipath)

            # add path to file names
            self.files = list(self.files)
            for i in range(0, len(self.files)):
                self.files[i] = os.path.join(self.ipath, self.files[i])
            self.files = tuple(self.files)

        if "raid" in imagetype:
            self.loopdev = self.fac.mount_raid(imagetype, self.ipath, self.mpath)
        else:
            self.fac.mount(imagetype, self.ipath, self.mpath)
        
        try:
            print("retrieving metadata from image using tsk")
            out = subprocess.check_output(['fls', '-r', '-m', '/', self.files[0]])
            tsk_files = self.parser.parse_fls_files(out)
            out = subprocess.check_output(['ils', '-a', self.files[0]])
            tsk_inodes = self.parser.parse_ils(out)
            for line in tsk_files:
                line.extend(tsk_inodes[line[1]])
                self.tsk.add(tuple(line))
            # print("TSK")
            # print(*self.tsk, sep='\n')
            
            print("retrieving metadata from filesystem using stat")
            stat_cmd = "stat -c '%n|%i|a|%u|%g|%Y|%X|%Z|%W|%a|%h|%s' "
            cmd = [stat_cmd + os.path.join(self.mpath, '*')]
            out = subprocess.check_output(cmd, shell=True)
            stat_inodes = self.parser.parse_stat(out, self.mpath)
            
            for root, dirs, files in os.walk(self.mpath):
                for dname in dirs:
                    try:
                        cmd = [stat_cmd + os.path.join(os.path.join(root, dname), '*')]
                        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
                        stat_inodes.extend(self.parser.parse_stat(out, self.mpath))
                    except subprocess.CalledProcessError:
                        continue
            for line in stat_inodes:
                self.stat.add(tuple(line))
            # print("STAT")
            # print(*self.stat, sep='\n')
            
            print("recovering files ...")
            if os.path.exists(self.rec_dir):
                raise Exception("file recovery directory already exits")
            os.makedirs(self.rec_dir)
            cmd = ['tsk_recover', '-a', self.files[0], self.rec_dir]
            subprocess.call(cmd, stdout=subprocess.DEVNULL)
        except Exception:
            self.fac.umount(self.mpath)
            shutil.rmtree(self.rec_dir, ignore_errors=True)
            raise

    ##
    # clean up after all test cases
    #
    # @param imagetype name of the image used
    # @param custom flag to indicate a custom image
    # @return None
    #
    def tearDownClassCustom(self, imagetype, custom=False):
        print("cleaning up files ...")

        # unmount
        if "raid" in imagetype:
            self.fac.umount_raid(self.mpath, self.loopdev)
        else:
            self.fac.umount(self.mpath)

        # delete recovered files
        shutil.rmtree(self.rec_dir, ignore_errors=True)

        # delete created image
        if not self.keep_images and not custom:
            print("removing image ...", imagetype + ".img")
            self.fac.delete(imagetype, self.ipath)
            shutil.rmtree(self.ipath, ignore_errors=True)
    
    ##
    # test if the file structure matches
    #
    def test_structure(self):
        tsk = set()
        for line in self.tsk:
            tsk.add(line[0])
        
        stat = set()
        for line in self.stat:
            stat.add(line[0])
        
        self.assertEqual(stat, tsk)
    
    ##
    # test if the inode number of the files matches
    #
    def test_metadata_inode(self):
        tsk = set()
        for line in self.tsk:
            try:
                cmd = ['istat', self.files[0], str(line[1])]
                istat = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                istat = e.output
            istat = istat.splitlines()
            istat = istat[2].decode('utf-8').split(' ')
            tsk.add((line[0], int(istat[2])))
        
        stat = set()
        for line in self.stat:
            stat.add((line[0], line[1]))
        
        self.assertEqual(stat, tsk)
    
    ##
    # test if the UID of the files matches
    #
    def test_metadata_uid(self):
        tsk = set()
        for line in self.tsk:
            tsk.add((line[0], line[3]))
        
        stat = set()
        for line in self.stat:
            stat.add((line[0], line[3]))
        
        self.assertEqual(stat, tsk)
    
    ##
    # test if the GID of the files matches
    #
    def test_metadata_gid(self):
        tsk = set()
        for line in self.tsk:
            tsk.add((line[0], line[4]))
        
        stat = set()
        for line in self.stat:
            stat.add((line[0], line[4]))
        
        self.assertEqual(stat, tsk)
    
    ##
    # test if the modification time of the files matches
    #
    def test_metadata_mtime(self):
        tsk = set()
        for line in self.tsk:
            tsk.add((line[0], line[5]))
        
        stat = set()
        for line in self.stat:
            stat.add((line[0], line[5]))
        
        self.assertEqual(stat, tsk)
    
    ##
    # test if the access time of the files matches
    #
    def test_metadata_atime(self):
        tsk = set()
        for line in self.tsk:
            tsk.add((line[0], line[6]))
        
        stat = set()
        for line in self.stat:
            stat.add((line[0], line[6]))
        
        self.assertEqual(stat, tsk)
    
    ##
    # test if the change time of the files matches
    #
    def test_metadata_ctime(self):
        tsk = set()
        for line in self.tsk:
            tsk.add((line[0], line[7]))
        
        stat = set()
        for line in self.stat:
            stat.add((line[0], line[7]))
        
        self.assertEqual(stat, tsk)
    
    ##
    # test if the creation time of the files matches
    #
    def test_metadata_crtime(self):
        tsk = set()
        for line in self.tsk:
            tsk.add((line[0], line[8]))
        
        stat = set()
        for line in self.stat:
            stat.add((line[0], line[8]))
        
        self.assertEqual(stat, tsk)
    
    ##
    # test if the mode of the files matches
    #
    def test_metadata_mode(self):
        tsk = set()
        for line in self.tsk:
            tsk.add((line[0], line[9]))
        
        stat = set()
        for line in self.stat:
            stat.add((line[0], line[9]))
        
        self.assertEqual(stat, tsk)
    
    ##
    # test if the link count of the files matches
    #
    def test_metadata_links(self):
        tsk = set()
        for line in self.tsk:
            tsk.add((line[0], line[10]))
        
        stat = set()
        for line in self.stat:
            stat.add((line[0], line[10]))
        
        self.assertEqual(stat, tsk)
    
    ##
    # test if the size of the files matches
    #
    def test_metadata_size(self):
        tsk = set()
        for line in self.tsk:
            tsk.add((line[0], line[11]))
        
        stat = set()
        for line in self.stat:
            value = line[11]
            # fix snapshot, subvolume and directory sizes if desired
            if self.fix_size:
                last = line[0].split('/')[-1]
                if "directory" in last or "subvolume" in last or "snapshot" in last:
                    value = 0
            stat.add((line[0], value))
        
        self.assertEqual(stat, tsk)
    
    ##
    # test if the data of the files matches (by comparing their md5 sums)
    #
    def test_filedata(self):
        stat = set()
        with open(self.files[-1]) as f:
            line = f.readline()
            while line != "" and line[0] != '-':
                line = line[0:-1].split(' ')
                fname = ' '.join(line[1:])
                stat.add((fname, line[0]))
                line = f.readline()
        
        tsk = set()
        for root, dirs, files in os.walk(self.rec_dir):
            for f in files:
                if f[0] != '$':
                    fpath = os.path.join(root, f)
                    # fix snapshot - subvolume behaviour if desired
                    if self.fix_subvols:
                        if "snapshot" in fpath and fpath.count("subvolume") > 0:
                            continue
                    if self.ignore_ext_backup:
                        if "ext2_saved" in fpath:
                            continue
                    # convert numbers to integers
                    h = self.fac.md5sum(fpath)
                    tsk.add((os.path.relpath(fpath, self.rec_dir), h))
        
        self.assertEqual(stat, tsk)
