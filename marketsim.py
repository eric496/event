import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import operator
import sys
import csv

if __name__ == '__main__':
    #read in arguments from command line
    cash = float(sys.argv[1])
    infile_path = sys.argv[2]
    outfile_path = sys.argv[3]    

    #lists to store values from the input data
    ls_datetime = []
    ls_symbols = []
    ls_types = []
    ls_volume = []
    
    #read in orders
    reader = csv.reader(open(infile_path, 'rU'), delimiter = ',')
    for row in reader:
        #input file structure: col1: year, col2: month, col3: day, col4: symbol, col5: order, col6: volume
        ls_datetime.append(dt.datetime(int(row[0]), int(row[1]), int(row[2]), 16, 00, 00))
        ls_symbols.append(row[3])
        if row[4] == 'Buy':
            ls_types.append(-1)
        elif row[4] == 'Sell':
            ls_types.append(1)
        ls_volume.append(row[5])
        
    #create the order dataframe
    order_data = {'datetime': ls_datetime, 'symbol': ls_symbols, 'type': ls_types, 'volume': ls_volume}
    df_orders = pd.DataFrame(order_data)
    
    #get unique symbols
    ls_symbols = list(set(ls_symbols))

    #generate start and end date from the date list
    dt_start = df_orders.datetime[0]
    dt_end = df_orders.datetime[len(df_orders) - 1]

    #read NYSE data
    dt_timeofday = dt.timedelta(hours = 16)
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end + dt.timedelta(days = 1), dt_timeofday)
    c_dataobj = da.DataAccess('Yahoo', cachestalltime = 0)
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))

    #remove NAN value
    for key in ls_keys:
        d_data[key] = d_data[key].fillna(method='ffill')
        d_data[key] = d_data[key].fillna(method='bfill')
        d_data[key] = d_data[key].fillna(1.0)

    #get the close price
    na_prices = d_data['close'].values

    #calculate summary statistics
    holdings = {}
    na_daily_values = np.zeros([len(ldt_timestamps), 4])
    for symbol in ls_symbols:
        holdings[symbol] = 0
    values = np.zeros((len(ldt_timestamps), len(ls_symbols)))
    port_values = []
    for dt in ldt_timestamps:
        ldt_ix = ldt_timestamps.index(dt)
        for i in range(len(df_orders)):
            if dt.date() == df_orders.ix[i]['datetime'].date():
                symbol = df_orders.ix[i]['symbol']
                type = df_orders.ix[i]['type']
                volume = df_orders.ix[i]['volume']
                symbol_ix = ls_symbols.index(symbol)
                price = na_prices[ldt_ix][symbol_ix]
                if symbol not in holdings:
                    holdings[symbol] = 0
                holdings[symbol] += int(volume) * (-1) * int(df_orders.ix[i]['type'])
                cash += float(price) * int(volume) * int(df_orders.ix[i]['type'])
        for symbol in ls_symbols:
            symbol_ix = ls_symbols.index(symbol)
            values[ldt_ix][symbol_ix] = (na_prices[ldt_ix][symbol_ix] * (float(holdings[symbol])))
        daily_val = np.sum(np.nan_to_num(values[ldt_ix])) + cash
        port_values.append(daily_val)
        na_daily_values[ldt_ix] = [dt.year, dt.month, dt.day, daily_val]

    #output to file
    np.savetxt(outfile_path, na_daily_values[:-1], fmt='%i', delimiter=',')