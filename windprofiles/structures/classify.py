"""Classes to define classification schemes for e.g. terrain & stability classification."""

import math
import pandas as pd
import numpy as np
from warnings import warn
from abc import ABC, abstractmethod
from windprofiles.lib.polar import angular_distance
from numbers import Number
import geopy.distance as gdist


class CoordinateRegion:
    """
    Pseudoclassifier class that can be used to determine whether a given coordinate point
    (latitude and longitude) are within a certain distance of a central point.
    """

    def __init__(
        self,
        latitude: float,
        longitude: float,
        radius: float,
        unit: str = "meters",
    ):
        """
        Arguments should be in degrees
        Pass either a single value for radius or a latitude,
            longitude tuple pair (order is important)
        """
        # Would like to add in ability to use distance radius rather than just angular
        if unit not in ["km", "m", "kilometers", "meters", "mi", "miles"]:
            raise Exception(f"Unit {unit} not recognized")
        self._unit = unit
        self._lat = latitude
        self._long = longitude
        self._radius = radius

    def _convertDistance(self, distance):
        match self._unit:
            case "km":
                return distance.km
            case "m":
                return distance.m
            case "mi":
                return distance.mi
            case "kilometers":
                return distance.km
            case "meters":
                return distance.m
            case "miles":
                return distance.mi
            case _:
                raise Exception(
                    f"Failure in distance conversion for distance {distance} and unit {self._unit}"
                )

    def classify(self, latitude, longitude):
        """
        Classify a latitude-longitude pair as either in the region (True)
            or outside of it (False)
        """
        if math.isnan(latitude) or math.isnan(longitude):
            return False
        dist_raw = gdist.geodesic(
            (latitude, longitude), (self._lat, self._long)
        )
        dist = self._convertDistance(dist_raw)
        return dist < self._radius

    def classify_line(self, begin_lat, begin_long, end_lat, end_long):
        to_check = [(begin_lat, begin_long), (end_lat, end_long)]
        while gdist.geodesic(to_check[0], to_check[1]) > self.radius:
            pass


# class CountyRegion:
#     def __init__(self, counties: list[str], state: str):
#         pass
#     # DO THIS LATER
#     # Cedar Rapids county: Linn
#     # Nearest counties in Iowa: Benton, Iowa, Johnson
#     # Other counties in Iowa bordering Linn: Cedar, Jones, Delaware, Buchanan, Black Hawk


class _TemplateClassifier(ABC):
    """
    Classifier abstract base class
    """

    def __init__(self, parameter: str = None, *, nanNA: bool = True):
        """
        `parameter` optionally sets the name of the parameter
            (for pd.DataFrame column selection) to classify based on
        `nanNA` is a boolean determining whether NaN values should
            be classified as None or left to be classified as "other"
        """
        self._classNames = ["other"]
        self._rules = [None]
        self._parameter = parameter
        self._nanNA = nanNA

    def _isNaN(self, value):
        return isinstance(value, Number) and math.isnan(value)

    def _validate(self, value):
        """
        A very simple validation that tests whether a value is a numerical
        data type. Values of None and NaN fail.
        """
        return isinstance(value, Number) and not math.isnan(value)

    def set_other(self, new_name: str):
        """
        Set the name of the class given when no other class is found
            based on the defined scheme (default is "other")
        """
        self._classNames[-1] = new_name

    def set_parameter(self, parameter: str = None):
        """
        Set classification parameter if one was not provided in __init__
            or for updating old one
        """
        self._parameter = parameter

    def _insert_class(self, class_name: str, rule):
        """
        Private: insert a new classification name-rule pair
            (Inserted at index 0 rather than appended)
        """
        self._classNames.insert(0, class_name)
        self._rules.insert(0, rule)

    def add_nan_rule(self, class_name: str):
        if self._nanNA:
            warn(
                "classify._TemplateClassifier.add_nan_rule: Creating a NaN rule when self._nanNA was True -- setting self._nanNA to False"
            )
            self._nanNA = False
        self._insert_class

    @abstractmethod
    def add_class(self):
        """
        Template: Define a method to create a new classification
        """
        pass

    @abstractmethod
    def _test_value(self, value, rule):
        """
        Template: Define a method that returns True if `value`
            satisfies `rule`, and False otherwise.
        """
        pass

    def classify(self, value: int | float) -> str:
        """
        Classify a value as one of the classNames based on the given
        classification rules defined by calls to self.add_class
        """
        if self._nanNA and self._isNaN(value):
            return None
        for clName, rule in zip(self._classNames, self._rules):
            if (
                rule is None
                or (self._isNaN(rule) and self._isNaN(value))
                or (
                    self._validate(value)
                    and self._test_value(value=value, rule=rule)
                )
            ):
                return clName
        raise Exception(
            "classify._TemplateClassifier.classify: unknown error encountered"
        )

    def classify_rows(self, df: pd.DataFrame) -> pd.Series:
        """
        Classify the rows of a dataframe according to their values
        """
        if self._parameter is not None:
            if self._parameter not in df.columns:
                raise Exception(
                    f"classify._TemplateClassifier.classify_rows: parameter {self._parameter} not found in columns of given pd.DataFrame"
                )
            return df.apply(
                lambda row: self.classify(row[self._parameter]), axis=1
            ).astype("category")
        else:
            raise Exception(
                "classify._TemplateClassifier.classify_rows: no parameter provided"
            )

    def get_classes(self, other: bool = True) -> list:
        """
        Public getter method that returns a list of the class names.
        Ordered by precedence: earlier is attempted first.
        """
        if other:
            return self._classNames
        return self._classNames[:-1]


