import logging
import socket

from zeroconf import ServiceInfo, Zeroconf

from app.core.config import settings

logger = logging.getLogger(__name__)

_SERVICE_TYPE = "_http._tcp.local."
_SERVICE_NAME = f"ACExchanger.{_SERVICE_TYPE}"

_zeroconf: Zeroconf | None = None
_service_info: ServiceInfo | None = None


def _get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def start_mdns() -> None:
    global _zeroconf, _service_info
    try:
        ip = settings.LAN_IP or _get_local_ip()
        _service_info = ServiceInfo(
            _SERVICE_TYPE,
            _SERVICE_NAME,
            addresses=[socket.inet_aton(ip)],
            port=settings.PORT,
            properties={"path": "/api/v1"},
            server=f"{socket.gethostname()}.local.",
        )
        _zeroconf = Zeroconf()
        _zeroconf.register_service(_service_info)
        logger.info("mDNS: advertising %s on %s:%d", _SERVICE_NAME, ip, settings.PORT)
    except Exception:
        logger.exception("mDNS: failed to start")


def stop_mdns() -> None:
    global _zeroconf, _service_info
    if _zeroconf and _service_info:
        try:
            _zeroconf.unregister_service(_service_info)
            _zeroconf.close()
            logger.info("mDNS: service stopped")
        except Exception:
            logger.exception("mDNS: failed to stop cleanly")
        finally:
            _zeroconf = None
            _service_info = None
