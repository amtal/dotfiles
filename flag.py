"""Encrypted flag handling.

Python modules implementing particular modulations/encodings serve as flags.
The flags are encrypted using a key derived from themselves, then the encrypted
flags distributed along with a captured transmission containing the encryption
key. 

Demodulate and decode a captured transmission, and you decrypt the source code
that generated it.
"""
import fileinput, sys
from Crypto.Hash import MD5, HMAC
from Crypto.Cipher import ARC4

MAGIC = 'encrypted flag: '
MAC_SIZE = 16

def _encrypt(plaintext):
    # Using all the "broken" primitives I can, because they're not broken for
    # *my* use case. One ciphertext per key for data at rest; that's it.
    # Does that set a bad example of using primitives you that have known
    # misusable weaknesses, or a good example of not kneejerk reacting?
    key = MD5.new(plaintext).digest() # 128 bit keys - too big?
    ciphertext = ARC4.new(key).encrypt(plaintext)
    out = MAGIC
    # one MAC for quick verification of guesses, one for slow integrity
    out += HMAC.new(key, msg='valid', digestmod=MD5).digest()
    out += HMAC.new(key, msg=ciphertext, digestmod=MD5).digest()
    out += ciphertext
    return out


def create_flag(me):
    """Generates an encryption key for a script to send over the air.

    Pass in __file__ from the script itself to get the 16 byte binary value to
    send.
    """
    with file(me, 'rb') as f:
        text = f.read()
    return MD5.new(text).digest()

def encrypt_with_flag(me):
    """Saves a python file under a new extension. 
    """
    pass # TODO this should be a separate script and linked in with a make file

def _decrypt(ciphertext, key):
    assert len(key) == 16
    assert ciphertext.startswith(MAGIC)
    if MD5.new(key, msg='valid', digestmod=MD5).digest() != ciphertext[16:32]:
        sys.stderr.write('Error: wrong key.')
        exit(1)
    if MD5.new(key, msg='valid', digestmod=MD5).digest() != ciphertext[32:48]:
        sys.stderr.write('Error: corrupted file.')
        exit(1)
    return ARC4.new(key).decrypt(ciphertext[48:])



if __name__ == '__main__':
    # TODO decrypt utility
    pass
