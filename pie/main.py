from collections import Counter
from math import pi

import numpy as np
import pandas as pd

from bokeh.io import curdoc
from bokeh.layouts import column, gridplot, row
from bokeh.models import (ColumnDataSource, DataTable, NumberFormatter,
                          RangeTool, StringFormatter, TableColumn, HoverTool, Select, Slider, Div)
from bokeh.palettes import Category20
from bokeh.plotting import figure
from bokeh.transform import cumsum

import json

import time
from datetime import datetime

import pymongo



        
###########################
###  Init Price Chart  ####
###########################

mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
mongodb = mongoclient["zilcrawl"]

# Load Zilgraph JSON 
fp_json = open("zilswap/zilgraph.json")
tokens = json.load(fp_json)["tokens"]


###########################
###    Donut chart     ####
###########################


# Configure MongoDB
mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
mongodb = mongoclient["zillog"]

# Legacy dictionaries (to be replaced)
_liq = {}
_rate = {}
for tok in tokens:
    _liq[tok] = []
    _rate[tok] = []
    
for tok in tokens:
    for x in mongodb[tok].find().sort('_id'):
        _liq[tok].append(x['liq_zil'])
        _rate[tok].append(x['rate'])
        
pie_dict = {}
for tok in tokens:
    pie_dict[tok.upper()] = int(_liq[tok][-1])

print(pie_dict)

x = Counter(pie_dict)
total_liq = sum(x.values())

data = pd.DataFrame.from_dict(dict(x), orient='index').reset_index().rename(index=str, columns={0:'value', 'index':'token'})
data['angle'] = data['value']/total_liq * 2*pi
data['color'] = Category20[len(tokens)]

region = figure(plot_height=420, toolbar_location=None, outline_line_color=None, sizing_mode="scale_both", name="region", x_range=(-0.5, 0.8))

region.annular_wedge(x=-0, y=1, inner_radius=0.2, outer_radius=0.32,
                  start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                  line_color="white", fill_color='color', legend_group='token', source=data)

region.axis.axis_label=None
region.axis.visible=False
region.grid.grid_line_color = None
region.legend.label_text_font_size = "1.5em"
region.legend.spacing = 2
region.legend.glyph_height = 20
region.legend.label_height = 16

# configure so that no drag tools are active
region.toolbar.active_drag = None

curdoc().add_root(region)


curdoc().title = "Zilgraph - A Zilswap Dashboard"
