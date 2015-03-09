import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys

def main():
    startyear = int(sys.argv[1])
    startmonth = int(sys.argv[2])
    startday = int(sys.argv[3])
    endyear = int(sys.argv[4])
    endmonth = int(sys.argv[5])
    endday = int(sys.argv[6])
    symbol1 = sys.argv[7]
    symbol2 = sys.argv[8]
    symbol3 = sys.argv[9]
    symbol4 = sys.argv[10]

    symbols = [symbol1, symbol2, symbol3, symbol4]
    startDate = dt.datetime(startyear, startmonth, startday)
    endDate = dt.datetime(endyear, endmonth, endday)
    c_dataobj = da.DataAccess('Yahoo', cachestalltime=0)
    keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    timeOfDay = dt.timedelta(hours=16)
    timeStamps = du.getNYSEdays(startDate, endDate, timeOfDay)
    data = c_dataobj.get_data(timeStamps, symbols, keys)
    dataDict = dict(zip(keys, data))
    price = dataDict['close'].values
    priceNormalized = price / price[0, :]
    
    def cumulativeReturnsCalculator(t, portfolioReturns):
        if t == 0:
            return (1 + portfolioReturns[0]);
        return (cumulativeReturnsCalculator(t-1, portfolioReturns) * (1 + portfolioReturns[t]))

    def statsCalculator(priceNormalized, weights):
        priceWeighted = priceNormalized.copy() * weights;
        portfolioValue = priceWeighted.copy().sum(axis=1);
        portfolioReturns = portfolioValue.copy()
        tsu.returnize0(portfolioReturns)
        volatility = np.std(portfolioReturns)
        averageReturns = np.mean(portfolioReturns)
        sharpeRatio = (averageReturns / volatility) * np.sqrt(252)
        cumulativeReturns = cumulativeReturnsCalculator(portfolioReturns.size - 1, portfolioReturns)
        return [volatility, averageReturns, sharpeRatio, cumulativeReturns, portfolioValue]
    
    def simulate(startDate, endDate, symbols, weights):
        timeOfDay = dt.timedelta(hours=16)
        timeStamps = du.getNYSEdays(startDate, endDate, timeOfDay)
        data = c_dataobj.get_data(timeStamps, symbols, keys)
        dataDict = dict(zip(keys, data))
        price = dataDict['close'].values
        priceNormalized = price / price[0, :]
        keyStats = statsCalculator(priceNormalized, weights)
        return keyStats

    weights = []
    weightTotal = 10
    for i in range(0, weightTotal + 1):
        for j in range(0, weightTotal - i + 1):
            for k in range(0, weightTotal - i - j + 1):
                for l in range(0, weightTotal - i - j - k + 1):
                    if i + j + k + l == 10:
                        weights.append([i, j, k, l])

    maxSharpeRatio = 0.0
    optimalKeyStats = []
    optimalWeights = []
    for item in weights:
        keyStats = statsCalculator(priceNormalized, [i / 10.0 for i in item])
        sharpeRatio = keyStats[2]
        if sharpeRatio > maxSharpeRatio:
            maxSharpeRatio = sharpeRatio
            optimalKeyStats = keyStats
            optimalWeights = [i / 10.0 for i in item]

    spxData = c_dataobj.get_data(timeStamps, ['$SPX'], keys)
    spxDataDict = dict(zip(keys, spxData))
    spxPrice = spxDataDict['close'].values
    spxPriceNormalized = spxPrice / spxPrice[0, : ]
    spxKeyStats = statsCalculator(spxPriceNormalized, [1])
    plt.clf()
    plt.plot(timeStamps, spxKeyStats[4])
    plt.plot(timeStamps, optimalKeyStats[4])
    plt.axhline(y=0, color='green');
    plt.legend(['SPX', 'Portfolio']);
    plt.ylabel('Normalized Value');
    plt.xlabel('Date');
    plt.savefig('comparison.png', format='png')

    print('Start Date: ' + startDate.strftime('%B') + ' ' + str(startday) + ', ' + str(startyear))
    print('End Date: ' + endDate.strftime('%B') + ' ' + str(endday) + ', ' + str(endyear))
    print('Symbols: ' + str(symbols))
    print('Optimal Allocations: ' + str(optimalWeights))
    print('Sharpe Ratio: ' + str(maxSharpeRatio))
    print('Volatility (stdev of daily returns): ' + str(optimalKeyStats[0]))
    print('Average Daily Return: ' + str(optimalKeyStats[1]))
    print('Cumulative Return: ' + str(optimalKeyStats[3]))
    
if __name__ == '__main__':
    main()