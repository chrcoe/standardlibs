'''
Tests for the FileQueue module.

@author: chrcoe
'''
import os
import shutil
import unittest

from standardlibs.FileQueue import FileQueue

# pylint: disable=too-many-public-methods
# A UNIT test will have as many methods as needed to complete testing.


class FileQueueTest(unittest.TestCase):

    ''' Tests FileQueue class. '''

    def setUp(self):
        ''' Sets up each test. '''
        self.base_dir = os.path.join(
            os.path.dirname(__file__), 'test_filequeue')
        self.input_path = os.path.join(
            self.base_dir, 'test_filequeue_input')
        self.output_path = os.path.join(
            self.base_dir, 'test_filequeue_output')
        self.queue_path = os.path.join(
            self.base_dir, 'test_filequeue_queue')
        self.archive_path = os.path.join(
            self.output_path, 'test_filequeue_archive')

    def tearDown(self):
        ''' Tears down each test. '''
        shutil.rmtree(self.base_dir, ignore_errors=True)
#         pass

    def test_constructor(self):
        ''' Does the constructor ensure the given directories exist? '''

#         shutil.rmtree(self.base_dir, ignore_errors=True)

#         self.assertFalse(os.path.isdir(self.input_path))
        self.assertFalse(os.path.isdir(self.output_path))
        self.assertFalse(os.path.isdir(self.queue_path))

        file_q = FileQueue(
            self.input_path, self.output_path, self.queue_path,
            self.archive_path)
        self.assertIsNotNone(file_q)
        self.assertTrue(os.path.isdir(self.input_path))
        self.assertTrue(os.path.isdir(self.output_path))
        self.assertTrue(os.path.isdir(self.queue_path))
        self.assertTrue(os.path.isdir(self.archive_path))

#         shutil.rmtree(self.base_dir)

    def test_push_valid(self):
        ''' When pushing a file is it moved the queue_path and return True? '''
        # create FileQueue
        file_q = FileQueue(
            self.input_path, self.output_path, self.queue_path,
            self.archive_path)
        # create test file to push
        test_file = os.path.join(self.input_path, 'test_file.txt')
        with open(test_file, 'w') as file_:
            file_.write('test text')
        self.assertTrue(os.path.isfile(test_file))

        # test valid case
        result = file_q.push(test_file)
        self.assertTrue(result)
        queue_file = os.path.join(self.queue_path, os.path.basename(test_file))
        self.assertTrue(os.path.isfile(queue_file))
        self.assertFalse(os.path.isfile(test_file))

#         shutil.rmtree(self.base_dir)

    def test_push_invalid(self):
        ''' When passing in an invalid file, or one that is already open,
        does it raise Exception after going through exponential backoff? '''
        # create FileQueue
        file_q = FileQueue(
            self.input_path, self.output_path, self.queue_path,
            self.archive_path)
        # test invalid case
        test_file = os.path.join(self.input_path, 'test_file.txt')
        self.assertFalse(os.path.isfile(test_file))

        with self.assertRaises(Exception):
            file_q.push(test_file)

#         self.assertFalse(result)

#         shutil.rmtree(self.base_dir)

    def test_pop_valid(self):
        ''' When popping a file, is it moved from the queue_path to the
        output_path and return the new file path? '''
        # create FileQueue
        file_q = FileQueue(
            self.input_path, self.output_path, self.queue_path,
            self.archive_path)
        # create test file and push to the queue
        test_file = os.path.join(self.input_path, 'test_file.txt')
        with open(test_file, 'w') as file_:
            file_.write('test text')
        file_q.push(test_file)

        # test WITH timestamp (standard)
        out_file = file_q.pop()
        self.assertTrue(os.path.isfile(out_file))
        archive_file = os.path.join(
            self.archive_path, os.path.basename(out_file))
        self.assertTrue(os.path.isfile(out_file))
        self.assertTrue(os.path.isfile(archive_file))

        self.assertNotEqual(
            os.path.basename(out_file), os.path.basename(test_file))
        self.assertEqual(os.path.dirname(out_file), self.output_path)
        queue_file = os.path.join(self.queue_path, os.path.basename(test_file))
        self.assertFalse(os.path.isfile(queue_file))
        self.assertFalse(os.path.isfile(test_file))

        with open(test_file, 'w') as file_:
            file_.write('test text')
        file_q.push(test_file)

        # test WITHOUT timestamp
        out_file = file_q.pop(addtimestamp=False)
        self.assertTrue(os.path.isfile(out_file))
        self.assertTrue(
            os.path.isfile(os.path.join(self.output_path, 'test_file.txt')))
        self.assertTrue(
            os.path.isfile(os.path.join(self.archive_path, 'test_file.txt')))

        self.assertEqual(
            os.path.basename(out_file), os.path.basename(test_file))

        self.assertEqual(os.path.dirname(out_file), self.output_path)
        queue_file = os.path.join(self.queue_path, os.path.basename(test_file))
        self.assertFalse(os.path.isfile(queue_file))
        self.assertFalse(os.path.isfile(test_file))

