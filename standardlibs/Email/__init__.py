'''
This provides email creation and sending.

@author: chrcoe

'''
import base64
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate, formataddr
import logging
import os
from smtplib import SMTPException, SMTPAuthenticationError
import smtplib
import time
try:
    import sspi
except ImportError:
    pass

SMTP_EHLO_OKAY = 250
SMTP_AUTH_CHALLENGE = 334
SMTP_AUTH_OKAY = 235


class Email(object):

    '''
    Allows creating and sending Email messages.
    '''

    # pylint: disable=too-many-instance-attributes
    # Twelve is reasonable in this case.

    def __init__(self, smtp_host, smtp_port, *,
                 is_exchange_server=False, smtp_usr=None,
                 smtp_passwd=None, use_smtp_tls=False, smtp_timeout=30):
        '''
        Sets up the Email object with all SMTP information required.

        @param smtp_host: the SMTP server to send email from
        @param smtp_port: the SMTP port of the server
        @param is_exchange_server: If true, it will authenticate with the
            local exchange server via NTLM authentication
        @param smtp_usr: if not using an exchange server, this should be
            populated the username to authenticate as
        @param smtp_passwd: if not using an exchange server, this should be
            populated the password for authentication
        @param use_smtp_tls: if not using an exchange server, should Email()
            try to setup TLS?  Check the SMTP server configs to find out
        @param smtp_timeout: the length in seconds to wait before timing out
        '''

        self.__root_logger = logging.getLogger('__root_logger')
        self.__smtp_logger = logging.getLogger('__smtp_logger')

        self.__exchange = is_exchange_server
        self.__smtp_host = smtp_host
        self.__smtp_port = smtp_port
        self.__smtp_timeout = smtp_timeout
        self.__smtp_usr = smtp_usr
        self.__smtp_passwd = smtp_passwd
        self.__use_smtp_tls = use_smtp_tls

        self.__full_recipients = None
        self.__msg = None
        self.__sender = None
        self.__sender_name_override = None

    def __asbase64(self, msg):
        ''' Encodes a message in base64 and then converts it to a string. '''
        return (base64.b64encode(msg)).decode("utf-8")

    def __connect_to_exchange(self, smtp):
        '''
        Connects to an exchange server for SMTP authentication.  This uses NTLM
        method which attempts to authenticate as the currently logged in user.

        This means whatever account is used to run this process must have
        access to the exchange server for sending email.

        Example:
        >>> import smtplib
        >>> smtp = smtplib.SMTP("my.smtp.server")
        >>> __connect_to_exchange(smtp)
        '''
        # NTLM Guide -- http://curl.haxx.se/rfc/ntlm.html

        # Send the SMTP EHLO command
        code, response = smtp.ehlo()
        if code != SMTP_EHLO_OKAY:
            raise SMTPException(
                "Server did not respond as expected to EHLO command")

        sspiclient = sspi.ClientAuth('NTLM')  # login as current user

        # Generate the NTLM Type 1 message
        sec_buffer = None
        err, sec_buffer = sspiclient.authorize(sec_buffer)
        ntlm_message = self.__asbase64(sec_buffer[0].Buffer)

        # Send the NTLM Type 1 message -- Authentication Request
        code, response = smtp.docmd("AUTH", "NTLM " + ntlm_message)

        # Verify the NTLM Type 2 response -- Challenge Message
        if code != SMTP_AUTH_CHALLENGE:
            raise SMTPException(
                "Server did not respond as expected to NTLM negotiate message")

        # Generate the NTLM Type 3 message
        err, sec_buffer = sspiclient.authorize(base64.decodestring(response))
        ntlm_message = self.__asbase64(sec_buffer[0].Buffer)

        if err:
            self.__root_logger.warning(('Error while authenticating to '
                                        'exchange server'))

        # Send the NTLM Type 3 message -- Response Message
        code, response = smtp.docmd("", ntlm_message)
        if code != SMTP_AUTH_OKAY:
            raise SMTPAuthenticationError(code, response)

    def create_mail(self, subject, *, html=None, text=None,
                    recip_list=[], cc_list=None, bcc_list=None, files=[],
                    sender=None, sender_name_override=None):
        '''
        Prepares a message for sending at a later time. The message is
        stored as an object inside this Email() object.  This can handle multi
        part messages containing plain text, HTML and files.

        @param subject: The subject of the message, if empty, it will default
            to 'Automated Msg Processing'
        @param html: a string containing HTML to add to the message
        @param text: a string containing plain text to add to the message
        @param recip_list: a list of recip_list to send this message to
        @param cc_list: a list of recip_list to copy on this message
        @param bcc_list: a list of recip_list to blind copy on this message
        @param files: a list of files to attach to this message
        @param sender: the sender of this message
        '''
        if sender:
            self.__sender = sender
        else:
            self.__sender = '' # TODO: fill in default ..

        if sender_name_override:
            self.__sender_name_override = sender_name_override
        else:
            self.__sender_name_override = self.__sender

        if not html and not text:
            self.__root_logger.warning(
                'Error creating email message - no TEXT or HTML!!')
            self.__smtp_logger.warning(
                'Error creating email message - no TEXT or HTML!!')
            raise ValueError

        cc_list = cc_list
        # BCC myself so I can track if these emails are being sent out properly
