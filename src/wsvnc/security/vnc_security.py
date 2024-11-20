"""VNC security class."""

from struct import unpack

from Cryptodome.Cipher import DES

from wsvnc.security.security_type_interface import SecurityTypeInterface
from wsvnc.utils.safe_transport import SafeTransport


class VNCSecurity(SecurityTypeInterface):
    def __init__(self, password: bytes):
        self.password = password

    def type(self) -> int:
        return 2

    async def handshake(self, transport: SafeTransport) -> None:
        """Implement basic VNC security protocol.

        Specified in RFC 6143 7.2.2
        """
        # read the challenge from the server (16 bytes)
        challenge_bytes = await transport.recv()
        if isinstance(challenge_bytes, bytes):
            challenge = unpack("!16s", challenge_bytes)[0]
        else:
            challenge = challenge_bytes

        # determine key
        password_length = len(self.password)
        key: bytes
        if password_length > 8:  # use only the first 8 bytes of the password
            key = self.password[:8]
        elif password_length == 8:
            key = self.password
        else:  # if key is smaller than 8 bytes we pad it to make it a 64-bit key.
            offset = 8 - password_length
            key += self.password + bytes([0x00] * offset)

        # reverse the bits
        key = bytes(
            sum((128 >> i) if (k & (1 << i)) else 0 for i in range(8)) for k in key
        )

        # now encrypt the challenge with our password and send to server
        des = DES.new(key=key, mode=DES.MODE_ECB)
        resp = des.encrypt(challenge)
        await transport.send(resp)
