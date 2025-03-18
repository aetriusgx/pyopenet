from datetime import date
from logging import Logger

from pandas import DataFrame, concat

from .ETRequest import Request, format_csv_response, format_json_response
from .ETTypes import RasterConfigSequence, DateRange

class ETJob:
    def __init__(self, api_key: str) -> None:
        # Private Fields
        self._api_key = api_key
        self._table: DataFrame = DataFrame([])
    
    def get_table(self) -> DataFrame:
        return self._table

    def export(self, path: str = "", file_format: str = "csv", **kwargs):
        if self._table is None:
            raise UnboundLocalError("No table found to export.")
        
        path = path.replace("\\", "/")
        
        match file_format.lower():
            case "csv":
                return self._table.reset_index().to_csv(path, **kwargs)
            case "pkl":
                return self._table.reset_index().to_pickle(path, **kwargs)
            case "json":
                return self._table.reset_index().to_json(path, **kwargs)
            case _:
                raise ValueError(f"File format {file_format} is not supported.")

class RasterTimeseries(ETJob):
    _RETURN_TABLE_COLUMNS = ["date", "model", "variable", "overpass", "reference_et", "units", "value"]
    _POINT_ENDPOINT = "https://developer.openet-api.org/raster/timeseries/point"
    _POLYGON_ENDPOINT = "https://developer.openet-api.org/raster/timeseries/polygon"

    def __init__(
        self,
        options: RasterConfigSequence,
        api_key: str,
        *,
        table: DataFrame, 
        index: str | None = None, 
        geometry: str | None = None,
    ) -> None:
        super().__init__(api_key)

        self.options = options
        
        if not geometry and "geometry" not in table.columns:
            raise KeyError("No geometry column found in DataFrame.")

        if geometry and geometry not in table.columns:
            raise KeyError(f"Geometry column {geometry} not found in DataFrame.")

        if index and index not in table.columns:
            raise KeyError(f"Index column {index} not found in DataFrame.")

        self.endpoint = self._POINT_ENDPOINT if not self.options.polygon else self._POLYGON_ENDPOINT
        
        self.index = index or table.index.name
        self.geometry = geometry or "geometry"
        self.table = (
            table.copy().reset_index().set_index(index)
            if index
            else table.copy()
        )

    def run(self, date: DateRange | list[str | date], logger: Logger | None = None) -> tuple[int, int]:
        success = 0
        fails = 0
        
        for params in self.options.iter():
            clean_params = params.__kv__()
            clean_params["date_range"] = date
            
            for index, row in self.table.iterrows():
                clean_params["geometry"] = row[self.geometry].get("coordinates")
                
                req = Request(
                    endpoint=self._POINT_ENDPOINT,
                    params=clean_params,
                    key=self._api_key,
                    logger=logger
                )
                res = req.send()
                
                if not res:
                    fails += 1
                    continue
                
                if req.success():
                    success += 1
                else:
                    fails += 1
                    continue
            
                data = None
                if clean_params["file_format"] == "csv":
                    data = format_csv_response(res)
                elif clean_params["file_format"] == "json":
                    data = format_json_response(res)
                else:
                    raise ValueError(f"File format {clean_params['file_format']} is not supported.")
                
                # Make index into a list if tuple, otherwise just a list with one element.
                indices = list(index) if isinstance(index, tuple) else [index]
                names = list(self.table.index.names) if self.table.index.names else list(self.table.index.name)
                
                _results = []
                
                for row in data:
                    _results.append({
                        "date": row["time"],
                        "model": clean_params.get("model"), 
                        "variable": clean_params.get("variable"), 
                        "overpass": clean_params.get("overpass"), 
                        "reference_et": clean_params.get("reference_et"), 
                        "units": clean_params.get("units"),
                        "value": row[str(list(row.keys())[1])]
                    })
                
                _results_table = DataFrame.from_records(_results)
                
                # Add index columns.
                for i, n in zip(indices, names):
                    _results_table[n] = i
                
                _results_table = _results_table.set_index(names)
                
                self._table = concat([self._table, _results_table])
        
        return success, fails
            
