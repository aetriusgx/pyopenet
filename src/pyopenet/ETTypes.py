import warnings
from collections.abc import Generator
from dataclasses import dataclass
from datetime import date
from itertools import product
from typing import Any, Hashable, Literal

from .ETException import PairValueError

ReducerType = Literal[
    "min",
    "max",
    "mean",
    "median",
    "mode",
    "sum"
]

IntervalType = Literal["daily", "monthly"]

ModelType = Literal[
    "ensemble",
    "geesebal",
    "ssebop",
    "sims",
    "disalexi",
    "ptjpl",
    "eemetric"
]

VariableType = Literal[
    "et",
    "et_mad_min",
    "et_mad_max",
    "eto",
    "etr",
    "etof",
    "ndvi",
    "pr",
    "count",
    "model_count"
]

ReferenceType = Literal["cimis", "gridmet", "fret"]
UnitType = Literal["mm", "in"]
FileType = Literal["csv", "json"]
DateRange = tuple[str | date, str | date]
_GeometryType = list[float | Hashable]

_Overpass_Models = {
    "ensemble": "et",
    "sims": "etof",
    "disalexi": "et",
    "eemetric": "etof",
    "geesebal": "et",
    "ptjpl": "et",
    "ssebop": "etof"
}

@dataclass
class PolygonConfig:
    reducer: ReducerType
    geojson: dict[str, Any] | None = None
    
    def __kv__(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}
    
    def __post_init__(self):
        if self.reducer not in ["min", "max", "mean", "median", "mode", "sum"]:
            raise ValueError("Reducer must be min, max, mean, median, mode, or sum.")

@dataclass
class RasterConfig:
    interval: IntervalType
    model: ModelType
    variable: VariableType
    reference_et: ReferenceType
    file_format: FileType
    units: UnitType
    
    overpass: bool = False
    
    geometry: _GeometryType | None = None
    date_range: DateRange | None = None
    polygon: PolygonConfig | None = None
    
    def __kv__(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}
    
    def __post_init__(self):
        if self.interval not in ["daily", "monthly"]:
            raise ValueError("Interval must be daily or monthly.")
        
        if self.reference_et not in ["cimis", "gridmet", "fret"]:
            raise ValueError("Reference ET must be cimis, gridmet, or fret.")
        
        if self.file_format not in ["csv", "json"]:
            raise ValueError("Format must be csv or json.")
        if self.file_format == "csv":
            warnings.warn("CSV format will be deprecated in a future release. Use JSON instead.", FutureWarning, stacklevel=2)
        
        if self.variable not in ["et", "et_mad_min", "et_mad_max", "eto", "etr", "etof", "ndvi", "pr", "count", "model_count"]:
            raise ValueError(f"Unknown variable '{self.variable}' Variable must be et, et_mad_in, et_mad_max, eto, etr, etof, ndvi, pr, count, or model_count.")
        
        if self.model not in ["ensemble", "geesebal", "ssebop", "sims", "disalexi", "ptjpl", "eemetric"]:
            raise ValueError(f"Unknown model '{self.model}'. Model must be ensemble, geesebal, ssebop, sims, disalexi, ptjpl, or eemetric.")
        
        if self.units not in ["mm", "in"]:
            raise ValueError("Units must be mm or in.")
        
        # If overpass is enabled, ensure it can be used with the given model and variable.
        if self.overpass and self.variable != _Overpass_Models[self.model]:
            raise PairValueError(f"Overpass is not supported for {self.model} and {self.variable}.")

@dataclass
class RasterConfigSequence:
    interval: list[IntervalType] | IntervalType
    model: list[ModelType] | ModelType
    variable: list[VariableType] | VariableType
    reference_et: list[ReferenceType] | ReferenceType
    format: list[FileType] | FileType
    units: list[UnitType] | UnitType
    overpass: list[bool] | bool = False
    
    geometry: list[_GeometryType] | _GeometryType | None = None
    date_range: list[DateRange | None] | DateRange | None = None
    polygon: list[PolygonConfig | None] | PolygonConfig | None = None
    
    def __post_init__(self):
        if not isinstance(self.polygon, list):
            self.polygon = [self.polygon]
        if not isinstance(self.interval, list):
            self.interval = [self.interval]
        if not isinstance(self.model, list):
            self.model = [self.model]
        if not isinstance(self.variable, list):
            self.variable = [self.variable]
        if not isinstance(self.reference_et, list):
            self.reference_et = [self.reference_et]
        if not isinstance(self.format, list):
            self.format = [self.format]
        if not isinstance(self.units, list):
            self.units = [self.units]
        if not isinstance(self.geometry, list):
            self.geometry = [self.geometry]
        if not isinstance(self.overpass, list):
            self.overpass = [self.overpass]
        if not isinstance(self.date_range, list):
            self.date_range = [self.date_range]
    
    def __kv__(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}
    
    def iter(self) -> Generator[RasterConfig, None, None]:
        keys, values = zip(*self.__kv__().items())
        
        for v in product(*values):
            try:
                yield RasterConfig(**dict(zip(keys, v)))
            except PairValueError:
                continue
