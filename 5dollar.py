import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da
import datetime as dt
import numpy as np
import pandas as pd
import copy
import csv
import QSTK.qstkutil.tsutil as tsu
import matplotlib.pyplot as plt

if __name__ == '__main__':
    sp_source = 'sp5002012'
    ls_start = [2008, 1, 1]
    ls_end = [2009, 12, 31]
    event_price = 5.0
    order_volume = 100
    ls_order_symbol = []
    lookback_days = 20
    lookforward_days = 20
    dt_start = dt.datetime(ls_start[0], ls_start[1], ls_start[2])
    dt_end = dt.datetime(ls_end[0], ls_end[1], ls_end[2])
    dt_timeofday = dt.timedelta(hours = 16)
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)
    dataobj = da.DataAccess('Yahoo', cachestalltime = 0)
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    
    #def event_profiler(sp_source):
    ls_symbols = dataobj.get_symbols_from_list(sp_source)
    ls_symbols.append('SPY')
    ldf_data = dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys);
    d_data = dict(zip(ls_keys, ldf_data))

    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method = 'ffill')
        d_data[s_key] = d_data[s_key].fillna(method = 'bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)

    df_close = d_data['actual_close']
    market_price = df_close['SPY']
    df_events = copy.deepcopy(df_close)
    df_events = df_events * np.NAN

    ls_order_year = []
    ls_order_month = []
    ls_order_day = []
    ls_order_type = []
    ls_order_volume = []
    for symbol in ls_symbols:
        for i in range(1, len(ldt_timestamps)):
            symbol_price_today = df_close[symbol].ix[ldt_timestamps[i]]
            symbol_price_yesterday = df_close[symbol].ix[ldt_timestamps[i - 1]]
            market_price_today = market_price.ix[ldt_timestamps[i]]
            market_price_yesterday = market_price.ix[ldt_timestamps[i - 1]]
            if symbol_price_yesterday >= 5.0 and symbol_price_today < 5.0:
                df_events[symbol].ix[ldt_timestamps[i]] = 1
                ls_order_year.append(ldt_timestamps[i].year)
                ls_order_month.append(ldt_timestamps[i].month)
                ls_order_day.append(ldt_timestamps[i].day)
                ls_order_symbol.append(symbol)
                ls_order_type.append('Buy')
                ls_order_volume.append(order_volume)

                ls_order_year.append(ldt_timestamps[i + 5].year)
                ls_order_month.append(ldt_timestamps[i + 5].month)
                ls_order_day.append(ldt_timestamps[i + 5].day)
                ls_order_symbol.append(symbol)
                ls_order_type.append('Sell')
                ls_order_volume.append(order_volume)
    d_orders = {'year': ls_order_year, 'month': ls_order_month, 'day': ls_order_day, 'symbol': ls_order_symbol, 'type': ls_order_type, 'volume': ls_order_volume}
    df_orders = pd.DataFrame(d_orders)
    df_orders.sort_index(by = ['year', 'month', 'day'], inplace = True)
    ls_df_order = ['year', 'month', 'day', 'symbol', 'type', 'volume']
    df_orders = df_orders[ls_df_order]
    df_orders.to_csv('orderstest.csv', index = False, header = False)

    #def marketsim():
    cash = float(50000)
    infile_path = "orderstest.csv"
    outfile_path = "valuestest.csv"
    
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
    for ts in ldt_timestamps:
        ldt_ix = ldt_timestamps.index(ts)
        for i in range(len(df_orders)):
            if ts.date() == df_orders.ix[i]['datetime'].date():
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
        na_daily_values[ldt_ix] = [ts.year, ts.month, ts.day, daily_val]

    #output to file
    np.savetxt(outfile_path, na_daily_values[:-1], fmt='%i', delimiter=',')

    #def analyze():
    benchmark = '$SPX'
    infile_path = 'valuestest.csv'

    ls_datetime = []
    ls_symbols = list(set(ls_order_symbol))
    ls_values = []

    reader = csv.reader(open(infile_path, 'rU'), delimiter = ',')
    for row in reader:
        ls_datetime.append(dt.datetime(int(row[0]), int(row[1]), int(row[2]), 16, 00, 00))
        ls_values.append(row[3])
    dt_start = ls_datetime[0]
    dt_end = ls_datetime[-1]

    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    dt_timeofday = dt.timedelta(hours = 16)
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)
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

    na_daily_values = np.zeros([len(ldt_timestamps), 4])
    for ts in ldt_timestamps:
        idt_ix = ldt_timestamps.index(ts)
        na_daily_values[idt_ix] = [ts.year, ts.month, ts.day, ls_values[idt_ix]]
      
    port_total_rets = na_daily_values[-1, 3] / na_daily_values[0, 3]
    port_daily_rets = na_daily_values.copy()[:, 3]
    tsu.returnize0(port_daily_rets)
    port_std = np.std(port_daily_rets)
    port_avg_daily_rets = np.average(port_daily_rets)
    port_sharpe_ratio = (port_avg_daily_rets / port_std * np.sqrt(252))

    data = c_dataobj.get_data(ldt_timestamps, [benchmark], ls_keys)
    dict_data = dict(zip(ls_keys, data))
    spx_prices = dict_data['close'].values
    spx_port = spx_prices[:, 0]
    spx_daily_rets = spx_port.copy()
    tsu.returnize0(spx_daily_rets)
    spx_total_rets = spx_port[-1] / spx_port[0]
    spx_std = np.std(spx_daily_rets)
    spx_avg_daily_rets = np.average(spx_daily_rets)
    spx_sharpe_ratio = (spx_avg_daily_rets / spx_std * np.sqrt(252))


    #print result of analysis
    print "The final value of the portfolio using the sample file is -- {0}, {1}, {2}, {3}".format(dt_end.year, dt_end.month, dt_end.day, int(round(na_daily_values[-1][-1])))
    print "Details of the Performance of the portfolio"
    print ""
    print "Data Range :", dt_start ," to ", dt_end
    print ""
    print "Sharpe Ratio of Fund :", port_sharpe_ratio
    print "Sharpe Ratio of $SPX :", spx_sharpe_ratio
    print ""
    print "Total Return of Fund :", port_total_rets
    print "Total Return of $SPX :", spx_total_rets
    print ""
    print "Standard Deviation of Fund :", port_std
    print "Standard Deviation of $SPX :", spx_std
    print ""
    print "Average Daily Return of Fund :", port_avg_daily_rets
    print "Average Daily Return of $SPX :", spx_avg_daily_rets

    #plot
    plt.clf()
    plt.plot(ldt_timestamps, spx_port / spx_port[0] * cash)
    plt.plot(ldt_timestamps, ls_values)
    plt.legend([benchmark] + ['portfolio']);
    plt.xlabel('Date')
    plt.ylabel('Portfolio Values')
    plt.title('Portfolio vs Market')
    plt.setp(plt.xticks()[1], rotation = 25)
    plt.savefig('port_peformance.pdf', format = 'pdf')