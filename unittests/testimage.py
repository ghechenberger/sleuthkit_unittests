#!/usr/bin/python3
################################################################################
# @file create_image.py
# @author Gerhard Hechenberger <gerhard.hechenberger@student.tuwien.ac.at>
# @date 2016-10-22
# @version 1.0
# 
# @brief test image creation script for btrfs
# @details This script creates file system images for testing a btrfs implemen-
# tation. Size of the image and the test-type can be chosen, the filenames
# correspond to the test-types ([type].img or [type].x.img for raid with x as 1
# or 2). All created files are hashed as md5-sums, these are written to an extra
# file named [image-name].md5. Also the complete image file is hashed and saved
# to this file (this process can take some time, according to the image size).
# For the images, various different types are supported:
# - ext4            ext4 as a reference
# - btrfs           btrfs with standard features (as in 3.18, needs 3.10)
# - btrfs_nofeature btrfs with filesystem features disabled
# - btrfs_zlib      fully zlib compressed standard btrfs
# - btrfs_lzo       fully lzo compressed standard btrfs
# - btrfs_mixed     standard btrfs in mixed mode
# - btrfs_nodemin   standard btrfs with minimum inode size
# - btrfs_nodemax   standard btrfs with maximum inode size
# - btrfs_noextref  standard btrfs without option extref (needs 3.7)
# - btrfs_noskinny  standard btrfs without option skinny-metadata (needs 3.10)
# - btrfs_noholes   standard btrfs with option no-holes (needs 3.14)
# - btrfs_raid0DM   standard btrfs raid 0 for data and metadata
# - btrfs_raid1D    standard btrfs raid 1 for data only
# - btrfs_raid1DM   standard btrfs raid 1 for data and metadata
# - ext2_btrfs      created as ext2 and converted to standard btrfs
# - ext3_btrfs      created as ext2 and converted to standard btrfs
# - ext4_btrfs      created as ext2 and converted to standard btrfs
# The contained class can be used to create images from other scripts.
################################################################################

import argparse
from argparse import RawTextHelpFormatter
import os
import sys
import stat
import subprocess
import hashlib
import socket


##
# main program to support stand-alone script usage
#
def main():
    # list of permitted image types
    types = ['ext4', 'btrfs', 'btrfs_zlib', 'btrfs_lzo', 'btrfs_mixed',
             'btrfs_nofeature', 'btrfs_nodemin', 'btrfs_nodemax',
             'btrfs_noextref', 'btrfs_noskinny', 'btrfs_noholes',
             'btrfs_raid0DM', 'btrfs_raid1D', 'btrfs_raid1DM', 'ext2_btrfs',
             'ext3_btrfs', 'ext4_btrfs']

    # parse arguments
    parser = argparse.ArgumentParser(
        description="This script creates file system images for testing a btrfs implementation. "
                    "Size of the image and the test-type can be choosen, the filenames correspond "
                    "to the test-types ([type].img or [type].x.img for raid with x as 1 or 2). All "
                    "created files are hashed as md5-sums, these are written to an extra file named "
                    "[image-name].md5. Also the complete image is hashed and saved to this file "
                    "(this process can take some time, according to the image size). Supported types "
                    "are:\n"
                    "ext4            ext4 as a reference\n"
                    "btrfs           btrfs with standard features (as in 3.18, needs 3.10)\n"
                    "btrfs_nofeature btrfs with filesystem features disabled\n"
                    "btrfs_zlib      fully zlib compressed standard btrfs\n"
                    "btrfs_lzo       fully lzo compressed standard btrfs\n"
                    "btrfs_mixed     standard btrfs in mixed mode\n"
                    "btrfs_nodemin   standard btrfs with minimum inode size\n"
                    "btrfs_nodemax   standard btrfs with maximun inode size\n"
                    "btrfs_noextref  standard btrfs without option extref (needs 3.7)\n"
                    "btrfs_noskinny  standard btrfs without option skinny-metadata (needs 3.10)\n"
                    "btrfs_noholes   standard btrfs with option no-holes (needs 3.14)\n"
                    "btrfs_raid0DM   standard btrfs raid 0 for data and metadata\n"
                    "btrfs_raid1D    standard btrfs raid 1 for data only\n"
                    "btrfs_raid1DM   standard btrfs raid 1 for data and metadata\n"
                    "ext2_btrfs      created as ext2 and converted to standard btrfs\n"
                    "ext3_btrfs      created as ext2 and converted to standard btrfs\n"
                    "ext4_btrfs      created as ext2 and converted to standard btrfs",
        formatter_class=RawTextHelpFormatter)
    parser.add_argument('-s', type=int, default=5, metavar='size',
                        help="size of the image in GiB (default = 5)")
    parser.add_argument('type', metavar='type', choices=types,
                        help="image type, choose from the listed above")
    args = parser.parse_args()

    # create a new image from factory class
    fac = ImageFactory(False)
    try:
        fac.create(args.type, size=args.s, fast=False)
    except ImageCreationError as e:
        print("ERROR:", e, file=sys.stderr)


