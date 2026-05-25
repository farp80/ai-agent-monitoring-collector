from collector.collectors.base import ICollector
from collector.domain.models import MachineSnapshot
from collector.providers.base import IPlatformProvider


class HardDrivesCollector(ICollector):
    @property
    def name(self) -> str:
        return "hard_drives"

    def collect(self, snapshot: MachineSnapshot, provider: IPlatformProvider) -> None:
        snapshot.hard_drives = provider.get_hard_drives()
