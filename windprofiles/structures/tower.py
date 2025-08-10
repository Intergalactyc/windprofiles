from collections.abc import Collection
from .location import Location


class Boom:
    def __init__(self, number: int, height: float):
        self.number = number
        """Boom number, uniquely identifying the boom in the tower"""
        self.height = height
        """Height from base of tower"""


class MetTower:
    def __init__(self, location: Location, booms: Collection[Boom]):
        self._location = location
        self._booms = {boom.number: boom for boom in booms}
        if len(self._booms) != len(booms):
            raise ValueError("Boom numbers are not unique!")

    def add_boom(self, boom: Boom):
        self._booms[boom.number] = boom

    def get_boom(self, number: int) -> Boom:
        """
        Returns the boom with the given number, if it exists, and `None` otherwise.
        """
        return self._booms.get(number)