#         shutil.rmtree(self.base_dir)

    def test_pop_invalid(self):
        ''' When popping a file that is not on the queue, does it return
        None? '''
        # create FileQueue
        file_q = FileQueue(
            self.input_path, self.output_path, self.queue_path,
            self.archive_path)

        test_file = os.path.join(self.input_path, 'test_file.txt')
        self.assertFalse(os.path.isfile(test_file))

        out_file = file_q.pop()  # nothing on the queue, should return None
        self.assertIsNone(out_file)
        queue_file = os.path.join(self.queue_path, os.path.basename(test_file))
        self.assertFalse(os.path.isfile(queue_file))
        self.assertFalse(os.path.isfile(test_file))

#         shutil.rmtree(self.base_dir)

    def test_check_dir(self):
        ''' Does it check the input directory as expected? Does this push all
        files found to the queue_path? '''
        # create FileQueue
        file_q = FileQueue(
            self.input_path, self.output_path, self.queue_path,
            self.archive_path)
        # create test file and push to the queue
        test_file = os.path.join(self.input_path, 'test_file.txt')
        with open(test_file, 'w') as file_:
            file_.write('test text')
        self.assertTrue(os.path.isfile(test_file))
        file_q.check_dir()  # checks the input_path for any files and pushes
        # them should have one item on it and it should be the test_file but it
        # should be on the queue
        queue_file = os.path.join(self.queue_path, os.path.basename(test_file))
        self.assertTrue(os.path.isfile(queue_file))
        self.assertFalse(os.path.isfile(test_file))
        with open(queue_file, 'r') as file_:
            line = file_.read()
            self.assertEqual(line, 'test text')

#         shutil.rmtree(self.base_dir)

    def test_negative_paths(self):
        ''' Negative test INPUT, QUEUE and ARCHIVE paths individually. '''
        # check INPUT
        with self.assertRaises(ValueError):
            FileQueue(None, self.output_path, self.queue_path,
                      self.archive_path)
        # check QUEUE
        with self.assertRaises(ValueError):
            FileQueue(self.input_path, self.output_path, None,
                      self.archive_path)
        # check ARCHIVE
        with self.assertRaises(ValueError):
            FileQueue(self.input_path, self.output_path, self.queue_path,
                      None)

    def test_empty_output_path(self):
        ''' If no output path specified, does it change the archive
        location? '''
        file_q = FileQueue(self.input_path, None, self.queue_path,
                           self.archive_path)

        test_file = os.path.join(self.input_path, 'test_file.txt')
        with open(test_file, 'w') as file_:
            file_.write('test text')

        file_q.check_dir()
        # if output Path is none, the files would show up in the archive path
        self.assertFalse(os.path.isfile(test_file))
        base_name = os.path.basename(test_file)
        # in queue now
        self.assertTrue(
            os.path.isfile(os.path.join(self.queue_path, base_name)))
        # pop file
        output = file_q.pop()
        self.assertEqual(
            os.path.join(self.archive_path, os.path.basename(output)), output)

    def test_output_archive_same(self):
        ''' Tests when output and archive directory are explicitly set to
        the same path. '''
        file_q = FileQueue(self.input_path, self.archive_path, self.queue_path,
                           self.archive_path)

        test_file = os.path.join(self.input_path, 'test_file.txt')
        with open(test_file, 'w') as file_:
            file_.write('test text')

        file_q.check_dir()
        # if output Path is none, the files would show up in the archive path
        self.assertFalse(os.path.isfile(test_file))
        base_name = os.path.basename(test_file)
        # in queue now
        self.assertTrue(
            os.path.isfile(os.path.join(self.queue_path, base_name)))
        # pop file
        output = file_q.pop(addtimestamp=False)
        self.assertEqual(os.path.join(self.archive_path, base_name), output)

    def test_properties(self):
        ''' Test all properties '''
        file_q = FileQueue(
            self.input_path, self.output_path, self.queue_path,
            self.archive_path)

        # getters
        self.assertEqual(self.queue_path, file_q.queue_path)
        self.assertEqual(self.archive_path, file_q.archive_path)

        # setters
        new_queue_path = os.path.join(
            self.base_dir, 'test_filequeue_new_queue')
        new_archive_path = os.path.join(
            self.output_path, 'test_filequeue_new_archive')

        self.assertFalse(os.path.isdir(new_queue_path))
        self.assertFalse(os.path.isdir(new_archive_path))

        file_q.queue_path = new_queue_path
        self.assertTrue(os.path.isdir(new_queue_path))
        self.assertEqual(new_queue_path, file_q.queue_path)

        file_q.archive_path = new_archive_path
        self.assertTrue(os.path.isdir(new_archive_path))
        self.assertEqual(new_archive_path, file_q.archive_path)

if __name__ == "__main__":
    unittest.main()