class PolarClassifier(_TemplateClassifier):
    """
    Classify wind directions in bins (allows for binning modulo 360)
    Directions assumed to be in degrees
    """

    def __init__(self, parameter: str = None, nanNA: bool = True):
        super().__init__(parameter=parameter, nanNA=nanNA)

    def add_class(
        self,
        class_name: str,
        center: int | float,
        radius: int | float = None,
        width: int | float = None,
        inclusive: bool = True,
    ):

        if (radius is not None and width is not None) and radius != width / 2:
            raise Exception(
                "classify.PolarClassifier.add_class: Conflicting radius and width arguments passed"
            )
        if radius is None and width is None:
            raise Exception(
                "classify.PolarClassifier.add_class: Width or radius must be specified"
            )
        if (isinstance(radius, Number) and radius < 0) or (
            isinstance(width, Number) and width < 0
        ):
            raise Exception(
                "classify.PolarClassifier.add_class: Negative radius or width provided"
            )

        if width is not None and radius is None:
            radius = width / 2

        rule = (center, [radius]) if inclusive else (center, radius)

        self._insert_class(class_name=class_name, rule=rule)

    def _test_value(self, value, rule):
        center, radius = rule
        if type(radius) is list:
            return angular_distance(value, center) <= radius[0]
        else:
            return angular_distance(value, center) < radius


class SingleClassifier(_TemplateClassifier):
    """
    Classify data based on a single real-valued parameter
    """

    def __init__(self, parameter: str = None, nanNA: bool = True):
        super().__init__(parameter=parameter, nanNA=nanNA)

    def _parse_interval(self, interval):
        if type(interval) is not str:
            raise Exception(
                "classify.SingleClassifier._parse_interval: provided interval must be a string"
            )

        stripped = interval.replace(" ", "")
        leftP = stripped[0]
        rightP = stripped[-1]

        if leftP not in ["[", "("] or rightP not in ["]", ")"]:
            raise Exception(
                "classify.SingleClassifier._parse_interval: provided interval must be in valid parenthetical format"
            )

        cleaned = stripped[1:-1]
        split = cleaned.split(",")

        if len(split) != 2:
            raise Exception(
                "classify.SingleClassifier._parse_interval: provided interval must contain a single delimiting comma ','"
            )

        if split[0].lower in ["-inf", "-infty", "-infinity", "-np.inf"]:
            leftV = -np.inf
        else:
            try:
                leftV = float(split[0])
            except ValueError:
                raise Exception(
                    f"classify.SingleClassifier._parse_interval: invalid left bound '{leftV}'"
                )

        if split[1].lower in [
            "inf",
            "infty",
            "infinity",
            "np.inf",
            "+inf",
            "+infty",
            "+infinity",
            "+np.inf",
        ]:
            rightV = np.inf
        else:
            try:
                rightV = float(split[1])
            except ValueError:
                raise Exception(
                    f"classify.SingleClassifier._parse_interval: invalid left bound '{leftV}'"
                )

        left_bound = leftV if leftP == "(" else [leftV]
        right_bound = rightV if rightP == ")" else [rightV]

        return (left_bound, right_bound)

    def add_class(
        self,
        class_name: str,
        interval: str = None,
        *,
        left_inclusive: int | float = None,
        left_exclusive: int | float = None,
        right_inclusive: int | float = None,
        right_exclusive: int | float = None,
    ):
        """
        Add a classification bin.
        Provide an interval string in standard open () closed [] format,
            or a valid combination of left and right inclusive/exclusive arguments.
        Interval strings take precedence. Given values must be numeric
            (instances of numbers.Number)
        """
        if interval:
            rule = self._parse_interval(interval)
            if rule is not None:
                self._insert_class(class_name=class_name, rule=rule)
        else:
            if left_inclusive is not None and left_exclusive is not None:
                raise Exception(
                    "classify.SingleClassifier.add_class: Only one of left_inclusive or left_exclusive may be provided"
                )
            if right_inclusive is not None and right_exclusive is not None:
                raise Exception(
                    "classify.SingleClassifier.add_class: Only one of right_inclusive or right_exclusive may be provided"
                )

            if self._validate(left_inclusive):
                left_bound = [left_inclusive]
            elif self._validate(left_exclusive):
                left_bound = left_exclusive
            else:
                warn(
                    "classify.SingleClassifier.add_class: Did not receive valid left bound, interpreting as -np.inf"
                )
                left_bound = -np.inf

            if self._validate(right_inclusive):
                right_bound = [right_inclusive]
            elif self._validate(right_exclusive):
                right_bound = right_exclusive
            else:
                warn(
                    "classify.SingleClassifier.add_class: Did not receive valid right bound, interpreting as +np.inf"
                )
                right_bound = np.inf

            self._insert_class(
                class_name=class_name, rule=(left_bound, right_bound)
            )

    def _test_value(self, value: int | float, rule: list[int | list]):
        left, right = rule
        if type(left) is list and type(right) is list:
            return left[0] <= value <= right[0]
        if type(right) is list:
            return left < value <= right[0]
        if type(left) is list:
            return left[0] <= value < right
        return left < value < right


