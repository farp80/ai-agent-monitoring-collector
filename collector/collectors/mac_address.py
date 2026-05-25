from collector.collectors.base import ICollector
from collector.domain.models import MachineSnapshot
from collector.providers.base import IPlatformProvider


class MacAddressCollector(ICollector):
    @property
    def name(self) -> str:
        return "mac_addresses"

    def collect(self, snapshot: MachineSnapshot, provider: IPlatformProvider) -> None:
        snapshot.mac_addresses = provider.get_mac_addresses()
