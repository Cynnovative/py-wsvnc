"""Server message interface class."""

from abc import ABC, abstractmethod

from wsvnc.utils.safe_transport import SafeTransport


class ServerMessage(ABC):
    @abstractmethod
    def type(self) -> int:
        """Return message type (uint8).

        Returns
        -------
            int
        """
        pass

    @abstractmethod
    async def read(self, transport: SafeTransport, msg: bytes) -> None:
        """Handle bytes message.

        Args:
            transport (SafeTransport)
            msg (bytes)
        """
        pass