# Future: add MultiClassifier which allows for classification
#   based on multiple parameters simultaneously;
#   DiscreteClassifier which classifies based on matching
#   exactly one value (possibly within tolerance) including non-numerics


class TerrainClassifier(PolarClassifier):
    """
    Simple terrain classifer that classifies terrain as either 'open'
        or 'complex' based on wind direction at a specific boom
    """

    def __init__(
        self,
        *,
        complexCenter: int | float,
        openCenter: int | float,
        radius: int | float = None,
        width: int | float = None,
        directionCol: str = None,
        boom: int = None,
        inclusive: bool = True,
    ):

        if directionCol is None and boom is None:
            warn(
                "classify.TerrainClassifier: Direction column unspecified, add manually by calling object method set_parameter"
            )
            param = None
        elif (
            directionCol is not None
            and boom is not None
            and directionCol != f"wd_{boom}"
        ):
            warn(
                "classify.TerrainClassifier: Got conflicting boom and directionCol specifications, defaulting parameter to None. Add manually by calling object method set_parameter"
            )
            param = None
        elif directionCol is not None:
            param = directionCol
        elif type(boom) is int:
            param = f"wd_{boom}"
        else:
            warn(
                "classify.TerrainClassifier: failed to parse direction column specification, defaulting parameter to None. Add manually by calling object method set_parameter"
            )
            param = None

        super().__init__(parameter=param, nanNA=False)

        self.add_nan_rule(class_name="calm")
        self.add_class(
            class_name="complex",
            center=complexCenter,
            radius=radius,
            width=width,
            inclusive=inclusive,
        )
        self.add_class(
            class_name="open",
            center=openCenter,
            radius=radius,
            width=width,
            inclusive=inclusive,
        )

        if param is not None:
            self._boom = self._colToBoom(param)
            self._directionCol = param
        else:
            self._boom = None
            self._directionCol = None

    def _colToBoom(self, colName):

        if "_" not in colName:
            warn(
                "classify.TerrainClassifier._colToBoom: atypical column name format, interpreting boom as None. Specify a boom by calling object method specify_boom"
            )
            return None

        cut = colName.split("_")[1]

        if not cut.isnumeric():
            warn(
                "classify.TerrainClassifier._colToBoom: noninteger boom in column name, interpreting boom as None. Specify a boom by calling object method specify_boom"
            )
            return None

        return int(cut)

    def specify_boom(self, new_boom: int):
        """
        Associate a classification boom without overwriting
            the direction column parameter
        """
        if self._boom is not None:
            warn(
                f"classify.TerrainClassifier.specify_boom: overwriting previous boom of {self._boom} with new value of {new_boom}"
            )
        self._boom = new_boom

    def set_parameter(self, parameter=None):
        """
        Set/update the wind direction column name (& with it the boom)
        """
        self._boom = self._colToBoom(parameter)
        self._directionCol = parameter
        return super().set_parameter(parameter)

    def get_boom(self) -> int:
        """
        Get the boom that classification is based on
        """
        return self._boom

    def get_boom_column(self) -> str:
        """
        Get the classification column name
        """
        return self._directionCol


class StabilityClassifier(SingleClassifier):
    def __init__(
        self, parameter: str = None, classes: list[tuple[str, str]] = None
    ):
        """
        Slightly easier setup for a stability-type SingleClassifer.
        `classes` should be a list of tuples in which the first entry is the class
            name and the second is a properly formatted selection interval.
        """
        if parameter is None or type(parameter) is not str:
            warn(
                "classify.StabilityClassifier: No valid classification parameter given, make sure to call object method set_parameter to add one"
            )
        super().__init__(parameter=parameter, nanNA=True)
        for cName, cInterval in classes:
            self.add_class(class_name=cName, interval=cInterval)
