'''
@author: chrcoe
'''

from collections import deque
from datetime import datetime
import logging
import math
import os
import shutil
import time

from standardlibs.Decorators import retry


class FileQueue(object):

    '''
    FileQueue allows tracking files as they come in and manages moving them
    according to the file paths passed in during instantiation.
    '''

    def __init__(self, input_path, output_path, queue_path, archive_path):
        '''
        Creates a FileQueue object to track files coming in and going out.
        Instantiation ensures that these folders exist and sets up the queue
        accordingly.

        @param input_path: path where files are being put for processing
        @param output_path: path where files should ultimately be placed when
            finished
        @param queue_path: path where files should be stored while waiting to
            be processed
        '''

        self.__root_logger = logging.getLogger('rootLogger')
        self.__smtp_logger = logging.getLogger('smtpLogger')

        self.__input_path = input_path
        self.__queue_path = queue_path
        self.__archive_path = archive_path
        if output_path:
            self.__output_path = output_path
        else:
            # if output path is None, it will default to the archive directory
            self.__output_path = self.__archive_path

        if not self.__input_path:
            self.__root_logger.critical(('Input path was invalid, '
                                         'cannot be empty!'))
            raise ValueError('Input path cannot be empty!')
        if not self.__queue_path:
            self.__root_logger.critical(('Queue path was invalid, '
                                         'cannot be empty!'))
            raise ValueError('Queue path cannot be empty!')
        if not self.__archive_path:
            self.__root_logger.critical(('Archive path was invalid, '
                                         'cannot be empty!'))
            raise ValueError('Archive path cannot be empty!')

        os.makedirs(self.__input_path, exist_ok=True)
        os.makedirs(self.__queue_path, exist_ok=True)
        os.makedirs(self.__archive_path, exist_ok=True)
        os.makedirs(self.__output_path, exist_ok=True)

        # this is a queue which will hold the file locations as strings
        self.__q = deque([])

    def get_queue_path(self):
        ''' Returns the internally set queue_path. '''
        return self.__queue_path

    def set_queue_path(self, value):
        ''' Sets the internal queue_path and creates the directory. '''
        self.__queue_path = value
        os.makedirs(self.__queue_path, exist_ok=True)

    def get_archive_path(self):
        ''' Returns the internally set archive_path. '''
        return self.__archive_path

    def set_archive_path(self, value):
        ''' Sets the internal archive_path and creates the directory. '''
        self.__archive_path = value
        os.makedirs(self.__archive_path, exist_ok=True)

    # pylint: disable=broad-except
    # We need to catch all remaining exceptions if the file move fails.
    @retry(5)  # exponential backoff, 5 tries:-> 3,6,12,24,48 (seconds)
    def push(self, in_file):
        '''
        Puts the given file onto the queue_path and returns True if successful.

        @param in_file: the file to put onto the queue
        '''
        try:
            # take this file OUT of the PATH_INPUT
            src = in_file
            dst = os.path.join(os.path.dirname(in_file), self.__queue_path,
                               os.path.basename(in_file))
            # and put it INTO the QUEUE_PATH
            self.__root_logger.info(
                'Pushing file to FileQueue:\t{}'.format(os.path.basename(dst)))
            print('moving to QUEUE_PATH:\t', dst)
            # and store its location on the internal queue object

            self.__q.append(shutil.move(src, dst))
            return True
        except Exception:
            self.__root_logger.error(
                'Error during pushing file on to FileQueue')
            self.__smtp_logger.error(
                'Error during pushing file on to FileQueue', exc_info=True)
#             print(e)
            return False

    def pop(self, *, addtimestamp=True):
        '''
        Pops a file off of the queue and returns its path.  You have the option
        of adding a date/time stamp to the file name for archival reasons.

        @param addtimestamp: if true, adds a date/time stamp to the filename
            when saving it on the output_path
        '''
        # take a single file OUT of the QUEUE_PATH
        try:
            # get the file loc from the internal queue
            src = self.__q.popleft()
            file_name, file_ext = os.path.splitext(src)

            if addtimestamp:
                # timestamp
                timestamp = datetime.fromtimestamp(
                    time.time()).strftime('%Y%m%d_%H%M%S')
                stamped_src = '.'.join(('{filename}-{datetimestamp}'.format(
                    filename=os.path.basename(file_name),
                    datetimestamp=timestamp), file_ext[1:]))
            else:
                stamped_src = '.'.join(('{filename}'.format(
                    filename=os.path.basename(file_name)), file_ext[1:]))

            # and move to the PATH_OUTPUT
            dst = os.path.join(self.__output_path, stamped_src)
            print('just popped file')
            # move the file to output_path
            dst = shutil.move(src, dst)
            # archive it to the archive_path
            arc_dst = self.__archive_file(in_file=dst)
            if arc_dst:
                dst = arc_dst

            # return path of file
            return dst
        except IndexError:
            return None

    def check_dir(self):
        '''
        This will check the input_path directory for files.  If any files are
        found, it will push them onto the queue.
        '''
        is_new_file = False
        os.chdir(self.__input_path)
        # check if there is a file in PATH_INPUT
        for file_ in os.listdir(path=self.__input_path):
            if os.path.isfile(file_):
                self.__root_logger.info('File found:\t{}'.format(file_))
                # and PUSH it to the queue
                is_new_file = self.push(os.path.join(self.__input_path, file_))
        return is_new_file

    def __archive_file(self, in_file):
        '''
        Handles archiving the file.
        '''
        src = in_file
        dst = os.path.join(self.__archive_path,
                           os.path.basename(in_file))
        print('Archiving to:\t{}'.format(dst))
        self.__root_logger.info('Archiving to:\t{}'.format(dst))
        if src == dst:
            return shutil.move(src, dst)
        else:
            shutil.copyfile(src, dst)  # don't want to return anything here

    archive_path = property(get_archive_path, set_archive_path, None, None)
    queue_path = property(get_queue_path, set_queue_path, None, None)
