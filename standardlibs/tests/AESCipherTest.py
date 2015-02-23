'''
Tests for AESCipher module.

@author: chrcoe
'''
import unittest

from standardlibs.AESCipher import AESCipherPlain, AESCipherHEX


# pylint: disable=too-many-public-methods
# A UNIT test will have as many methods as needed to complete testing.


class AESCipherTest(unittest.TestCase):

    '''
    NIST AES ECB Test Vectors for HEX input:
    http://csrc.nist.gov/publications/nistpubs/800-38a/sp800-38a.pdf

    AESCipherPlain only works on ECB Mode with 0 byte padding
    '''

    def test_aes128_fulllength_hex(self):
        ''' Tests AES128 with full length input and hex encoded text. '''
        # ENCRYPT and DECRYPT All Blocks (#1-4) HEX input (standard)
        hex_key = '2b7e151628aed2a6abf7158809cf4f3c'  # in hex
        cipher = AESCipherHEX(hex_key)
        hex_text = {  # these are in HEX
            1: '6bc1bee22e409f96e93d7e117393172a',
            2: 'ae2d8a571e03ac9c9eb76fac45af8e51',
            3: '30c81c46a35ce411e5fbc1191a0a52ef',
            4: 'f69f2445df4f9b17ad2b417be66c3710'
        }
        plain_text = {  # these are in HEX
            1: '6bc1bee22e409f96e93d7e117393172a',
            2: 'ae2d8a571e03ac9c9eb76fac45af8e51',
            3: '30c81c46a35ce411e5fbc1191a0a52ef',
            4: 'f69f2445df4f9b17ad2b417be66c3710'
        }
        cipher_text = {
            1: '3ad77bb40d7a3660a89ecaf32466ef97',
            2: 'f5d3d58503b9699de785895a96fdbaaf',
            3: '43b1cd7f598ece23881b00e3ed030688',
            4: '7b0c785e27e8ad3f8223207104725dd4'
        }
        for block in range(1, 5):
            enc = cipher.encrypt(hex_text[block])
            self.assertEqual(enc, cipher_text[block])
            dec = cipher.decrypt(cipher_text[block])
            self.assertEqual(dec, plain_text[block])

    def test_aes128_fulllength_plain(self):
        ''' Tests AES128 with full length input and plain text. '''
        # this is not a real key, just here for testing purposes.
        plain_key = '2b7e151628aed2a6abf7158809cf4f3c'  # in PLAINTEXT
        cipher = AESCipherPlain(plain_key)
        plain_text = {  # these are in HEX
            1: '6bc1bee22e409f96e93d7e117393172a',
            2: 'ae2d8a571e03ac9c9eb76fac45af8e51',
            3: '30c81c46a35ce411e5fbc1191a0a52ef',
            4: 'f69f2445df4f9b17ad2b417be66c3710'
        }
        plain_cipher_text = {
            1: ('3360ec85c7925b94340e49a64c6ce3a41df28e0d7e8169c91160a5d7f61'
                'cd581'),
            2: ('1b003b6526b884b5e1fcf1291e5ff8bf42c84b3e58f6dd4f48be15274f1'
                '4b4cf'),
            3: ('dd3000ba91f5684377d3fc458b82108cd6fbe2eaa994a3fa8e9687bef51'
                'b8072'),
            4: ('de5cce6d21d536cab2373237faaf2297e3a25b4418da6852a1a719e360b'
                'c7725')
        }
        for block in range(1, 5):
            enc = cipher.encrypt(plain_text[block])
            self.assertEqual(enc, plain_cipher_text[block])
            dec = cipher.decrypt(plain_cipher_text[block])
            self.assertEqual(dec, plain_text[block])

    def test_aes128_padding_hex(self):
        ''' Tests AES128 with padding and hex encoded text. '''
        hex_key = '2b7e151628aed2a6abf7158809cf4f3c'
        cipher = AESCipherHEX(hex_key)
        hex_text = {  # these are in HEX
            1: '31',  # 1
            2: '54455354',  # TEST
            3: '30393837363534333231',  # 0987654321
            4: '68656c6c6f21'  # hello!
        }
        plain_text = {  # these are in HEX
            1: '1',
            2: 'TEST',
            3: '0987654321',
            4: 'hello!'
        }
        cipher_text = {
            1: '18f01a9770e246f5855e63478c36f91e',
            2: '568f9df0279b926cc6f6620987cf5bef',
            3: 'b7e2de059b6584e0eb73db25d0492512',
            4: '5d75ed1927966980d7ece4b8c6497b33'
        }
        for block in range(1, 5):
            enc = cipher.encrypt(hex_text[block])
            self.assertEqual(enc, cipher_text[block])
            dec = cipher.decrypt(cipher_text[block])
            self.assertEqual(dec, plain_text[block])

    def test_aes128_padding_plain(self):
        ''' Tests AES128 with padding and plain text. '''
        plain_key = '2b7e151628aed2a6abf7158809cf4f3c'
        cipher = AESCipherPlain(plain_key)
        plain_text = {  # these are in HEX
            1: '1',
            2: 'TEST',
            3: '0987654321',
            4: 'hello!'
        }
        cipher_text = {
            1: '83d088a2358b7782d8f82f98f96b1b52',
            2: 'd911c8757c3577943bfda94eb3411031',
            3: '49644121088a89faa0ea2066178ff911',
            4: '30ee48f50d21d0be4d2c4f40f711b4d6'
        }
        for block in range(1, 5):
            enc = cipher.encrypt(plain_text[block])
            self.assertEqual(enc, cipher_text[block])
            dec = cipher.decrypt(cipher_text[block])
            self.assertEqual(dec, plain_text[block])

    def test_aes128_empty_plain(self):
        ''' Tests AES128 with empty string and plain text.
        This tests both encrypt and decrypt with empty input.  '''
        plain_key = '2b7e151628aed2a6abf7158809cf4f3c'
        cipher = AESCipherPlain(plain_key)
        plain_text = ''
        self.assertRaises(ValueError, cipher.encrypt, plain_text)

        cipher_text = ''
        self.assertRaises(ValueError, cipher.decrypt, cipher_text)

    def test_aes128_empty_hex(self):
        ''' Tests AES128 with empty string and hex encoded text.
        This tests both encrypt and decrypt with empty input.  '''
        hex_key = '2b7e151628aed2a6abf7158809cf4f3c'
        cipher = AESCipherHEX(hex_key)
        hex_text = ''
        self.assertRaises(ValueError, cipher.encrypt, hex_text)

        cipher_text = ''
        self.assertRaises(ValueError, cipher.decrypt, cipher_text)


if __name__ == "__main__":
    unittest.main()
