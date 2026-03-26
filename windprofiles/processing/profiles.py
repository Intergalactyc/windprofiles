import pandas as pd
import numpy as np
from abc import ABC, abstractmethod, abstractproperty
from sklearn.metrics import r2_score


class ProfileModel(ABC):
    def __init__(self, booms: list[int], heights: list[float], name: str):
        self.booms = booms
        self.heights = heights
        self.name = name

    @abstractmethod
    @staticmethod
    def model(self, parameters: dict, height):
        return

    @abstractmethod
    @staticmethod
    def fit(self, heights: list, speeds: list, constraints: list = []) -> dict:
        pass

    @abstractproperty
    def num_parameters(self) -> int:
        return NotImplemented

    @abstractproperty
    def num_constraints(self) -> int:
        return NotImplemented

    def get_r2(self, speeds, parameters):
        model_speeds = [self.model(parameters, h) for h in self.heights]
        return r2_score(speeds, model_speeds)

    def get_fit_columns(
        self,
        df: pd.DataFrame,
        out_col_suffix: str,
        get_r2: bool,
        ws_col: str = "ws",
        constraint_cols: list[str] = [],
    ):
        if len(constraint_cols) != self.num_constraints:
            raise ValueError(
                f"Must pass {self.num_constraints} constraint column names"
            )

        # if len(out_cols) == self.num_parameters:
        #     def _apply_func(heights, speeds, constraints):
        #         return self.fit(heights, speeds, constraints)
        # elif len(out_cols) == self.num_parameters + 1:
        #     def _apply_func(heights, speeds, constraints):
        #         params = self.fit(heights, speeds, constraints)
        #         r2 = self.get_r2(speeds, params + constraints)
        #         return *params, (r2)
        # else:
        #     raise ValueError(f"Must pass either {self.num_parameters} or {self.num_parameters + 1} output column names")

        # df[
        #     out_cols[0] if len(out_cols) == 1
        #     else out_cols if len(out_cols) == self.num_parameters
        #     else out_cols[:-1]
        # ] = df.apply(
        #         lambda row : _apply_func(
        #             self.heights,
        #             [row[f"{ws_col}_{b}"] for b in self.booms],
        #             [row[cc] for cc in constraint_cols]
        #         ),
        #         axis = 1,
        #         result_type = "expand" if len(out_cols) > 1 else None
        #     )
        # return df


def log_model(parameters, height):
    ustar = parameters["ustar"]
    z0 = parameters["z0"]


def powerlaw_model(parameters, height):
    alpha, beta = parameters


class UnconstrainedLogarithmicProfile(ProfileModel):
    model = log_model
    num_parameters = 2
    num_constraints = 0


class ConstrainedLogarithmicProfile(ProfileModel):
    model = log_model
    num_parameters = 1
    num_constraints = 1


class PowerLawProfile(ProfileModel):
    model = powerlaw_model
    num_parameters = 2
    num_constraints = 0

    # def ft
