from collections import Counter
from math import pi

import numpy as np
import pandas as pd

from bokeh.io import curdoc
from bokeh.layouts import column, gridplot, row
from bokeh.models import (ColumnDataSource, DataTable, NumberFormatter,
                          RangeTool, StringFormatter, TableColumn, HoverTool, Select, Slider, Div)
from bokeh.palettes import Spectral
from bokeh.plotting import figure
from bokeh.transform import cumsum

import json

import time
from datetime import datetime

import pymongo




tokens = ["gzil", "xsgd", "bolt", "zlp" ,"SHRK”]
tokens_upper = ["GZIL", "XSGD", "BOLT", "ZLP”, “SHRK”]

tok_upper_to_down = {"GZIL"  : "gzil", 
                     "XSGD"  : "xsgd", 
                     "BOLT"  : "bolt", 
                     "ZLP"   : "zlp", 
                     "ZYF"   : "zyf", 
                     "SHRK" :  "SHRK"}

_time = {}
_rate = {}
_liq = {}

=======

###########################
### Update Price Chart ####
###########################

class zilgraph:
    def __init__(self):
        self.g_tok = "xsgd"
        self.g_timebase = timebase[1]
        
    def update_chart(self, attrname, old, new):
        self.g_tok = new.split()[-1].lower()
        source.data.update(ohlc[self.g_timebase][self.g_tok])
            
    def update_timebase(self, attrname, old, new):
        self.g_timebase = tb_dict[new]
        source.data.update(ohlc[self.g_timebase][self.g_tok])    

        
###########################
###  Init Price Chart  ####
###########################

mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
mongodb = mongoclient["zilcrawl"]

# Load Zilgraph JSON 
fp_json = open("dash/zilgraph.json")
tokens = json.load(fp_json)["tokens"]

# Setup dictionaries
ohlcdb_1h = {}
ohlcdb_24h = {}
for tok in tokens:
    ohlcdb_1h[tok]  = mongodb["ohlc_1h_" + tok]
    ohlcdb_24h[tok] = mongodb["ohlc_24h_" + tok]

timebase = ["1h", "24h"]
timebase_options = ["Hourly - 1h", "Daily - 24h"]

tb_dict = {timebase_options[0] : "1h",
           timebase_options[1] : "24h"}


ohlcdb = {"1h" : ohlcdb_1h, "24h" : ohlcdb_24h}

ohlc = { "1h" : {}, "24h" : {}}

for tb in ohlcdb:
    for tok in tokens:
        for x in ohlcdb[tb][tok].find().sort('_id'):
            if tok not in ohlc[tb]:
                ohlc[tb][tok] = {}
                ohlc[tb][tok]['time']    = x['time']
                ohlc[tb][tok]['open']    = x['open']
                ohlc[tb][tok]['high']    = x['high']
                ohlc[tb][tok]['low']     = x['low']
                ohlc[tb][tok]['close']   = x['close']
                ohlc[tb][tok]['average'] = x['average']
                ohlc[tb][tok]['color']   = x['color']
    
            ohlc[tb][tok]['time'].append(x['time'][0])
            ohlc[tb][tok]['open'].append(x['open'][0])
            ohlc[tb][tok]['high'].append(x['high'][0])
            ohlc[tb][tok]['low'].append(x['low'][0])
            ohlc[tb][tok]['close'].append(x['close'][0])
            ohlc[tb][tok]['average'].append(x['average'][0])
            ohlc[tb][tok]['color'].append(x['color'][0])
            
        
mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
mongodb = mongoclient["zilcrawl"]

source = ColumnDataSource(dict(time=[], average=[], low=[], high=[], open=[], close=[], color=[]))

p = figure(plot_height=200, tools="pan,wheel_zoom,box_zoom,reset", x_axis_type="datetime", y_axis_location="right")
p.x_range.follow = "end"
p.x_range.follow_interval = 10000000000
p.x_range.range_padding = 0

p.line(x='time', y='average', alpha=0.2, line_width=3, color='navy', source=source)
p.line(x='time', y='ma', alpha=0.8, line_width=2, color='orange', source=source)
p.segment(x0='time', y0='low', x1='time', y1='high', line_width=2, color='black', source=source)
p.segment(x0='time', y0='open', x1='time', y1='close', line_width=8, color='color', source=source)

layout = column(p, sizing_mode="scale_width", name="line")

curdoc().add_root(layout)

z = zilgraph()
z.update_chart('tok', 'XSGD', 'XSGD')

# Streaming
#for x in ohlcdb['xsgd'].find().sort('_id'):
#    del x['_id']
#    source.stream(x, 4000)



###########################
###    Dropdown Menu   ####
###########################

dropdown_timebase = Select(value=timebase_options[1], options=timebase_options, name="dropdown_timebase", max_width=150)
dropdown_timebase.on_change('value', z.update_timebase)

tokens_upper = []
for tok in tokens:
    if tokens[tok]["verified"]:
        tokens_upper.append("✓ " + tok.upper())
    else:
        tokens_upper.append(tok.upper())

# UTF-8 Star: ★

dropdown_token = Select(value="✓ XSGD", options=tokens_upper, name="dropdown_token", max_width=150)
dropdown_token.on_change('value', z.update_chart)

curdoc().add_root(dropdown_timebase)
curdoc().add_root(dropdown_token)


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
data['color'] = Spectral[len(tokens)]

region = figure(plot_height=350, toolbar_location=None, outline_line_color=None, sizing_mode="scale_both", name="region", x_range=(-0.5, 0.8))

region.annular_wedge(x=-0, y=1, inner_radius=0.2, outer_radius=0.32,
                  start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                  line_color="white", fill_color='color', legend_group='token', source=data)

region.axis.axis_label=None
region.axis.visible=False
region.grid.grid_line_color = None
region.legend.label_text_font_size = "1.5em"
region.legend.spacing = 5
region.legend.glyph_height = 20
region.legend.label_height = 20

# configure so that no drag tools are active
region.toolbar.active_drag = None


###########################
###        Table       ####
###########################

table_dict = {}
table_dict["tok"]  = []
table_dict["rate"] = []
table_dict["liq"]  = []
for tok in tokens:
    table_dict["tok"].append(tok.upper())
    table_dict["rate"].append(round(_rate[tok][-1],2))
    table_dict["liq"].append(int(_liq[tok][-1]))


pdsource = ColumnDataSource(data=pd.DataFrame(table_dict))

columns = [
    TableColumn(field="tok", title="Token", formatter=StringFormatter(text_align="center")),
    TableColumn(field="rate", title="Price [ZIL]",  formatter=StringFormatter(text_align="center")),
    TableColumn(field="liq", title="Liquitidy [ZIL]", formatter=NumberFormatter(text_align="center")),
]
table = DataTable(source=pdsource, columns=columns, height=193, width=330, name="table", sizing_mode="scale_both")

#layout = row(region, table)
curdoc().add_root(region)
curdoc().add_root(table)


###########################
###        Setup       ####
###########################


# Calculate change
total_liq_change = 0.01
xsgd_liq_change = 0.01
pairs_change = 150.0

#ohlc["24h"]['gzil']['time'][-1]
#ohlc["24h"]['gzil']['close'][-1]
gzil_rate = ohlc["24h"]['gzil']['close'][-1]
gzil_rate_1wk = ohlc["24h"]['gzil']['close'][-8]

gzil_change = round((gzil_rate / gzil_rate_1wk - 1)*100, 2)

curdoc().title = "Zilgraph - A Zilswap Dashboard"
curdoc().template_variables['stats_names'] = ['total_liq', 'xsgd_liq', 'pairs', 'sales']
curdoc().template_variables['stats'] = {
    'total_liq' : {'icon': 'user',        'value': str(int(total_liq)) + " ZIL", 'change':  total_liq_change   , 'label': 'Total Liquidity'},
    'xsgd_liq'  : {'icon': 'user',        'value': str(int(_liq['xsgd'][-1])) + " ZIL",   'change':  xsgd_liq_change , 'label': 'XSGD Liquidity'},
    'pairs'     : {'icon': 'user',        'value': len(tokens), 'change':  pairs_change , 'label': 'Tokens'},
    'sales'     : {'icon': 'dollar',      'value': str(int(gzil_rate)) + " ZIL",  'change': gzil_change , 'label': 'gZIL Token Price'},
}

#_rate['gzil'][-1])



















