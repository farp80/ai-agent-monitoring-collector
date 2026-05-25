from collector.collectors.base import ICollector
from collector.domain.models import MachineSnapshot
from collector.providers.base import IPlatformProvider


class NetworkAdaptersCollector(ICollector):
    @property
    def name(self) -> str:
        return "network_adapters"

    def collect(self, snapshot: MachineSnapshot, provider: IPlatformProvider) -> None:
        snapshot.network_adapters = provider.get_network_adapters()
