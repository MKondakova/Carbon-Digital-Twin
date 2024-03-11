from abc import ABC, abstractmethod
from typing import Any, Dict

from network_models.active_sensors_response import ActiveSensorsResponseItem
from sensors_module.property import Property


class Sensor(ABC):

    def __init__(self, title: str, id: int, properties: Dict[int, Property]) -> None:
        self.title = title
        self.id = id
        self.properties = properties

    @abstractmethod
    def read_property_data(self, property_id: int) -> Any:
        pass

    @abstractmethod
    def read_all_properties(self) -> Dict[int, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_network(cls, sensor: ActiveSensorsResponseItem) -> 'Sensor':
        pass