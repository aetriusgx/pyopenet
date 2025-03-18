from pyopenet.ETUtils import parse_geo

import json
import pandas as pd

def test_parse_geo(cleandir):
    cwd = cleandir
    table = pd.read_csv(f"{cwd}/tests/static/points.csv")
    
    # make a copy of the original geo column.
    og_geo_column = table.copy()[".geo"]
    
    table[".geo"] = parse_geo(table[".geo"])
    
    # Convert both to lists for easier checking.
    og_geo_column = og_geo_column.tolist()
    new_geo_column = table[".geo"].tolist()
    
    assert len(og_geo_column) == len(new_geo_column)
    
    for og, new in zip(og_geo_column, new_geo_column):
        assert json.loads(og) == new
    