#!/usr/bin/python3
################################################################################
# @file textparser.py
# @author Gerhard Hechenberger <gerhard.hechenberger@student.tuwien.ac.at>
# @date 2016-10-22
# @version 1.0
#
# @brief process and organize shell output of different tools
# @details This class can be used to process the output of various Linux and TSK
# shell tools. Precisely, it can take the output of fls to extract the file
# names, the output of ils to organize the meta data and the output of stat
# to do the same. Additionally, it filters and removes some not matching or
# unnecessary data.
################################################################################

import os


##
# class used to parse various tool output
#
class TextParser:
    fix_subvols = False
    ignore_ext_backup = True

    ##
    # constructor
    #
    # @param ignore_ext_backup ignore the backup directory created during
    #        conversion in tsk
    # @param fix_subvolumes ignore the snapshotted subvolume content in tsk
    # @return a new instance of this class
    #
    def __init__(self, ignore_ext_backup, fix_subvols):
        self.ignore_ext_backup = ignore_ext_backup
        self.fix_subvols = fix_subvols

    ##
    # parse fls -r -m / output
    # @details This function parses the output of TSKs fls tool. It splits up
    # the different parts, filters and converts some values and rearranges
    # them as a list.
    #
    # @param data raw output of fls tool to process
    # @return list of contained files
    #
    def parse_fls_files(self, data):
        files = list()
        data = data.decode('utf-8')
        # split in elements
        for line in data.splitlines():
            line = line.split('|')
            # filter empty lines and special TSK directories
            if len(line) > 1 and not line[1][1] == '$':
                # fix snapshot - subvolume behaviour if desired
                if self.fix_subvols:
                    if "snapshot" in line[1] and line[1].count("subvolume") > 0:
                        continue
                # do not test the content of the ext backup directory
                if self.ignore_ext_backup:
                    if "ext2_saved" in line[1]:
                        continue
                # convert symlink representation
                if line[3][0] == 'l':
                    end = line[1].find(' -> ')
                    line[1] = line[1][1:end]
                else:
                    line[1] = line[1][1:]
                files.append([line[1], int(line[2])])
        return files
    
    ##
    # parse ils -a output
    # @details This function parses the output of TSKs ils tool. It splits up
    # the different parts, filters and converts some values and rearranges
    # them as a list.
    #
    # @param data raw output of ils tool to process
    # @return list of contained inodes
    #
    @staticmethod
    def parse_ils(data):
        inodes = dict()
        data = data.decode('utf-8')
        # split in elements
        for line in data.splitlines():
            line = line.split('|')
            # filter no inode lines, 0-value inode lines and special TSK 
            # directory inode lines
            if line[0].isdigit() and line[0] != '0' and line[8] != '0':
                # convert numbers to integers
                intline = list()
                for i in line:
                    try:
                        intline.append(int(i))
                    except ValueError:
                        intline.append(i)
                inodes[intline[0]] = intline[1:]
        return inodes
    
    ##
    # parse stat -c '%n|%i|a|%u|%g|%Y|%X|%Z|%W|%a|%h|%s' output
    # @details This function parses the output of the stat tool. It splits up
    # the different parts, filters and converts some values and rearranges
    # them as a list.
    #
    # @param data raw output of stat tool to process
    # @param mpath mount path of the image to create relative paths
    # @return list of contained inodes
    #
    def parse_stat(self, data, mpath=None):
        inodes = list()
        data = data.decode('utf-8')
        # split in elements
        for line in data.splitlines():
            line = line.split('|')
            # fix snapshot - subvolume behaviour if desired
            if self.fix_subvols:
                if "snapshot" in line[0] and line[0].count("subvolume") > 0:
                    continue
            # do not test the content of the ext backup directory
            if self.ignore_ext_backup:
                if "ext2_saved" in line[0]:
                    continue
            # convert numbers to integers
            intline = list()
            for i in line:
                try:
                    intline.append(int(i))
                except ValueError:
                    intline.append(i)
            inodes.append(intline)
        # set relative path
        if mpath is not None:
            for line in inodes:
                line[0] = os.path.relpath(line[0], mpath)
        return inodes
