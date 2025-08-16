from collections.abc import (
    Collection,
    Callable,
)
from abc import ABC


class _NamedObject(ABC):
    def __init_subclass__(
        cls,
    ):
        cls._registry = {}

    def __init__(
        self,
        name: str,
        aliases: Collection[str] = None,
    ):
        self.name = name
        self._register(name)
        for alias in aliases or []:
            self._register(alias)

    def _register(
        self,
        key: str,
    ):
        cls = self.__class__
        _key = (
            str(key)
            .lower()
            .replace(
                "-",
                "_",
            )
            .replace(
                " ",
                "_",
            )
        )
        if _key in cls._registry:
            raise ValueError(
                f"Alias '{_key}' already registered in {cls.__name__}"
            )
        cls._registry[_key] = self

    def __getattr__(
        cls,
        item: str,
    ):
        _item = item.lower()
        try:
            return cls._registry[_item]
        except KeyError:
            raise AttributeError(
                f"{cls.__name__} has no registered attribute '{_item}'"
            )


class _Unit:
    def __init__(
        self,
        name: str,
        factor: float,
        offset: float = 0,
        converter: Callable = None,
        inverse_converter: Callable = None,
    ):
        """
        Define a unit (for use within Dimension; external interaction to create is via register_unit).
        Conversion definition: provide a way to convert from this unit to the default unit of the dimension.
        This can be done using factor (and optionally offset), or converter/inverse_converter for more complicated definitions.
        """
        self.name = name
        self.convert = converter or (
            lambda x: factor * x + offset
        )  # this unit -> default unit
        self.invert = inverse_converter or (
            lambda x: (x - offset) / factor
        )  # default unit -> this unit


class Dimension(_NamedObject):
    def __init__(
        self,
        name: str,
        aliases: Collection[str],
        default_unit: str,
    ):
        super().__init__(
            name=name,
            aliases=aliases,
        )
        self._default_unit = _Unit(
            name=default_unit,
            factor=1,
        )
        self._units = {default_unit: self._default_unit}

    def register_unit(
        self,
        name,
        factor: float,
        offset: float = 0,
        converter: Callable = None,
        inverse_converter: Callable = None,
        ignore_existing: bool = False,
    ):
        """
        `name` is the name of the unit. `ignore_existing` can be used to loop: if a unit is provided
        whose name conflicts with an existing one, the new one is ignored (rather than raising an error).

        Either a `factor` (and optionally an `offset`) can be specified, or a method for conversion
        (`converter` and `inverse_converter`). Forward conversion is from this unit (being registered) to the
        dimension's default unit. `` `default` = factor * `this` + offset`` if factor/offset are specified. That is,
        a step of 1 of this unit corresponds to a step of `factor` default units, and when a quantity's value is
        `offset` of this unit, then it is 0 default units. If `factor` is given but not `offset`, the offset value
        is taken to be 0.
        """
        if name in self._units:
            if ignore_existing:
                return
            raise ValueError(
                f"Unit '{name}' already registered for dimension {self.name}"
            )
        unit = _Unit(
            name,
            factor,
            offset,
            converter=converter,
            inverse_converter=inverse_converter,
        )
        self._units[name] = unit


class Variable(_NamedObject):
    def __init__(
        self,
        name: str,
        aliases: list[str],
        dimension: Dimension,
        *,
        case_sensitive: bool = False,
    ):
        super().__init__(
            name=name,
            aliases=aliases,
        )
        self._dimension = dimension
