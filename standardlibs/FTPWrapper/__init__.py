'''
Allows for easy to use FTP operations.  Includes sFTP and FTPes as well.

@author: chrcoe
'''
import ftplib
import logging
import os

from standardlibs.Decorators import retry
import paramiko


class FTPWrapper(object):

    '''
    This class provides a basic FTP module which allows for sending files
    programmatically.  This class handles SSH over FTP (sFTP), FTP and
    FTP with TLS (FTPes).
    '''

    def __init__(self, host, user, passwd, *, path=None,
                 is_ftp_tls=False, is_secure_ftp=False, time_to_live=60):
        '''
        Constructor - this holds all FTP related settings and operations for
        processing individual files as needed.

        @param host: the FTP host address
        @param is_secure_ftp: is the FTP host using SSH over FTP?
        @param user: encrypted username for FTP account
        @param passwd: encrypted password for FTP account
        @param path: the path on the FTP host to store the file (if any)
        @param is_ftp_tls: send via FTP over TLS ? (default: False)
        @param time_to_live: how long to wait when creating connection,
            Default: 60 seconds
        '''
        self.__root_logger = logging.getLogger('rootLogger')
        self.__smtp_logger = logging.getLogger('smtpLogger')

        self.__host = host
        self.__is_ssh_ftp = is_secure_ftp
        self.__usrname = user  # stored encrypted, need to decrypt
        self.__passwd = passwd  # stored encrypted, need to decrypt
        self.__port = 22  # for SFTP
        self.__path = path
        self.__is_ftp_tls = is_ftp_tls
        self.__time_to_live = time_to_live

    # pylint: disable=broad-except
    # other exceptions are explicitly caught but if there is a remaining
    # exception, it needs to be logged
    @retry(5)
    def send_file(self, file_to_post, *, name_override=None):
        '''
        This method will take in a file to post via FTP.  This will use this
        OBT's information to connect and send the file.

        @param file_to_post: the path to the file to be posted via FTP, raises
            FileNotFoundError if file is NoneType
        @param name_override: if present, this name will be what is used to
            save the file on the FTP host, else file_to_post will be used

        @return: boolean based on success/failure
        '''

        if file_to_post is None:
            self.__root_logger.critical(
                'Tried to send NoneType file to host'
                + 'The file could have failed encryption.')
            self.__smtp_logger.critical(
                'Tried to send NoneType file to host'
                + 'The file could have failed encryption.', exc_info=True)
            raise FileNotFoundError
