import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import sys
import csv

if __name__ == '__main__':
    infile_path = sys.argv[1]
    benchmark = sys.argv[2]

    ls_datetime = []
    ls_symbols = ['GOOG', 'AAPL', 'IBM', 'XOM']
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
    for dt in ldt_timestamps:
        idt_ix = ldt_timestamps.index(dt)
        na_daily_values[idt_ix] = [dt.year, dt.month, dt.day, ls_values[idt_ix]]
      
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
    plt.plot(ldt_timestamps, spx_port / spx_port[0] * 1000000)
    plt.plot(ldt_timestamps, ls_values)
    plt.legend([benchmark] + ['portfolio']);
    plt.xlabel('Date')
    plt.ylabel('Portfolio Values')
    plt.title('Portfolio vs Market')
    plt.setp(plt.xticks()[1], rotation = 25)
    plt.savefig('port_peformance.pdf', format = 'pdf')