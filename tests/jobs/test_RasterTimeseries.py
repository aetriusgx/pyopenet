from copy import copy

import logging
import pandas as pd
import pandas.testing as pdtest
import pytest
from requests_mock import Mocker
import sys

from pyopenet.ETJob import RasterTimeseries
from pyopenet.ETTypes import PolygonConfig, RasterConfigSequence
from pyopenet.ETUtils import parse_geo

# todos:
# - csv, pkl, json exports
# - good job run with 1 retry
# - good job run with a failure


class TestRasterTimeseries:
    @pytest.fixture(scope="class")
    def setup(self, cleandir):
        cwd = cleandir
        default_options = RasterConfigSequence(
            interval="monthly",
            model="ensemble",
            variable="et",
            reference_et="cimis",
            file_format=["csv", "json"],
            units="mm",
        )

        in_data = pd.read_csv(f"{cwd}/tests/static/points.csv")
        in_data[".geo"] = parse_geo(in_data[".geo"])
        
        out_data = pd.read_csv(f"{cwd}/tests/static/raster_timeseries_out.csv")

        response_mock = [
            # CSV responses.
            {"status_code": 200, "content": 
                b"""time,et\n2023-06-01,0.12"""},
            {"status_code": 200, "content": b"time,et\n2023-06-01,0.15"},
            {"status_code": 200, "content": b"time,et\n2023-06-01,0.13"},
            # JSON responses.
            {"status_code": 200, "content": b'[{"time": "2023-06-01", "et": 0.12}]'},
            {"status_code": 200, "content": b'[{"time": "2023-06-01", "et": 0.15}]'},
            {"status_code": 200, "content": b'[{"time": "2023-06-01", "et": 0.13}]'},
        ]
        
        std_out = logging.StreamHandler(sys.stdout)
        std_out.setLevel(logging.DEBUG)
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(name)s] %(asctime)s - %(levelname)s - %(message)s",
            handlers=[std_out],
        )
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        yield default_options, in_data, out_data, response_mock, logger

    def test_init_point(self, setup):
        options, in_data, out_data, response_mock, logger = setup
        job = RasterTimeseries(
            options=options, api_key="test", table=in_data, geometry=".geo"
        )

        assert job.get_table().empty
        assert job.endpoint == RasterTimeseries._POINT_ENDPOINT

        with pytest.raises(UnboundLocalError):
            job.export()

        job._table = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

        with pytest.raises(ValueError) as err:
            job.export(file_format="txt")
        assert "File format txt is not supported." in str(err.value)

    def test_init_polygon(self, setup):
        options, in_data, out_data, response_mock, logger = setup
        options = copy(options)
        options.polygon = PolygonConfig(reducer="mean")

        job = RasterTimeseries(
            options=options, api_key="test", table=in_data, geometry=".geo"
        )

        assert job.get_table().empty
        assert job.endpoint == RasterTimeseries._POLYGON_ENDPOINT

    def test_init_no_geometry(self, setup):
        options, in_data, out_data, response_mock, logger = setup
        in_data = in_data.copy()
        del in_data[".geo"]

        with pytest.raises(KeyError) as err:
            RasterTimeseries(options=options, api_key="test", table=in_data)

        assert "No geometry column found in DataFrame." in str(err.value)

    def test_init_geometry_not_in_table(self, setup):
        options, in_data, out_data, response_mock, logger = setup
        in_data = in_data.copy()
        del in_data[".geo"]

        with pytest.raises(KeyError) as err:
            RasterTimeseries(
                options=options, api_key="test", table=in_data, geometry=".geo"
            )

        assert "Geometry column .geo not found in DataFrame." in str(err.value)

    def test_init_no_index(self, setup):
        options, in_data, out_data, response_mock, logger = setup
        in_data = in_data.copy()

        with pytest.raises(KeyError) as err:
            RasterTimeseries(
                options=options,
                api_key="test",
                table=in_data,
                index="index",
                geometry=".geo",
            )

        assert "Index column index not found in DataFrame." in str(err.value)

    def test_run_point(self, setup, requests_mock: Mocker):
        options, in_data, out_data, response_mock, logger = setup
        in_data = in_data.copy().set_index(["OPENET_ID", "CROP_2023"])
        
        job = RasterTimeseries(
            options=options, api_key="test", table=in_data, geometry=".geo"
        )

        requests_mock.post(job.endpoint, response_list=response_mock)

        success, fails = job.run(date=["2023-06-01", "2023-06-30"], logger=logger)
        
        assert success == 6
        assert fails == 0
        
        table = job.get_table()
        assert table is not None
        
        pdtest.assert_frame_equal(table.reset_index(), out_data, check_dtype=False, check_like=True, check_index_type=False)
