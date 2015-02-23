'''
Provides a wrapper around the system GnuPG/PGP installation.

@author: chrcoe
'''
import logging
import os
from subprocess import Popen, PIPE


class PGPWrapper(object):

    '''
    Provides a wrapper for the GnuPG program which must be installed on the
    system utilizing this code.
    '''

    def __init__(self):
        '''
        Sets up the PGPWrapper.
        '''

        self.__root_logger = logging.getLogger('rootLogger')
        self.__smtp_logger = logging.getLogger('smtpLogger')

        self.__enc_addr = ''
        self.__private_key = ''
        self.__passwd = ''

    # pylint: disable=lost-exception
    # pylint: disable=broad-except
    # this is fine because the exception is being logged so the process
    # can continue
    def encrypt_file(self, clear_file, public_key):
        '''
        @attention: NEED to set GNUPGHOME environment variable to: C:\.gnupg\
            and copy over pubring.gpg and secring.gpg
        @precondition: the Recipient's public key must already be stored in the
            public keyring
        @postcondition: the text will be encrypted and can only be decrypted
            using that person's private key

        Takes in a file in clear text and encrypts it using the passed in
        signature name/ID.

        Sample usage:
        clear_file = "test.txt"
        helpers.encrypt_file(clear_file,"email@test.com")
        --> outfile file is stored in "test.txt.pgp"

        @param clear_file: path to file for encryption
        @param public_key: The recipient key to use for encryption

        @return path to encrypted file
        '''
        self.__enc_addr = public_key

        if self.__enc_addr is None or self.__enc_addr == '':
            return None

#        rootLogger = logging.getLogger('rootLogger')
#        smtpLogger = logging.getLogger('smtpLogger')
        self.__root_logger.info(
            'Started encryption of %s for %s',
            os.path.basename(clear_file),
            self.__enc_addr
        )

        out_file = '{}/{}.pgp'.format(
            os.path.dirname(clear_file),
            os.path.basename(clear_file)
        )

        try:
            args = "gpg2 --yes --trust-model always -o " \
                + "\"{outfile}\" -er {encaddr} \"{infile}\"".format(
                    outfile=out_file, encaddr=self.__enc_addr,
                    infile=clear_file
                )
            proc = Popen(
                args, stdout=PIPE, stderr=PIPE, universal_newlines=True)
            proc.wait()
            # opens up communication with the process
            err = proc.communicate()[1]
            if proc.returncode != 0:
                # and finds out what the error is
                gpg_error = err.splitlines()[0]
                # then it adds this error to the log file
                raise Exception
            else:
                self.__root_logger.info(
                    'Finished encryption of {} for {}'.format(
                        os.path.basename(clear_file), self.__enc_addr)
                )
        except Exception as ex:
            print(ex)
            self.__root_logger.error('Encryption Failed: {}'.format(gpg_error))
            self.__smtp_logger.error(
                'Encryption Failed: {}\n{}'.format(
                    gpg_error, ex), exc_info=True)
            out_file = None
        finally:
            proc.kill()
            return out_file

    def decrypt_file(self, encrypted_file, *, private_key='admin@ts4.com',
                     passwd=None):
        r'''
        @attention: NEED to set GNUPGHOME environment variable to: C:\.gnupg\
            and copy over pubring.gpg and secring.gpg
        @precondition: The private key must be stored in the secret keyring
            on the machine running the hrfeed
        @postcondition: The text will be decrypted and returned

        Takes in an encrypted file and decrypts it using the passed in
        signature file.  This method utilizes tools from the GnuPG windows
        package "GPG4WIN".


        Sample usage:
        encrypted_file = 'test2.txt.pgp'
        h.decrypt_file(encrypted_file, 'admin@ts4.com')

        @param encrypted_file: path to file for decryption
        @param private_key: ID to use for decryption: this uses
            the private key
        @param passwd: the ENCRYPTED password, if any, for the private_key

        @return: path to decrypted file
        '''
        self.__private_key = private_key
        self.__passwd = passwd

#         logger = logging.getLogger(__name__)

#        __root_logger = logging.getLogger('__root_logger')
#        __smtp_logger = logging.getLogger('__smtp_logger')
        self.__root_logger.info('Started decryption of {} for {}'.format(
            os.path.basename(encrypted_file),
            self.__private_key))

        # dynamically decides what to call the DECRYPTED file, regardless of
        # the extensions passed in
        head, tail = os.path.split(encrypted_file)
        ext_list = tail.split(os.extsep)
        base_file_name = ext_list[0]
        out_file = os.path.join(
            head, '{}-DECRYPTED.txt'.format(base_file_name))

        try:
            # this allows specifying the output file
            if self.__passwd is not None:
                args = ("gpg2 --batch --yes --passphrase \"{passwd}\" "
                        "-o \"{outfile}\" -du {privkey} \"{infile}\"")
                args = args.format(
                    passwd=self.__passwd,
                    outfile=out_file,
                    privkey=self.__private_key,
                    infile=encrypted_file
                )
            else:
                args = ("gpg2 --batch -o \"{outfile}\" -du {privkey} "
                        "\"{infile}\"")
                args = args.format(
                    outfile=out_file,
                    privkey=self.__private_key,
                    infile=encrypted_file
                )
            # this will remove the gpg or pgp extension by default

            # call the gpg2 process and pipe the stderr output back
            proc = Popen(
                args, stdout=PIPE, stderr=PIPE, universal_newlines=True)
            proc.wait()
            err = proc.communicate()[1]
            if proc.returncode != 0:
                # communication with the process and finds out what the error
                # is
                gpg_error = err.splitlines()
                # then it adds this error to the log file
                raise Exception
            else:
                self.__root_logger.info('Finished decryption of '
                                        + '{} for {}'.format(
                                            os.path.basename(encrypted_file),
                                            self.__private_key))
        except Exception as ex:
            if len(gpg_error) == 3:
                # this could be because you do not have the private key for the
                # file you are trying to decrypt
                self.__root_logger.error('Decryption Failed: {error}'.format(
                    error=gpg_error[2]))
                self.__smtp_logger.error(
                    'Decryption Failed: {error}'.format(
                        error=gpg_error[2]), exc_info=True)
            else:
                # this is normally due to invalid file
                self.__root_logger.error(
                    'Decryption Failed: {}'.format(gpg_error[0]))
                self.__smtp_logger.error(
                    'Decryption Failed: {}'.format(gpg_error[0]),
                    exc_info=True
                )
            print(ex)
            out_file = None
        finally:
            proc.kill()
            return out_file
