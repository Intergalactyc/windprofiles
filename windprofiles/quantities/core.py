from windprofiles.utilities.collections import CaseInsensitiveDict
from collections.abc import (
    Collection,
    Callable,
)
from abc import ABC
from pandas import Series


class _NamedObject(ABC):
    def __init_subclass__(
        cls,
    ):
        cls._primary_registry = {}
        cls._secondary_registry = {}

    def __init__(
        self,
        name: str,
        strong_aliases: Collection[str] = None,
        weak_aliases: Collection[str] = None,
    ):
        self.name = name
        self._register_strong(name)
        for alias in strong_aliases or []:
            self._register(alias, True)
        for alias in weak_aliases or []:
            self._register(alias, False)

    @classmethod
    def _transform(cls, value, strong: bool):
        if strong:
            return str(value).replace("-", "_").replace(" ", "")
        return str(value).lower().replace("-", "_").replace(" ", "")

    def _register(self, key: str, strong: bool):
        cls = self.__class__
        _key = cls._transform(key, False)
        if _key in cls._secondary_registry:
            raise ValueError(
                f"Alias '{_key}' already registered in {cls.__name__}"
            )
        cls._secondary_registry[_key] = self
        if strong:
            cls._primary_registry[cls._transform(key, True)] = self

    def __getattr__(cls, item: str):
        _item = cls._transform(item, True)
        try:
            return cls._primary_registry[_item]
        except KeyError:
            raise AttributeError(
                f"{cls.__name__} has no strongly registered object '{_item}'"
            )

    def __class_getitem__(cls, item: str):
        _item = _NamedObject._transform(item, False)
        try:
            return cls._secondary_registry[_item]
        except KeyError:
            raise AttributeError(
                f"{cls.__name__} has no registered object '{_item}'"
            )

    @classmethod
    def get(cls, item: str):
        try:
            return cls[item]
        except (AttributeError, KeyError):
            return None

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.__class__.transform(self.name, strong = True)}"


class _Unit:
    def __init__(
        self,
        name: str,
        factor: float,
        offset: float = 0,
        aliases: Collection[str] = None,
        converter: Callable = None,
        inverse_converter: Callable = None,
    ):
        """
        Define a unit (for use within Dimension; external interaction to create is via register_unit).
        Conversion definition: provide a way to convert from this unit to the default unit of the dimension.
        This can be done using factor (and optionally offset), or converter/inverse_converter for more complicated definitions.
        """
        self.name = name
        self.aliases = set(aliases) if aliases else set()
        self.aliases.add(name)
        self.converter = converter or (
            lambda x: factor * x + offset
        )  # this unit -> default unit
        self.inverse_converter = inverse_converter or (
            lambda x: (x - offset) / factor
        )  # default unit -> this unit

    def __str__(self):
        return self.name


class Dimension(_NamedObject):
    def __init__(
        self,
        name: str,
        aliases: Collection[str],  # case sensitive aliases for attr access
        default_unit: str,
        default_unit_aliases,
    ):
        super().__init__(
            name=name,
            strong_aliases=aliases,
        )
        self._default_unit = _Unit(
            name=default_unit,
            factor=1,
        )
        self._units = CaseInsensitiveDict(
            {a: self._default_unit for a in self._default_unit.aliases}
        )

    def register_unit(
        self,
        name,
        factor: float,
        offset: float = 0,
        aliases: Collection[str] = None,
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
        for alias in aliases:
            if alias in self._units:
                raise ValueError(
                    f"Alias '{alias}' already registered to unit {self._units[alias]} for dimension {self.name}"
                )
        unit = _Unit(
            name,
            factor,
            offset,
            aliases=aliases,
            converter=converter,
            inverse_converter=inverse_converter,
        )
        self._units.update({a: unit for a in unit.aliases})

    def _run_conversion(self, value, converter):
        try:
            return converter(value)
        except Exception:
            if isinstance(value, Series):
                return value.apply(converter, axis=1)
            if isinstance(value, list):
                return [converter(v) for v in value]
            raise

    def _get_unit(self, unit_name):
        if unit_name is None:
            return self._default_unit
        unit = self._units.get(unit_name)
        if unit is None:
            raise KeyError(
                f"Unit {unit_name} is not recognized. Possible values are {', '.join([u.name for u in self._units])}"
            )
        return unit

    def convert(self, value, from_unit):
        """Convert a value, or list/series of values, from the given unit to the default unit"""
        unit = self._get_unit(from_unit)
        return self._run_conversion(value, unit.converter)

    def convert_from(self, *args, **kwargs):
        """Alias for Dimension.convert"""
        return self.convert(*args, **kwargs)

    def convert_to(self, value, to_unit):
        """Convert a value, or list/series of values, from the default unit to the given unit"""
        unit = self._get_unit(to_unit)
        return self._run_conversion(value, unit.inverse_converter)

    @property
    def default_unit(self):
        return self._default_unit


class Variable(_NamedObject):
    def __init__(
        self,
        name: str,  # case-sensitive main name for display, used as a strong alias
        dimension: Dimension,
        strong_aliases: Collection[
            str
        ],  # case-sensitive aliases for attr access (Variable.Alias), also used for case-insensitive dictlike access
        weak_aliases: Collection[
            str
        ],  # case-insensitive aliases for dictlike access (possible/typical column names)
    ):
        super().__init__(
            name=name, strong_aliases=strong_aliases, weak_aliases=weak_aliases
        )
        self._dimension = dimension

    def convert(self, *args, **kwargs):
        return self._dimension.convert(*args, **kwargs)

    def convert_from(self, *args, **kwargs):
        return self._dimension.convert_from(*args, **kwargs)

    def convert_to(self, *args, **kwargs):
        return self._dimension.convert_to(*args, **kwargs)