##
# exception used in the ImageFactory class
#
class ImageCreationError(Exception):
    pass


##
# class used to create and destroy test images
#
class ImageFactory:
    # configurable constants
    # mount path
    MOUNT_PATH = "/mnt/loop"
    # standard options for btrfs (to keep consistency among versions)
    BTRFS_STD_OPT = '-Oextref,skinny-metadata'

    # flag for fast image creation (skip big files)
    f_fast = False
    # text output, if None, stdout is used
    out = None

    ##
    # constructor
    #
    # @param unittest flag to suppress stdout output for unittests
    # @return a new instance of this class
    #
    def __init__(self, unittest=False):
        self.unittest = unittest

    ##
    # create a test image
    #
    # @param imagetype type of the image
    # @param size size of the image (standard = 5)
    # @param fast flag to skip big files for fast tests (standard = False)
    # @param imagedir directory where the files should be created
    # @throw ValueError if received an invalid parameter
    # @throw ImageCreationError in case something went wrong
    # @return tuple of created files
    #
    def create(self, imagetype, size=5, fast=False, imagedir=""):
        if imagetype is None or size is None or fast is None or imagedir is None:
            raise ValueError("parameter must not be None")
        if size <= 0:
            raise ValueError("cannot create zero or negative sized image")

        self.f_fast = fast
        if self.unittest:
            self.out = open(os.devnull, 'w')

        # check for root (needed for mounting and loop devices)
        if os.getuid() != 0:
            raise ImageCreationError("this method needs root")
        uid = int(os.getenv('SUDO_UID'))
        gid = int(os.getenv('SUDO_GID'))

        # check for image directory
        if imagedir != "" and not os.path.exists(imagedir):
            raise ImageCreationError("directory does not exist")

        # create image-filenames from imagetype
        files = self.__type_to_names(imagetype)
        filename = list()
        for f in files[0:-1]:
            filename.append(os.path.join(imagedir, f))
        hfname = os.path.join(imagedir, files[-1])

        # if one of the files already exist, do nothing
        cnt = 0
        for f in filename:
            if os.path.isfile(f):
                cnt += 1
        if cnt != 0:
            if len(filename) == cnt:
                print("image file already exists")
                return files
            else:
                raise ImageCreationError("some image files already exist")

        # create the image(s) and fill with files 
        try:
            # create loop devices and files
            loopdev = []
            for f in filename:
                loopdev += [self.__create_image(f, size, uid, gid)]

            # format images
            print("formatting image ...", file=self.out)

            if imagetype == 'ext4' or \
                            imagetype == 'ext4_btrfs':
                cmd = ['mkfs.ext4', loopdev[0]]
            elif imagetype == 'ext3_btrfs':
                cmd = ['mkfs.ext3', loopdev[0]]
            elif imagetype == 'ext2_btrfs':
                cmd = ['mkfs.ext2', loopdev[0]]
            elif imagetype == 'btrfs' or \
                            imagetype == 'btrfs_zlib' or \
                            imagetype == 'btrfs_lzo':
                cmd = ['mkfs.btrfs', self.BTRFS_STD_OPT, loopdev[0]]
            elif imagetype == 'btrfs_nofeature':
                cmd = ['mkfs.btrfs', '-O^extref,^skinny-metadata', loopdev[0]]
            elif imagetype == 'btrfs_nodemin':
                cmd = ['mkfs.btrfs', self.BTRFS_STD_OPT, '-n4096', loopdev[0]]
            elif imagetype == 'btrfs_nodemax':
                cmd = ['mkfs.btrfs', self.BTRFS_STD_OPT, '-n65536', loopdev[0]]
            elif imagetype == 'btrfs_noextref':
                cmd = ['mkfs.btrfs', '-O^extref,skinny-metadata', loopdev[0]]
            elif imagetype == 'btrfs_noskinny':
                cmd = ['mkfs.btrfs', '-Oextref,^skinny-metadata', loopdev[0]]
            elif imagetype == 'btrfs_noholes':
                cmd = ['mkfs.btrfs', self.BTRFS_STD_OPT + ',no-holes', loopdev[0]]
            elif imagetype == 'btrfs_mixed':
                cmd = ['mkfs.btrfs', self.BTRFS_STD_OPT, '--mixed', loopdev[0]]
            elif imagetype == 'btrfs_raid0DM':
                cmd = ['mkfs.btrfs', self.BTRFS_STD_OPT, '-draid0', '-mraid0',
                       loopdev[0], loopdev[1]]
            elif imagetype == 'btrfs_raid1D':
                cmd = ['mkfs.btrfs', self.BTRFS_STD_OPT, '-draid1', '-mraid0',
                       loopdev[0], loopdev[1]]
            elif imagetype == 'btrfs_raid1DM':
                cmd = ['mkfs.btrfs', self.BTRFS_STD_OPT, '-draid1', '-mraid1',
                       loopdev[0], loopdev[1]]
            else:
                raise ImageCreationError("this type is not supported")
            res = subprocess.call(cmd, stdout=self.out, stderr=self.out)
            if res != 0:
                raise ImageCreationError("formatting failed")

            # mount image(s)
            self.mount(imagetype, imagedir, self.MOUNT_PATH)

            # create files
            print("creating files ...", file=self.out)

            self.__create_files_std(self.MOUNT_PATH)
            if imagetype == 'ext4':
                self.__create_files_deleted(self.MOUNT_PATH)
            elif imagetype == 'ext4_btrfs' or \
                            imagetype == 'ext3_btrfs' or \
                            imagetype == 'ext2_btrfs':
                self.__create_files_deleted(self.MOUNT_PATH)
                self.umount(self.MOUNT_PATH)
                res = subprocess.call(['btrfs-convert', self.BTRFS_STD_OPT,
                                       loopdev[0]])
                if res != 0:
                    raise ImageCreationError("conversion failed")
                self.mount(imagetype, imagedir, self.MOUNT_PATH)
                self.__create_files_ext(self.MOUNT_PATH)
            else:
                self.__create_files_ext(self.MOUNT_PATH)
                self.__create_files_deleted(self.MOUNT_PATH)

            # change owner of all files
            cmd = ['chown', str(uid) + ':' + str(gid), '-R', self.MOUNT_PATH]
            res = subprocess.call(cmd)
            if res != 0:
                raise ImageCreationError("changing file owner failed")

            # hash all created files and the image(s) itself
            print("creating file checksums ...", file=self.out)

            try:
                with open(hfname, 'a') as hf:
                    os.chown(hfname, uid, gid)

                    # hash all files
                    self.__md5sum_image(hf)

                    # unmount image(s) and detach loop device(s)
                    self.__cleanup(loopdev)

                    # hash the image(s)
                    print("creating image checksum ...", file=self.out)

                    hf.write("--------------------------------\n")
                    for f in filename:
                        hf.write(self.md5sum(f) + "  " + os.path.basename(f) + "\n")
            except Exception as e:
                print(e, file=sys.stderr)
                raise ImageCreationError("could not create md5 file")
        except:
            # in case of an exception, clean up and delete images
            self.__cleanup(loopdev)
            self.delete(imagetype, imagedir)
            raise

        return files

    ##
    # delete the created images for this type if they exist
    #
    # @param imagetype type of the image
    # @param ipath directory of the image
    # @throw ValueError if received an invalid parameter
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def delete(self, imagetype, ipath):
        if imagetype is None:
            raise ValueError("parameter must not be None")

        for f in self.__type_to_names(imagetype):
            try:
                os.remove(os.path.join(ipath, f))
            except OSError as e:
                print(e, file=sys.stderr)
                raise ImageCreationError("could not remove files")

    ##
    # mount the files of an image type
    #
    # @param imagetype type of the image
    # @param ipath directory of the image, if None, path has to point to a
    #        custom image (imagetype is a full path then)
    # @param mpath path where to mount
    # @throw ValueError if received an invalid parameter
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def mount(self, imagetype, ipath, mpath):
        if imagetype is None or mpath is None:
            raise ValueError("parameter must not be None")

        # create mountpoint
        if not os.path.exists(mpath):
            try:
                os.mkdir(mpath)
            except OSError as e:
                print(e, file=sys.stderr)
                raise ImageCreationError("could not create mount point")

        # is it a custom image?
        if ipath is None:
            files = (os.path.basename(imagetype), os.path.basename(imagetype) + ".md5")
            image = files[0]
        else:
            files = self.__type_to_names(imagetype)
            image = os.path.join(ipath, files[0])

        # mount with appropriate options
        cmd = ['mount']
        if imagetype == 'btrfs_zlib':
            cmd += ['-ocompress-force=zlib']
        elif imagetype == 'btrfs_lzo':
            cmd += ['-ocompress-force=lzo']
        cmd += [image, mpath]
        res = subprocess.call(cmd)
        if res != 0:
            raise ImageCreationError("mounting failed")

    ##
    # unmount the image
    #
    # @param mpath mount path of the image
    # @throw ValueError if received an invalid parameter
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    @staticmethod
    def umount(mpath):
        if mpath is None:
            raise ValueError("parameter must not be None")

        res = subprocess.call(['umount', mpath])
        if res != 0:
            raise ImageCreationError("unmounting failed")

    ##
    # mount raid images
    #
    # @param imagetype type of the image
    # @param ipath directory of the image
    # @param mpath path where to mount
    # @throw ValueError if received an invalid parameter
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def mount_raid(self, imagetype, ipath, mpath):
        if imagetype is None or mpath is None:
            raise ValueError("parameter must not be None")

        # create mountpoint
        if not os.path.exists(mpath):
            try:
                os.mkdir(mpath)
            except OSError as e:
                print(e, file=sys.stderr)
                raise ImageCreationError("could not create mount point")

        files = self.__type_to_names(imagetype)
        devs = list()

        # attach to loop device
        for i in range(0, 2):
            try:
                loopdev = subprocess.check_output(['losetup', '-f'],
                                                  universal_newlines=True)
            except subprocess.CalledProcessError as e:
                print(e, file=sys.stderr)
                raise ImageCreationError("no free loop device available")
            loopdev = loopdev.replace('\n', '')
            res = subprocess.call(['losetup', loopdev, os.path.join(ipath, files[i])])
            if res != 0:
                raise ImageCreationError("attaching to device failed")
            devs.append(loopdev)

        # mount with appropriate options
        cmd = ['mount', devs[0], mpath]
        res = subprocess.call(cmd)
        if res != 0:
            raise ImageCreationError("mounting failed")

        return tuple(devs)

    ##
    # unmount raid images
    #
    # @param mpath mount path of the image
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def umount_raid(self, mpath, loopdev):
        self.umount(mpath)

        if loopdev is not None:
            for d in loopdev:
                if d is not None:
                    res = subprocess.call(['losetup', '-d', d],
                                          stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
                    if res != 0:
                        raise ImageCreationError("releasing from device failed")

    ##
    # create the filenames from the image type
    #
    # @param imagetype type of the image
    # @return the created names, 1 or 2 for images and 1 for the hashfile
    #
    @staticmethod
    def __type_to_names(imagetype):
        if 'raid' in imagetype:
            names = [imagetype + '.1.img', imagetype + '.2.img']
        else:
            names = [imagetype + '.img']
        names.append(imagetype + ".img.md5")
        return tuple(names)

    ##
    # create container image for file system
    #
    # @param fname filename of the image
    # @param size size of the image
    # @throw ImageCreationError if something went wrong
    # @return loop-device of filesystem image
    #
    def __create_image(self, fname, size, uid, gid):
        print("creating image ...", file=self.out)

        try:
            with open(fname, 'w') as img:
                img.truncate(size * 1024 ** 3)
        except IOError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create image")

        try:
            os.chown(fname, uid, gid)
        except OSError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not change user of image:")

        # attach to loop device
        try:
            loopdev = subprocess.check_output(['losetup', '-f'],
                                              universal_newlines=True)
        except subprocess.CalledProcessError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("no free loop device available")
        loopdev = loopdev.replace('\n', '')
        res = subprocess.call(['losetup', loopdev, fname])
        if res != 0:
            raise ImageCreationError("attaching to device failed")

        return loopdev

    ##
    # cleanup function to unmount and free the loop devices
    #
    # @param loopdev tuple of loop devices
    # @return None
    #
    def __cleanup(self, loopdev):
        print("cleaning up", file=self.out)
        subprocess.call(['umount', self.MOUNT_PATH], stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)

        for d in loopdev:
            if d is not None:
                subprocess.call(['losetup', '-d', d],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

    ##
    # create generic file
    #
    # @param path file creation director
    # @param fname filename
    # @param bsize size of the file in bytes
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    @staticmethod
    def __create_raw_file(path, fname, bsize):
        lines = (bsize - 5) // 80
        padding = (bsize - 5) % 80

        try:
            with open(os.path.join(path, fname), 'a') as f:
                if bsize > 5:
                    for i in range(0, lines):
                        f.write('{:0<79}'.format(str(i + 1) + ' ') + '\n')
                    for i in range(0, padding):
                        f.write('-')
        except IOError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create file")

    ##
    # create inline file
    #
    # @param path file creation directory
    # @param fname filename
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_inline_file(self, path, fname):
        print("creating inline file", file=self.out)
        self.__create_raw_file(path, fname, 400)

    ##
    # create standard file
    #
    # @param path file creation directory
    # @param fname filename
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_file(self, path, fname):
        print("creating standard file", file=self.out)
        self.__create_raw_file(path, fname, 1 * (1024 ** 2))

    ##
    # create big file
    #
    # @param path file creation directory
    # @param fname filename
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_big_file(self, path, fname):
        if self.f_fast:
            return
        else:
            print("creating big file ...", file=self.out)
            self.__create_raw_file(path, fname, 1124 * (1024 ** 2))

    ##
    # create file with long name
    #
    # @param path file creation directory
    # @throw ImageCreationError if something went wrong
    # @return None
    #

    def __create_long_file(self, path):
        print("creating long file name", file=self.out)
        self.__create_file(path, "this_is_a_file_with_a_very_long_file_name_44"
                                 "_this_is_a_file_with_a_very_long_file_name_89"
                                 "_this_is_a_file_with_a_very_long_file_name_135"
                                 "_this_is_a_file_with_a_very_long_file_name_181"
                                 "_this_is_a_file_with_a_very_long_file_name_227"
                                 "_this_is_a_file_with_an_EOF")

    ##
    # create hardlink
    #
    # @param path file creation directory
    # @param lname linkname
    # @param fname file to be linked
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_hardlink(self, path, lname, fname):
        print("creating hardlink", file=self.out)
        try:
            p = os.getcwd()
            os.chdir(path)
            os.link(fname, os.path.join(path, lname))
            os.chdir(p)
        except OSError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create hardlink")

    ##
    # create softlink
    #
    # @param path file creation directory
    # @param lname linkname
    # @param fname file to be linked
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_symlink(self, path, lname, fname):
        print("creating symlink", file=self.out)
        try:
            p = os.getcwd()
            os.chdir(path)
            os.symlink(fname, os.path.join(path, lname))
            os.chdir(p)
        except OSError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create symlink")

    ##
    # create block device
    #
    # @param path file creation directory
    # @param dname device name
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_block_device(self, path, dname):
        print("creating block device", file=self.out)
        try:
            os.mknod(os.path.join(path, dname), 0o600 | stat.S_IFBLK)
        except OSError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create block device")

    ##
    # create char device
    #
    # @param path file creation directory
    # @param dname device name
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_char_device(self, path, dname):
        print("creating character device", file=self.out)
        try:
            os.mknod(os.path.join(path, dname), 0o600 | stat.S_IFCHR)
        except OSError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create char device")

    ##
    # create named fifo
    #
    # @param path file creation directory
    # @param fname fifo name
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_named_fifo(self, path, fname):
        print("creating named fifo", file=self.out)
        try:
            os.mkfifo(os.path.join(path, fname))
        except OSError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create fifo")

    ##
    # create named socket
    #
    # @param path file creation directory
    # @param sname socket name
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_named_socket(self, path, sname):
        print("creating named socket", file=self.out)
        try:
            s = socket.socket(socket.AF_UNIX)
            s.bind(os.path.join(path, sname))
        except socket.error as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create socket")

    ##
    # create folder structure
    #
    # @param path folder creation directory
    # @param dname directory name
    # @param depth number of nested directories
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_folder_structure(self, path, dname, depth):
        print("creating folder structure", file=self.out)
        p = path
        for i in range(0, depth):
            p = os.path.join(p, dname)
        try:
            os.makedirs(p, 0o777, False)
        except OSError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create folder structure")

        self.__create_raw_file(p, "EOD", 100)

    ##
    # create sparse file
    #
    # @param path file creation directory
    # @param fname filename
    # @param size filesize
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_sparse_file(self, path, fname, size):
        print("creating sparse file", file=self.out)
        try:
            with open(os.path.join(path, fname), 'ab') as f:
                f.truncate(size)
        except IOError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create sparse file")

    ##
    # create reflink
    #
    # @param path file creation directory
    # @param lname linkname
    # @param fname file to be linked
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_reflink(self, path, lname, fname):
        print("creating reflink", file=self.out)
        try:
            p = os.getcwd()
            os.chdir(path)
            res = subprocess.call(['cp', '--reflink', fname, lname],
                                  stdout=subprocess.DEVNULL)
            if res != 0:
                raise ImageCreationError("could not create reflink")
            os.chdir(p)
        except OSError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create reflink")

    ##
    # create nested subvolumes
    #
    # @param path subvolume creation directory
    # @param vname subvolume name
    # @param depth number of nested subvolumes
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_subvolumes(self, path, vname, depth):
        print("creating subvolume structure", file=self.out)
        p = path
        for i in range(0, depth):
            p = os.path.join(p, vname)
            res = subprocess.call(['btrfs', 'subvolume', 'create', p],
                                  stdout=subprocess.DEVNULL)
            if res != 0:
                raise ImageCreationError("could not create subvolumes")

        self.__create_raw_file(p, "EOS", 100)

    ##
    # create a snapshot
    #
    # @param path snapshot creation directory
    # @param sname snapshot name
    # @param src snapshot source
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_snapshot(self, path, sname, src):
        print("creating snapshot", file=self.out)
        res = subprocess.call(['btrfs', 'subvolume', 'snapshot',
                               os.path.join(path, src),
                               os.path.join(path, sname)],
                              stdout=subprocess.DEVNULL)
        if res != 0:
            raise ImageCreationError("could not create snapshot")

    ##
    # modify file
    #
    # @param path file creation directory
    # @param fname filename
    # @param tag tag for identification
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __modify_file(self, path, fname, tag):
        print("modify file", file=self.out)
        try:
            with open(os.path.join(path, fname), 'a') as f:
                f.write("\n")
                f.write('{:^79}'.format(" MODIFICATION:" + tag + " "))
                f.write("\n")
        except IOError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not modify file")

        self.__create_raw_file(path, fname, 100 * (1024 ** 1))

    ##
    # create standard files
    # @details This function creates the standard files, directories and links,
    # which should be available on most of the current file systems.
    #
    # @param path directory where the files should be created
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_files_std(self, path):
        self.__create_inline_file(path, "file_inline")
        self.__create_file(path, "file")
        self.__create_big_file(path, "file_big")
        self.__create_long_file(path)
        self.__create_hardlink(path, "file_hardlink", "file")
        self.__create_symlink(path, "file_symlink", "file")
        self.__create_block_device(path, "block_device")
        self.__create_char_device(path, "char_device")
        self.__create_named_fifo(path, "named_fifo")
        self.__create_named_socket(path, "named_socket")
        self.__create_folder_structure(path, "directory_single", 1)
        self.__create_folder_structure(path, "directory", 5)  # TODO change (100?)
        self.__create_sparse_file(path, "sparse_file", 1024 ** 2)

    ##
    # create special files
    # @details This function creates special files, directories and links, which are
    # mostly only available on BTRFS file systems, like subvolumes and reflinks.
    #
    # @param path directory where the files should be created
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_files_ext(self, path):
        self.__create_reflink(path, "file_reflink", "file")
        self.__create_subvolumes(path, "subvolume_single", 1)
        self.__create_subvolumes(path, "subvolume", 5)
        self.__create_snapshot(path, "snapshot", "")
        self.__modify_file(path, "file_reflink", "reflink")
        self.__modify_file(path, "file", "file")

    ##
    # create deleted files
    # @details This function creates files and deletes them for recovery testing.
    #
    # @param path directory where the files should be created
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __create_files_deleted(self, path):
        self.__create_file(path, "file_deleted")
        try:
            os.remove(os.path.join(path, "file_deleted"))
            print("deleting file", file=self.out)
        except OSError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not delete file")

    ##
    # calculate md5 sums of all files
    #
    # @param path directory with content that should get hashed
    # @param hf all hashsums are written to this file
    # @throw ImageCreationError if something went wrong
    # @return None
    #
    def __md5sum_image(self, hf):
        for root, dirs, files in os.walk(self.MOUNT_PATH):
            for fname in files:
                s = os.stat(os.path.join(root, fname)).st_mode

                # do not try to hash if file is a device, socket or pipe
                if (stat.S_ISBLK(s) or stat.S_ISCHR(s) or
                        stat.S_ISFIFO(s) or stat.S_ISSOCK(s)):
                    continue

                res = self.md5sum(os.path.join(root, fname))
                rp = os.path.relpath(os.path.join(root, fname), self.MOUNT_PATH)
                hf.write(res + " " + rp + "\n")

    ##
    # calculate md5 sum
    #
    # @param fname name of file to hash
    # @throw ImageCreationError if something went wrong
    # @return the md5 sum in hex digits
    #
    @staticmethod
    def md5sum(fname):
        hashsum = hashlib.md5()
        try:
            with open(fname, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hashsum.update(chunk)
        except IOError as e:
            print(e, file=sys.stderr)
            raise ImageCreationError("could not create md5 sum of file")

        return hashsum.hexdigest()


# start the program
if __name__ == '__main__':
    main()