#         bcc_recip = []
        bcc_recip = [''] # TODO: fill in default ..
        if bcc_list is not None:
            # remove duplicates
            bcc_recip = list(set(bcc_recip + bcc_list))

        if not recip_list:
            _recipients = [''] # TODO: fill in default ..
        else:
            _recipients = recip_list
        if subject is None:
            subject = 'Automated Msg Processing'
        else:
            subject = subject

        # use MIMEMultipart msg
        msg = MIMEMultipart()
#         msg['From'] = self.__sender
        msg['From'] = formataddr(
            (str(Header(self.__sender_name_override, 'utf-8')),
             self.__sender)
        )
        msg['To'] = COMMASPACE.join(_recipients)
        if cc_list is not None:
            msg['CC'] = COMMASPACE.join(cc_list)
        else:
            cc_list = []

        msg['BCC'] = COMMASPACE.join(bcc_recip)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject

        # Record the MIME types of both parts - text/plain and text/html.
        if text:
            part1 = MIMEText(text, 'plain')
        if html:
            part2 = MIMEText(html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this
        # case the HTML message, is best and preferred.
        # HOWEVER, the second to be attached will show up as an attachment and
        # not the main message... we do not want this.  In fact, our message
        # might have a link stating to click to view in browser...
        if html:
            msg.attach(part2)
        if text:
            msg.attach(part1)

        # add all files in the file list (if any)
        for file_ in files:
            part3 = MIMEBase('application', "octest-stream")
            part3.set_payload(open(file_, 'rb').read())
            encoders.encode_base64(part3)
            part3.add_header(
                'Content-Disposition', 'attachment; filename="{}"'.format(
                    os.path.basename(file_))
            )
            msg.attach(part3)

        self.__msg = msg  # set this message as the Email's msg to be sent out
        # remove duplicates and set full list of recip_list
        self.__full_recipients = list(
            set(_recipients + cc_list + bcc_recip))

    # pylint:disable=broad-except
    # We want to catch all remaining problems in this case
    def send_mail(self):
        '''
        Sends an email message previously prepared with Email.create_mail()

        The settings for sending are dictacted at time of Email instantiation.

        Example:
        >>> ex = Email(host='localhost',port='25')
        >>> ex.create_mail(subject='Trendy subject line!',\
        ... text='Body of message!')
        >>> ex.send_mail()
        '''
        try:
            msg_out = self.__msg.as_string()
        except AttributeError as ex:
            self.__root_logger.warning(('send_mail called without calling '
                                        'create_mail first'))
            self.__smtp_logger.warning(('send_mail called without calling '
                                        'create_mail first:\n{}').format(ex),
                                       exc_info=True)
            raise
        try:
            smtp = smtplib.SMTP(
                host=self.__smtp_host, port=self.__smtp_port,
                timeout=self.__smtp_timeout)
            if self.__use_smtp_tls:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(self.__smtp_usr, self.__smtp_passwd)
            smtp.set_debuglevel(1)
            if self.__exchange:
                self.__connect_to_exchange(smtp)  # if exchange server
            smtp.sendmail(
                self.__sender, self.__full_recipients, msg_out)
            self.__root_logger.info('eMail Sent to {}'.format(
                self.__full_recipients))
        except smtplib.SMTPAuthenticationError:
            self.__root_logger.warning(
                'eMail failed: authentication details incorrect')
        except smtplib.SMTPException:
            self.__root_logger.warning(
                'Authentication method not supported by smtp')
        except Exception as ex:
            self.__root_logger.warning('eMail failed to send')
            self.__smtp_logger.warning(
                'eMail failed to send with exception:\n{}'.format(ex),
                exc_info=True)
        finally:
            # pause one second
            time.sleep(1)
            smtp.quit()
