from collector.collectors.base import ICollector
from collector.domain.models import MachineSnapshot
from collector.providers.base import IPlatformProvider


class SerialNumberCollector(ICollector):
    @property
    def name(self) -> str:
        return "serial_number"

    def collect(self, snapshot: MachineSnapshot, provider: IPlatformProvider) -> None:
        snapshot.serial_number = provider.get_serial_number()