#             return False
        # if file_to_post is None, then it CANNOT be used here so need to check
        # that first!
        if name_override is None:
            name_override = os.path.basename(file_to_post)
        else:
            name_override = name_override.lower()

        in_basename = os.path.basename(file_to_post)

        try:
            if self.__is_ssh_ftp:
                self.__send_ssh(file_to_post, name_override)
            elif self.__is_ftp_tls:
                self.__send_tls(file_to_post, name_override)
            else:
                self.__send_clear(file_to_post, name_override)
        # catch ftplib specific problems
        except ftplib.error_reply as ex:
            self.__root_logger.critical(
                ('error while sending file to host '
                 '(unexpected reply): {}').format(in_basename)
            )
            self.__smtp_logger.critical(
                ('error while sending file to host '
                 '(unexpected reply): {}\n\n{}').format(in_basename, ex),
                exc_info=True
            )
            return False
        except ftplib.error_temp as ex:
            self.__root_logger.info(
                ('error while sending file to host '
                 '(temporary error): {}').format(in_basename)
            )
            self.__smtp_logger.debug(
                ('error while sending file to host '
                 '(temporary error): {}\n').format(in_basename)
            )
            return False
        except ftplib.error_perm as ex:
            self.__root_logger.critical(
                ('error while sending file to host '
                 '(permanent error - check '
                 'credentials): {}').format(in_basename)
            )
            self.__smtp_logger.critical(
                ('error while sending file to host '
                 '(permanent error - check '
                 'credentials): {}\n\n{}').format(in_basename, ex),
                exc_info=True
            )
            return False
        except ftplib.error_proto as ex:
            self.__root_logger.critical(
                ('error while sending file to host '
                 '(protocol error): {}').format(in_basename)
            )
            self.__smtp_logger.critical(
                ('error while sending file to host '
                 '(protocol error): {}\n\n{}').format(in_basename, ex),
                exc_info=True
            )
            return False
        except ftplib.all_errors as ex:
            self.__root_logger.critical(
                ('error while sending file to host '
                 '(ftplib): {}').format(in_basename)
            )
            self.__smtp_logger.critical(
                ('error while sending file to host '
                 '(ftplib): {}\n\n{}').format(in_basename, ex),
                exc_info=True
            )
            return False
        # catch everything else that is not related to the ftplib code
        except Exception as ex:
            self.__root_logger.critical(
                ('error while sending file to host '
                 '(non-FTP error): {}').format(in_basename)
            )
            self.__smtp_logger.critical(
                ('error while sending file to host '
                 '(non-FTP error): {}\n\n{}').format(in_basename, ex),
                exc_info=True
            )
            return False
        else:
            self.__root_logger.info(
                'Finished FTP transfer to host: {}'.format(self.__host))
            return True

    def __send_tls(self, file_to_post, name_override):
        '''
        Handles sending files using the FTP over TLS method.
        '''
        with ftplib.FTP_TLS(host=self.__host,
                            user=self.__usrname,
                            passwd=self.__passwd,
                            timeout=self.__time_to_live) as ftp_es:
            ftp_es.login(user=self.__usrname, passwd=self.__passwd)
            ftp_es.prot_p()
            if self.__path is not None:
                ftp_es.cwd(self.__path)  # CD to the proper directory
            with open(file_to_post, 'rb') as file_:
                if name_override == 'multiple':
                    self.__root_logger.info(
                        'Initiated FTP transfer of {} to host: {}'.format(
                            os.path.basename(file_to_post), self.__host))
                    ftp_es.storbinary(
                        'STOR {}'.format(os.path.basename(file_to_post)),
                        file_)
                else:
                    self.__root_logger.info(
                        'Initiated FTP transfer of {} to host: {}'.format(
                            name_override, self.__host))
                    ftp_es.storbinary('STOR {}'.format(name_override),
                                      file_)

    def __send_ssh(self, file_to_post, name_override):
        '''
        Handles sending files using the SSH over FTP method.
        '''
        # Transport could raise OSError ...
        sftp_transport = paramiko.Transport((self.__host, self.__port))
        # connect could raise paramiko.ssh_exception.SSHException
        sftp_transport.connect(
            username=self.__usrname,
            password=self.__passwd)
        sftp = paramiko.SFTPClient.from_transport(sftp_transport)
        if self.__path is not None:
            sftp.chdir(path=self.__path)  # CD to the proper directory
        # open file for reading
        with open(file_to_post, 'rb') as file_:
            data = file_.read()
        # determine remoteFilename
        if name_override == 'multiple':
            self.__root_logger.info(
                'Initiated FTP transfer of {} to host: {}'.format(
                    os.path.basename(file_to_post), self.__host))
            remote_file_name = '{}'.format(
                os.path.basename(file_to_post))
        else:
            self.__root_logger.info(
                'Initiated FTP transfer of {} to host: {}'.format(
                    name_override, self.__host))
            remote_file_name = '{}'.format(name_override)
        # open remote file for writing
        with sftp.open(remote_file_name, 'wb') as file_:
            file_.write(data)
        # done writing remote file

        if sftp_transport:
            sftp_transport.close()

    def __send_clear(self, file_to_post, name_override):
        '''
        Handles sending files using clear FTP method.
        '''
        with ftplib.FTP(host=self.__host,
                        user=self.__usrname,
                        passwd=self.__passwd,
                        timeout=self.__time_to_live) as ftp_con:
            if self.__path is not None:
                ftp_con.cwd(self.__path)  # CD to the proper directory
            with open(file_to_post, 'rb') as file_:
                if name_override == 'multiple':
                    self.__root_logger.info(
                        'Initiated FTP transfer of {} to host: {}'.format(
                            os.path.basename(file_to_post), self.__host))
                    ftp_con.storbinary(
                        'STOR {}'.format(os.path.basename(file_to_post)),
                        file_)
                else:
                    self.__root_logger.info(
                        'Initiated FTP transfer of {} to host: {}'.format(
                            name_override, self.__host))
                    ftp_con.storbinary('STOR {}'.format(name_override), file_)

    @retry(5)
    def download_file(self):
        ''' Downloads a single file from the remote server. '''
        # TODO: implement this
        pass
