"""Standard No security type used by ESXi."""

from wsvnc.security.security_type_interface import SecurityTypeInterface
from wsvnc.utils.safe_transport import SafeTransport


class NoSecurity(SecurityTypeInterface):
    def type(self) -> int:
        return 1

    async def handshake(self, transport: SafeTransport) -> None:
        return
