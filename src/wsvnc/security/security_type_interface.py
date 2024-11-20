"""Security interface class."""

from abc import ABC, abstractmethod

from wsvnc.utils.safe_transport import SafeTransport


class SecurityTypeInterface(ABC):
    @abstractmethod
    def type(self) -> int:
        """Return security type (uint8).

        Returns
        -------
            int
        """
        pass

    @abstractmethod
    async def handshake(self, transport: SafeTransport) -> None:
        """Handle security handshake.

        Args:
            transport (SafeTransport): the websocket connection.
        """
        pass
