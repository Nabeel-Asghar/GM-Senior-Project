from sqlalchemy import true
import DataForecast
from datetime import datetime
from scipy.stats import t
from dbEngine import DBEngine
import pandas as pd
import numpy


def accuracy(self):
    query = 'SELECT * FROM dbo_algorithmmaster'
    algorithm_df = pd.read_sql_query(query, self.engine)

    query = 'SELECT * FROM dbo_instrumentmaster'
    instrument_master_df = pd.read_sql_query(query, self.engine)

    # Changes algorithm code
    for code in range(len(algorithm_df)):
        # Dynamic range for changing instrument ID starting at 1
        for ID in range(1, len(instrument_master_df) + 1):
            query = 'SELECT * FROM dbo_algorithmforecast AS a, dbo_instrumentstatistics AS b WHERE a.forecastdate = b.date AND' \
                    ' a.instrumentid = %d AND b.instrumentid = %d AND a.algorithmcode = "%s"' % (
                        ID, ID, algorithm_df['algorithmcode'][code])
            df = pd.read_sql_query(query, self.engine)
            count = 0
            # Calculates accuracy
            for x in range((len(df) - 1)):
                # Check if upward or downward trend
                if (df['close'][x + 1] > df['close'][x] and df['forecastcloseprice'][x + 1] > df['forecastcloseprice'][
                    x]) or \
                        (df['close'][x + 1] < df['close'][x] and df['forecastcloseprice'][x + 1] <
                         df['forecastcloseprice'][
                             x]):
                    count += 1


            # Populates absolute_percent_error with the calculated percent error for a specific data point
            absolute_percent_error = []
            for i in range(len(df)):
                absolute_percent_error.append(
                    abs((df['close'].loc[i] - df['forecastcloseprice'].loc[i]) / df['close'].loc[i]))

            # Calculate sum of percent error and find average
            average_percent_error = 0
            for i in absolute_percent_error:
                average_percent_error = average_percent_error + i
            average_percent_error = average_percent_error / len(df)

            # return the average percent error calculated above
            print("Average percent error for instrument: %d and algorithm: %s " % (ID, algorithm_df['algorithmcode'][code]), average_percent_error)
            #print('Algorithm:', algorithm_df['algorithmcode'][code])
            #print('instrumentid: %d' % ID, instrument_master_df['instrumentname'][ID - 1])
            #print('length of data is:', len(df))
            #print('number correct: ', count)
            d = len(df)
            b = (count / d) * 100
            #print('The accuracy is: %.2f%%\n' % b)


def arima_accuracy(self):
    query = 'SELECT * FROM dbo_algorithmforecast AS a, dbo_instrumentstatistics AS b WHERE a.forecastdate = b.date AND' \
            ' a.instrumentid = 1 AND b.instrumentid = 1 AND a.algorithmcode = "ARIMA"'
    df = pd.read_sql_query(query, self.engine)
    df = df.tail(10)
    df = df.reset_index(drop=true)

    #print(df)
    arima_count = 0
    for x in range((len(df) - 1)):
        # Check if upward or downward trend
        if df['close'][x + 1] > df['close'][x] and df['forecastcloseprice'][x + 1] > df['forecastcloseprice'][x] \
                or (df['close'][x + 1] < df['close'][x] and df['forecastcloseprice'][x + 1] < df['forecastcloseprice'][x]):
            arima_count += 1
    #print(df['close'], df['forecastcloseprice'])
    #print(arima_count)
    #print(arima_count/len(df))

''' Currently a work in progress
def MSF1_accuracy(self):
    n = 9
    print("hello")
    #Gets the macro economic variables codes and names to loop through the inidividual macro variables
    query = "SELECT macroeconcode, macroeconname FROM dbo_macroeconmaster WHERE activecode = 'A'"
    data = pd.read_sql_query(query, self.engine)
    macrocodes = []
    indicators = {}
    for i in range(len(data['macroeconcode'])):
        macrocodes.append(data['macroeconcode'].loc[i])
        d = {data['macroeconcode'].loc[i]: []}
        indicators.update(d)
    #Gets the instrument ids to loop through the individual instruments
    query = 'SELECT instrumentid, instrumentname FROM dbo_instrumentmaster'
    data = pd.read_sql_query(query, self.engine)
    instrumentids = []
    for i in data['instrumentid']:
        instrumentids.append(i)
    #Loops through each instrument id to preform error calculations 1 instrument at a time
    for i in instrumentids:
        #Gets the instrument statistics to run through the function
        query = "SELECT date, close, instrumentid FROM ( SELECT date, close, instrumentID, ROW_NUMBER() OVER " \
                "(PARTITION BY YEAR(date), MONTH(date) ORDER BY DAY(date) DESC) AS rowNum FROM " \
                "dbo_instrumentstatistics WHERE instrumentid = {} AND date BETWEEN '2016-01-01' AND '2018-01-01' ) z " \
                "WHERE rowNum = 1 AND ( MONTH(z.date) = 3 OR MONTH(z.date) = 6 OR MONTH(z.date) = 9 OR " \
                "MONTH(z.date) = 12)".format(i)
        train_data = pd.read_sql_query(query, self.engine)
        #Gets the instrument statistics to check against the forecast prices
        query = "SELECT date, close, instrumentid FROM ( SELECT date, close, instrumentID, ROW_NUMBER() OVER " \
                "(PARTITION BY YEAR(date), MONTH(date) ORDER BY DAY(date) DESC) AS rowNum FROM " \
                "dbo_instrumentstatistics WHERE instrumentid = {} AND date BETWEEN '2018-01-01' AND '2020-01-01' ) z " \
                "WHERE rowNum = 1 AND ( MONTH(z.date) = 3 OR MONTH(z.date) = 6 OR MONTH(z.date) = 9 OR " \
                "MONTH(z.date) = 12)".format(i)
        check_data = pd.read_sql_query(query, self.engine)
        #Gets the dates for the future forecast prices so they match the instrument statistics
        dates = []
        for l in check_data['date']:
            dates.append(str(l))
        #Loops through the macro economic variable codes to calculate percent change
        for x in macrocodes:
            #Retrieves macro economic statistics for each macro variables
            query = 'SELECT date, statistics, macroeconcode FROM dbo_macroeconstatistics WHERE macroeconcode = {}'.format('"' + x + '"')
            df = pd.read_sql_query(query,self.engine)  # Executes the query and stores the result in a dataframe variable
            macro = df.tail(n)  # Retrieves the last n rows of the dataframe variable and stores it in GDP, a new dataframe variable
            SP = check_data.tail(n)  # Performs same operation, this is because we only want to work with a set amount of data points for now
            temp = df.tail(n + 1)  # Retrieves the nth + 1 row from the GDP tables so we can calculate percent change of the first GDP value
            temp = temp.reset_index()  # Resets the index so it is easy to work with
            # Converts macro variables to precent change
            macroPercentChange = macro  # Creates a new dataframe variable and initializes to the GDP table of n rows
            macro = macro.reset_index(drop=True)  # Resets the index of the GDP dataframe so it is easy to work with
            SP = SP.reset_index(drop=True)  # Same here
            macroPercentChange = macroPercentChange.reset_index(drop=True)  # And same here as well
            for i in range(0, n):  # Creates a for loop to calculate the percent change
                if (i == 0):  # On the first iteration grab the extra row stored in temp to compute the first GDP % change value of the table
                    macrov = (macro['statistics'][i] - temp['statistics'][i]) / temp['statistics'][i]
                    macroPercentChange['statistics'].iloc[i] = macrov * 100
                else:  # If it is not the first iteration then calculate % change using previous row as normal
                    macrov = (macro['statistics'][i] - macro['statistics'][i - 1]) / macro['statistics'][i - 1]
                    macroPercentChange['statistics'].iloc[i] = macrov * 100
        #Preforms the actual calculations and stores them in an array called calculated forecast
        calculated_forecast = []


        def calc(self, df1, df2, n, x):
            G = 0
            S = 0
            for i in range(n-1):  # Calculates average Macro Variable % change and S&P closing prices over past n days
                G = df1['statistics'][i] + G
                S = df2['close'][i] + S
            G = G / n
            S = S / n  # Divide percent change by 2
            G = G / 100  # Then convert from percent to number
            return (G * 2), S  # And return both values
        G, S = calc(self, macroPercentChange, SP, n, x)                                               #Calculates the average GDP and S&P values for the given data points over n days and performs operations on GDP average
        for k in range(n):
            if x in [2,3,4]:
                S = (S * (-G)) + S
            else:
                S = (S * (G*2)) + S
            calculated_forecast.append([dates[k], SP['instrumentid'][k], data['macroeconcode'][k], S, 'MSF1', 0])                  #Column organization setup according to dbo_macroeconforecast
        #Creates and inserts the forecast dates, instrument ids, calculated forecast prices, and actual close prices into an array
        results = []
        for k in range(n):
            results.append([dates[k], i, calculated_forecast[k], check_data['close'].loc[k]])
        #Creates a dataframe out of the array created above
        df = pd.DataFrame(results, columns=['forecastdate', 'instrumentid', 'forecastcloseprice', 'close'])
        count = 0
        # Calculates accuracy
        percent_error = []
        temp_error = 0
        for x in range((len(df) - 1)):
            # Check if upward or downward trend
            if (df['close'][x + 1] > df['close'][x] and df['forecastcloseprice'][x + 1] > df['forecastcloseprice'][x]) or \
                    (df['close'][x + 1] < df['close'][x] and df['forecastcloseprice'][x + 1] < df['forecastcloseprice'][x]):
                count += 1
            temp_error = abs((df['close'][x] - df['forecastcloseprice'][x]))/df['close']
        #Percent Error calculation
        temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
        absolute_percent_error = [abs(ele) for ele in temp_error]
        percent_error.append(absolute_percent_error)
        print(df['intstrumentid'][i])
        if df['instrumentid'][i] == 1:
            gm_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            gm_absolute_percent_error = [abs(ele) for ele in gm_temp_error]
            #Calculate sum of percent error and find average
            gm_average_percent_error = sum(gm_absolute_percent_error) / 8
            print("Average percent error of MSF1 on GM stock is: ", gm_average_percent_error * 100, "%")
        if df['instrumentid'][i] == 2:
            pfe_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            pfe_absolute_percent_error = [abs(ele) for ele in pfe_temp_error]
            #Calculate sum of percent error and find average
            pfe_average_percent_error = sum(pfe_absolute_percent_error) / 8
            print("Average percent error of MSF1 on PFE stock is: ", pfe_average_percent_error * 100, "%")
        if df['instrumentid'][i] == 3:
            spy_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            spy_absolute_percent_error = [abs(ele) for ele in spy_temp_error]
            #Calculate sum of percent error and find average
            spy_average_percent_error = sum(spy_absolute_percent_error) / 8
            print("Average percent error of MSF1 on S&P 500 stock is: ", spy_average_percent_error * 100, "%")
        if df['instrumentid'][i] == 4:
            xph_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            xph_absolute_percent_error = [abs(ele) for ele in xph_temp_error]
            #Calculate sum of percent error and find average
            xph_average_percent_error = sum(xph_absolute_percent_error) / 8
            print("Average percent error of MSF1 on XPH stock is: ", xph_average_percent_error * 100, "%")
        if df['instrumentid'][i] == 5:
            carz_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            carz_absolute_percent_error = [abs(ele) for ele in carz_temp_error]
            #Calculate sum of percent error and find average
            carz_average_percent_error = sum(carz_absolute_percent_error) / 8
            print("Average percent error of MSF1 on CARZ index stock is: ", carz_average_percent_error * 100, "%")
        if df['instrumentid'][i] == 6:
            tyx_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            tyx_absolute_percent_error = [abs(ele) for ele in tyx_temp_error]
            #Calculate sum of percent error and find average
            tyx_average_percent_error = sum(tyx_absolute_percent_error) / 8
            print("Average percent error of MSF1 on TYX 30-YR bond is: ", tyx_average_percent_error * 100, "%")
        d = len(df)
        b = (count / d) * 100
        #Prints the trend accuracy
        #print('The accuracy for instrument %d: %.2f%%\n' % (i, b))
db_engine = DBEngine().mysql_engine()
#arima_accuracy(db_engine)
#accuracy(db_engine)
'''



def MSF2_accuracy(self):
    n = 8

    #Gets the macro economic variables codes and names to loop through the inidividual macro variables
    query = "SELECT macroeconcode, macroeconname FROM dbo_macroeconmaster WHERE activecode = 'A'"
    data = pd.read_sql_query(query, self.engine)
    macrocodes = []
    indicators = {}
    for i in range(len(data['macroeconcode'])):
        macrocodes.append(data['macroeconcode'].loc[i])
        d = {data['macroeconcode'].loc[i]: []}
        indicators.update(d)

    #Gets the instrument ids to loop through the individual instruments
    query = 'SELECT instrumentid, instrumentname FROM dbo_instrumentmaster'
    data = pd.read_sql_query(query, self.engine)
    instrumentids = []
    for i in data['instrumentid']:
        instrumentids.append(i)

    #Loops through each instrument id to preform error calculations 1 instrument at a time
    for i in instrumentids:

        #Gets the instrument statistics to run through the function
        query = "SELECT date, close, instrumentid FROM ( SELECT date, close, instrumentID, ROW_NUMBER() OVER " \
                "(PARTITION BY YEAR(date), MONTH(date) ORDER BY DAY(date) DESC) AS rowNum FROM " \
                "dbo_instrumentstatistics WHERE instrumentid = {} AND date BETWEEN '2016-01-01' AND '2018-01-01' ) z " \
                "WHERE rowNum = 1 AND ( MONTH(z.date) = 3 OR MONTH(z.date) = 6 OR MONTH(z.date) = 9 OR " \
                "MONTH(z.date) = 12)".format(i)
        train_data = pd.read_sql_query(query, self.engine)

        #Gets the instrument statistics to check against the forecast prices
        query = "SELECT date, close, instrumentid FROM ( SELECT date, close, instrumentID, ROW_NUMBER() OVER " \
                "(PARTITION BY YEAR(date), MONTH(date) ORDER BY DAY(date) DESC) AS rowNum FROM " \
                "dbo_instrumentstatistics WHERE instrumentid = {} AND date BETWEEN '2018-01-01' AND '2020-01-01' ) z " \
                "WHERE rowNum = 1 AND ( MONTH(z.date) = 3 OR MONTH(z.date) = 6 OR MONTH(z.date) = 9 OR " \
                "MONTH(z.date) = 12)".format(i)
        check_data = pd.read_sql_query(query, self.engine)

        #Gets the dates for the future forecast prices so they match the instrument statistics
        dates = []
        for l in check_data['date']:
            dates.append(str(l))

        #Loops through the macro economic variable codes to calculate percent change
        for j in macrocodes:
            #Retrieves macro economic statistics for each macro variables
            query = 'SELECT date, statistics, macroeconcode FROM dbo_macroeconstatistics WHERE macroeconcode = {}'.format(
                '"' + j + '"')
            data = pd.read_sql_query(query, self.engine)

            # For loop to retrieve macro statistics and calculate percent change
            for k in range(n):
                temp = data.tail(n + 1)
                data = data.tail(n)
                if j == k:
                    macrov = (data['statistics'].iloc[k] - temp['statistics'].iloc[0]) / temp['statistics'].iloc[0]
                    indicators[j].append(macrov)
                else:
                    macrov = (data['statistics'].iloc[k] - data['statistics'].iloc[k - 1]) / data['statistics'].iloc[
                        k - 1]
                    indicators[j].append(macrov)

        #Preforms the actual calculations and stores them in an array called calculated forecast
        calculated_forecast = []
        for k in range(n):
            stat = indicators['GDP'][k] * 1 - (indicators['UR'][k] * 0 + indicators['IR'][k] * .5) - (
                        indicators['MI'][k] * indicators['MI'][k])
            stat = (stat * train_data['close'].iloc[k]) + train_data['close'].iloc[k]
            calculated_forecast.append(stat)


        #Creates and inserts the forecast dates, instrument ids, calculated forecast prices, and actual close prices into an array
        results = []
        for k in range(n):
            results.append([dates[k], i, calculated_forecast[k], check_data['close'].loc[k]])

        #Creates a dataframe out of the array created above
        df = pd.DataFrame(results, columns=['forecastdate', 'instrumentid', 'forecastcloseprice', 'close'])
        #print(df)


        count = 0
        # Calculates accuracy
        percent_error = []
        temp_error = 0
        for x in range((len(df) - 1)):
            # Check if upward or downward trend
            if (df['close'][x + 1] > df['close'][x] and df['forecastcloseprice'][x + 1] > df['forecastcloseprice'][x]) or \
                    (df['close'][x + 1] < df['close'][x] and df['forecastcloseprice'][x + 1] < df['forecastcloseprice'][x]):
                count += 1
            temp_error = abs((df['close'][x] - df['forecastcloseprice'][x]))/df['close']

        #Percent Error calculation

        temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
        absolute_percent_error = [abs(ele) for ele in temp_error]
        percent_error.append(absolute_percent_error)
        print(percent_error)

        if df['instrumentid'][i] == 1:
            gm_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            gm_absolute_percent_error = [abs(ele) for ele in gm_temp_error]

            #Calculate sum of percent error and find average

            gm_average_percent_error = sum(gm_absolute_percent_error) / 8
            #print("Average percent error of MSF2 on GM stock is: ", gm_average_percent_error * 100, "%")

        if df['instrumentid'][i] == 2:
            pfe_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            pfe_absolute_percent_error = [abs(ele) for ele in pfe_temp_error]

            #Calculate sum of percent error and find average

            pfe_average_percent_error = sum(pfe_absolute_percent_error) / 8
            #print("Average percent error of MSF2 on PFE stock is: ", pfe_average_percent_error * 100, "%")

        if df['instrumentid'][i] == 3:
            spy_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            spy_absolute_percent_error = [abs(ele) for ele in spy_temp_error]

            #Calculate sum of percent error and find average

            spy_average_percent_error = sum(spy_absolute_percent_error) / 8
            #print("Average percent error of MSF2 on S&P 500 stock is: ", spy_average_percent_error * 100, "%")

        if df['instrumentid'][i] == 4:
            xph_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            xph_absolute_percent_error = [abs(ele) for ele in xph_temp_error]

            #Calculate sum of percent error and find average

            xph_average_percent_error = sum(xph_absolute_percent_error) / 8
            #print("Average percent error of MSF2 on XPH stock is: ", xph_average_percent_error * 100, "%")

        if df['instrumentid'][i] == 5:
            carz_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            carz_absolute_percent_error = [abs(ele) for ele in carz_temp_error]

            #Calculate sum of percent error and find average

            carz_average_percent_error = sum(carz_absolute_percent_error) / 8
            #print("Average percent error of MSF2 on CARZ index stock is: ", carz_average_percent_error * 100, "%")

        if df['instrumentid'][i] == 6:
            tyx_temp_error = (df['close'] - df['forecastcloseprice']) / df['close']
            tyx_absolute_percent_error = [abs(ele) for ele in tyx_temp_error]

            #Calculate sum of percent error and find average

            tyx_average_percent_error = sum(tyx_absolute_percent_error) / 8
            #print("Average percent error of MSF2 on TYX 30-YR bond is: ", tyx_average_percent_error * 100, "%")



        d = len(df)
        b = (count / d) * 100
        #Prints the trend accuracy
        #print('The accuracy for instrument %d: %.2f%%\n' % (i, b))

def create_weightings_MSF2(self):
    keys = {}
    query = "SELECT macroeconcode, macroeconname FROM dbo_macroeconmaster WHERE activecode = 'A'"
    data = pd.read_sql_query(query, self.engine)
    vars = {}
    for i in data['macroeconname']:
        d = {i: []}
        vars.update(d)
    # (vars)
    query = 'SELECT instrumentid, instrumentname FROM dbo_instrumentmaster'
    data1 = pd.read_sql_query(query, self.engine)
    ikeys = {}
    result = {}
    weightings = {}
    for i in data1['instrumentid']:
        d = {i: []}
        result.update(d)
        weightings.update(d)

    currentDate = str(
        datetime.today())  # Initiailizes a variable to represent today's date, used to fetch forecast dates
    currentDate = ("'" + currentDate + "'")

    n = 8
    for i in range(len(data)):
        keys.update({data['macroeconname'].iloc[i]: data['macroeconcode'].iloc[i]})

    for x in range(len(data1)):
        ikeys.update({data1['instrumentname'].iloc[x]: data1['instrumentid'].iloc[x]})

    for i in keys:
        if i in vars:
            query = 'SELECT date, statistics, macroeconcode FROM dbo_macroeconstatistics WHERE macroeconcode = {}'.format(
                '"' + keys[i] + '"')
            data = pd.read_sql_query(query, self.engine)

            # For loop to retrieve macro statistics and calculate percent change
            for j in range(n):
                temp = data.tail(n + 1)
                data = data.tail(n)
                if j == 0:
                    macrov = (data['statistics'].iloc[j] - temp['statistics'].iloc[0]) / temp['statistics'].iloc[0]
                    vars[i].append(macrov)
                else:
                    macrov = (data['statistics'].iloc[j] - data['statistics'].iloc[j - 1]) / \
                             data['statistics'].iloc[j - 1]
                    vars[i].append(macrov)

    for x in ikeys:
        query = "SELECT date, close, instrumentid FROM ( SELECT date, close, instrumentid, ROW_NUMBER() OVER " \
                "(PARTITION BY YEAR(date), MONTH(date) ORDER BY DAY(date) DESC) AS rowNum FROM " \
                "dbo_instrumentstatistics WHERE instrumentid = {} AND date BETWEEN '2016-01-01' AND '2018-01-01' ) z " \
                "WHERE rowNum = 1 AND ( MONTH(z.date) = 3 OR MONTH(z.date) = 6 OR MONTH(z.date) = 9 OR " \
                "MONTH(z.date) = 12)".format(ikeys[x])

        instrumentStats = pd.read_sql_query(query, self.engine)

        instrumentStats = instrumentStats.tail(n)

        avg_percent_errors = []
        best_weightings = [0, 0, 0]
        best_avg_error = -1
        best_trend_error = -1
        for weight in numpy.arange(0, 2, .1):
            for uweight in numpy.arange(0, 1, .1):
                for iweight in numpy.arange(0, 1, .1):
                    stat_check = []
                    for i in range(n):
                        stat = vars['GDP'][i] * weight - (vars['Unemployment Rate'][i] * uweight + vars['Inflation Rate'][i] * iweight) - (
                                    vars['Misery Index'][i] * vars['Misery Index'][i])
                        stat = (stat * instrumentStats['close'].iloc[i]) + instrumentStats['close'].iloc[i]
                        stat_check.append(stat)

                    temp_avg_error, temp_trend_error = weight_check(DBEngine().mysql_engine(), stat_check, ikeys[x], n, 'MSF2')
                    if (best_avg_error < 0):
                        best_avg_error = temp_avg_error
                        best_weightings = [weight, uweight, iweight]
                        best_trend_error = temp_trend_error
                    elif (best_avg_error > temp_avg_error):
                        best_avg_error = temp_avg_error
                        best_weightings = [weight, uweight, iweight]
                        best_trend_error = temp_trend_error
        print("The lowest avg percent error is %.7f%% for instrumentID %d" % (best_avg_error, ikeys[x]), ' for function: MSF2')
        print("The weightings are: ", best_weightings, ' for function: MSF2')
        print('The trend error is: ', best_trend_error)
        weightings[ikeys[x]] = best_weightings

    return weightings

def create_weightings_MSF3(self):
    keys = {}
    query = "SELECT macroeconcode, macroeconname FROM dbo_macroeconmaster WHERE activecode = 'A'"
    data = pd.read_sql_query(query, self.engine)
    vars = {}
    weightings = {}
    for i in data['macroeconcode']:
        if (i == 'GDP' or i == 'COVI' or i == 'CPIUC' or i == 'FSI'):
            d = {i: []}
            vars.update(d)
            weightings.update(d)
    query = 'SELECT instrumentid, instrumentname FROM dbo_instrumentmaster'
    data1 = pd.read_sql_query(query, self.engine)
    ikeys = {}
    result = {}
    for i in data1['instrumentid']:
        d = {i: []}
        result.update(d)

    currentDate = str(datetime.today())  # Initiailizes a variable to represent today's date, used to fetch forecast dates
    currentDate = ("'" + currentDate + "'")

    n = 8
    for i in range(len(data)):
        keys.update({data['macroeconname'].iloc[i]: data['macroeconcode'].iloc[i]})

    for x in range(len(data1)):
        ikeys.update({data1['instrumentname'].iloc[x]: data1['instrumentid'].iloc[x]})

    for i in keys:
        if keys[i] in vars:
            query = 'SELECT date, statistics, macroeconcode FROM dbo_macroeconstatistics WHERE macroeconcode = {}'.format(
                '"' + keys[i] + '"')
            data = pd.read_sql_query(query, self.engine)

            # For loop to retrieve macro statistics and calculate percent change
            for j in range(n):
                temp = data.tail(n + 1)
                data = data.tail(n)
                if j == 0:
                    macrov = (data['statistics'].iloc[j] - temp['statistics'].iloc[0]) / temp['statistics'].iloc[0]
                    vars[keys[i]].append(macrov)
                else:
                    macrov = (data['statistics'].iloc[j] - data['statistics'].iloc[j - 1]) / \
                             data['statistics'].iloc[j - 1]
                    vars[keys[i]].append(macrov)

    for x in ikeys:
        query = "SELECT date, close, instrumentid FROM ( SELECT date, close, instrumentid, ROW_NUMBER() OVER " \
                "(PARTITION BY YEAR(date), MONTH(date) ORDER BY DAY(date) DESC) AS rowNum FROM " \
                "dbo_instrumentstatistics WHERE instrumentid = {} AND date BETWEEN '2016-01-01' AND '2018-01-01' ) z " \
                "WHERE rowNum = 1 AND ( MONTH(z.date) = 3 OR MONTH(z.date) = 6 OR MONTH(z.date) = 9 OR " \
                "MONTH(z.date) = 12)".format(ikeys[x])

        instrumentStats = pd.read_sql_query(query, self.engine)

        instrumentStats = instrumentStats.tail(n)

        avg_percent_errors = []
        best_weightings = [0, 0, 0]
        best_avg_error = -1
        best_trend_error = -1
        for weight in numpy.arange(0, 2, .1):
            for uweight in numpy.arange(0, 1, .1):
                for iweight in numpy.arange(0, 1, .1):
                    stat_check = []
                    for i in range(n):
                        stat = vars['GDP'][i] * weight - (vars['COVI'][i] * uweight + vars['FSI'][i] * iweight) - (
                                    vars['CPIUC'][i] * vars['CPIUC'][i])
                        stat = (stat * instrumentStats['close'].iloc[i]) + instrumentStats['close'].iloc[i]
                        stat_check.append(stat)

                        #MAKE SURE STAT IS BETWEEN 0 and 1

                    temp_avg_error, temp_trend_error = weight_check(DBEngine().mysql_engine(), stat_check, ikeys[x], n, 'MSF3')
                    if (best_avg_error < 0):
                        best_avg_error = temp_avg_error
                        best_weightings = [weight, uweight, iweight]
                        best_trend_error = temp_trend_error
                    elif (best_avg_error > temp_avg_error):
                        best_avg_error = temp_avg_error
                        best_weightings = [weight, uweight, iweight]
                        best_trend_error = temp_trend_error

        #print("The lowest avg percent error is %.7f%% for instrumentID %d" % (best_avg_error, ikeys[x]), ' for function: MSF3')
        #print("The weightings are: ", best_weightings, ' for function: MSF3')
        #print('The trend error is: ',  best_trend_error)

        weightings[ikeys[x]] = best_weightings
    #print(vars)
    return weightings

def weight_check(self, calculated_forecast, instrumentid, n, function_name):
    #Retrieves the actual stock closing prices quarterly from 2018 to 2020 to compare with our calculated forecast prices
    query = "SELECT date, close, instrumentid FROM ( SELECT date, close, instrumentID, ROW_NUMBER() OVER " \
            "(PARTITION BY YEAR(date), MONTH(date) ORDER BY DAY(date) DESC) AS rowNum FROM " \
            "dbo_instrumentstatistics WHERE instrumentid = {} AND date BETWEEN '2018-01-01' AND '2020-01-01' ) z " \
            "WHERE rowNum = 1 AND ( MONTH(z.date) = 3 OR MONTH(z.date) = 6 OR MONTH(z.date) = 9 OR " \
            "MONTH(z.date) = 12)".format(instrumentid)
    check_data = pd.read_sql_query(query, self.engine)

    # Gets the dates for the future forecast prices so they match the instrument statistics
    dates = []
    for l in check_data['date']:
        dates.append(str(l))

    # Creates and inserts the forecast dates, instrument ids, calculated forecast prices, and actual close prices into an array
    results = []
    for k in range(n):
        results.append([dates[k], instrumentid, calculated_forecast[k], check_data['close'].loc[k]])

    # Creates a dataframe out of the array created above
    df = pd.DataFrame(results, columns=['forecastdate', 'instrumentid', 'forecastcloseprice', 'close'])

    #Populates absolute_percent_error with the calculated percent error for a specific data point
    absolute_percent_error = []
    for i in range(n):
        absolute_percent_error.append(abs((df['close'].loc[i] - df['forecastcloseprice'].loc[i]) / df['close'].loc[i]))

    # Calculate sum of percent error and find average
    average_percent_error = 0
    for i in absolute_percent_error:
        average_percent_error = average_percent_error + i
    average_percent_error = average_percent_error/n

    count = 0
    # Calculates accuracy
    for x in range((len(df) - 1)):
        # Check if upward or downward trend
        if (df['close'][x + 1] > df['close'][x] and df['forecastcloseprice'][x + 1] > df['forecastcloseprice'][
            x]) or \
                (df['close'][x + 1] < df['close'][x] and df['forecastcloseprice'][x + 1] <
                 df['forecastcloseprice'][
                     x]):
            count += 1

    d = len(df)
    b = (count / d) * 100




    #print("Trend accuracy for %s is %.2f%%" % (function_name, b))
    #return the average percent error calculated above
    return average_percent_error, b

def t_test(self):

    n = 8

    #Gets the macro economic variables codes and names to loop through the inidividual macro variables
    query = "SELECT macroeconcode, macroeconname FROM dbo_macroeconmaster WHERE activecode = 'A'"
    data = pd.read_sql_query(query, self.engine)
    macrocodes = []
    indicators = {}
    for i in range(len(data['macroeconcode'])):
        macrocodes.append(data['macroeconcode'].loc[i])
        d = {data['macroeconcode'].loc[i]: []}
        indicators.update(d)

    #Gets the instrument ids to loop through the individual instruments
    query = 'SELECT instrumentid, instrumentname FROM dbo_instrumentmaster'
    data = pd.read_sql_query(query, self.engine)
    instrumentids = []
    for i in data['instrumentid']:
        instrumentids.append(i)

    #Loops through each instrument id to preform error calculations 1 instrument at a time
    for i in instrumentids:

        #Gets the instrument statistics to run through the function
        query = "SELECT date, close, instrumentid FROM ( SELECT date, close, instrumentID, ROW_NUMBER() OVER " \
                "(PARTITION BY YEAR(date), MONTH(date) ORDER BY DAY(date) DESC) AS rowNum FROM " \
                "dbo_instrumentstatistics WHERE instrumentid = {} AND date BETWEEN '2016-01-01' AND '2018-01-01' ) z " \
                "WHERE rowNum = 1 AND ( MONTH(z.date) = 3 OR MONTH(z.date) = 6 OR MONTH(z.date) = 9 OR " \
                "MONTH(z.date) = 12)".format(i)
        train_data = pd.read_sql_query(query, self.engine)

        #Gets the instrument statistics to check against the forecast prices
        query = "SELECT date, close, instrumentid FROM ( SELECT date, close, instrumentID, ROW_NUMBER() OVER " \
                "(PARTITION BY YEAR(date), MONTH(date) ORDER BY DAY(date) DESC) AS rowNum FROM " \
                "dbo_instrumentstatistics WHERE instrumentid = {} AND date BETWEEN '2018-01-01' AND '2020-01-01' ) z " \
                "WHERE rowNum = 1 AND ( MONTH(z.date) = 3 OR MONTH(z.date) = 6 OR MONTH(z.date) = 9 OR " \
                "MONTH(z.date) = 12)".format(i)
        check_data = pd.read_sql_query(query, self.engine)

        #Gets the dates for the future forecast prices so they match the instrument statistics
        dates = []
        for l in check_data['date']:
            dates.append(str(l))

        #Loops through the macro economic variable codes to calculate percent change
        for j in macrocodes:
            #Retrieves macro economic statistics for each macro variables
            query = 'SELECT date, statistics, macroeconcode FROM dbo_macroeconstatistics WHERE macroeconcode = {}'.format(
                '"' + j + '"')
            data = pd.read_sql_query(query, self.engine)

            # For loop to retrieve macro statistics and calculate percent change
            for k in range(n):
                temp = data.tail(n + 1)
                data = data.tail(n)
                if j == k:
                    macrov = (data['statistics'].iloc[k] - temp['statistics'].iloc[0]) / temp['statistics'].iloc[0]
                    indicators[j].append(macrov)
                else:
                    macrov = (data['statistics'].iloc[k] - data['statistics'].iloc[k - 1]) / data['statistics'].iloc[
                        k - 1]
                    indicators[j].append(macrov)

        #Preforms the actual calculations and stores them in an array called calculated forecast
        calculated_forecast = []
        for k in range(n):
            stat = indicators['GDP'][k] * 1 - (indicators['UR'][k] * 0 + indicators['IR'][k] * .5) - (
                        indicators['MI'][k] * indicators['MI'][k])
            stat = (stat * train_data['close'].iloc[k]) + train_data['close'].iloc[k]
            calculated_forecast.append(stat)


        #Creates and inserts the forecast dates, instrument ids, calculated forecast prices, and actual close prices into an array
        results = []
        for k in range(n):
            results.append([dates[k], i, calculated_forecast[k], check_data['close'].loc[k]])

        #Creates a dataframe out of the array created above
        MSF2_df = pd.DataFrame(results, columns=['forecastdate', 'instrumentid', 'forecastcloseprice', 'close'])
        #print(df)

        MSF2_percent_error = []
        temp_error = 0
        for k in range(n):
            temp_error = (MSF2_df['close'] - MSF2_df['forecastcloseprice']) / MSF2_df['close']
            absolute_percent_error = [abs(ele) for ele in temp_error]
            MSF2_percent_error.append(absolute_percent_error[k])


        MSF2_percent_df = pd.DataFrame(MSF2_percent_error, columns=['PercentError'])

    """MSF3 forecasting"""
    n = 8

    #Gets the macro economic variables codes and names to loop through the inidividual macro variables
    query = "SELECT macroeconcode, macroeconname FROM dbo_macroeconmaster WHERE activecode = 'A'"
    data = pd.read_sql_query(query, self.engine)
    macrocodes = []
    indicators = {}
    for i in range(len(data['macroeconcode'])):
        macrocodes.append(data['macroeconcode'].loc[i])
        d = {data['macroeconcode'].loc[i]: []}
        indicators.update(d)

    #Gets the instrument ids to loop through the individual instruments
    query = 'SELECT instrumentid, instrumentname FROM dbo_instrumentmaster'
    data = pd.read_sql_query(query, self.engine)
    instrumentids = []
    for i in data['instrumentid']:
        instrumentids.append(i)
    weightings = create_weightings_MSF3(self.engine)


    #Loops through each instrument id to preform error calculations 1 instrument at a time
    for i in instrumentids:

        #Gets the instrument statistics to run through the function
        query = "SELECT date, close, instrumentid FROM ( SELECT date, close, instrumentID, ROW_NUMBER() OVER " \
                "(PARTITION BY YEAR(date), MONTH(date) ORDER BY DAY(date) DESC) AS rowNum FROM " \
                "dbo_instrumentstatistics WHERE instrumentid = {} AND date BETWEEN '2016-01-01' AND '2018-01-01' ) z " \
                "WHERE rowNum = 1 AND ( MONTH(z.date) = 3 OR MONTH(z.date) = 6 OR MONTH(z.date) = 9 OR " \
                "MONTH(z.date) = 12)".format(i)
        train_data = pd.read_sql_query(query, self.engine)

        #Gets the instrument statistics to check against the forecast prices
        query = "SELECT date, close, instrumentid FROM ( SELECT date, close, instrumentID, ROW_NUMBER() OVER " \
                "(PARTITION BY YEAR(date), MONTH(date) ORDER BY DAY(date) DESC) AS rowNum FROM " \
                "dbo_instrumentstatistics WHERE instrumentid = {} AND date BETWEEN '2018-01-01' AND '2020-01-01' ) z " \
                "WHERE rowNum = 1 AND ( MONTH(z.date) = 3 OR MONTH(z.date) = 6 OR MONTH(z.date) = 9 OR " \
                "MONTH(z.date) = 12)".format(i)
        check_data = pd.read_sql_query(query, self.engine)
        #print(check_data)

        #Gets the dates for the future forecast prices so they match the instrument statistics
        dates = []
        for l in check_data['date']:
            dates.append(str(l))

        #Loops through the macro economic variable codes to calculate percent change
        for j in macrocodes:
            #Retrieves macro economic statistics for each macro variables
            query = 'SELECT date, statistics, macroeconcode FROM dbo_macroeconstatistics WHERE macroeconcode = {}'.format(
                '"' + j + '"')
            data = pd.read_sql_query(query, self.engine)

            # For loop to retrieve macro statistics and calculate percent change
            for k in range(n):
                temp = data.tail(n + 1)
                data = data.tail(n)
                if j == k:
                    macrov = (data['statistics'].iloc[k] - temp['statistics'].iloc[0]) / temp['statistics'].iloc[0]
                    indicators[j].append(macrov)
                else:
                    macrov = (data['statistics'].iloc[k] - data['statistics'].iloc[k - 1]) / data['statistics'].iloc[
                        k - 1]
                    indicators[j].append(macrov)

        #Preforms the actual calculations and stores them in an array called calculated forecast
        calculated_forecast = []
        for k in range(n):
            stat = indicators['GDP'][k] * weightings[instrumentids[i-1]][0] - (indicators['COVI'][k] * weightings[instrumentids[i-1]][1]) + (indicators['FSI'][k] * weightings[instrumentids[i-1]][2]) - \
                                (indicators['CPIUC'][i-1] * indicators['CPIUC'][i-1])
            stat = (stat * train_data['close'].iloc[k]) + train_data['close'].iloc[k]
            calculated_forecast.append(stat)


        #Creates and inserts the forecast dates, instrument ids, calculated forecast prices, and actual close prices into an array
        results = []
        for k in range(n):
            results.append([dates[k], i, calculated_forecast[k], check_data['close'].loc[k]])

        #Creates a dataframe out of the array created above
        MSF3_df = pd.DataFrame(results, columns=['forecastdate', 'instrumentid', 'forecastcloseprice', 'close'])



        MSF3_percent_error = []
        temp_error = 0
         #Percent Error calculation

        for k in range(n):
            temp_error = (MSF3_df['close'] - MSF3_df['forecastcloseprice']) / MSF3_df['close']
            absolute_percent_error = [abs(ele) for ele in temp_error]
            MSF3_percent_error.append(absolute_percent_error[k])


        MSF3_percent_df = pd.DataFrame(MSF3_percent_error, columns=['PercentError'])

        #calculating mean of the two algorithms percent error
        mean_MSF2, mean_MSF3 = numpy.mean(MSF2_percent_error), numpy.mean(MSF3_percent_error)
        mean_MSF2.astype('float64')
        mean_MSF3.astype('float64')


        paired_samples = len(MSF2_percent_error)

        # sum squared difference between observations
        difference_list = []
        second_diff_list = []
        difference1 = sum([(MSF2_percent_df['PercentError']- MSF3_percent_df['PercentError'])**2 for i in range(paired_samples)])
        for i in range(paired_samples):

            difference_list.append(difference1[i])

        square_difference_df = pd.DataFrame(difference_list, columns=['SquaredDifference'])
        square_difference_df.astype('float64')


        # sum difference between observations
        difference2 = sum([MSF2_percent_df['PercentError']-MSF3_percent_df['PercentError'] for i in range(paired_samples)])
        for i in range(paired_samples):
            second_diff_list.append(difference2[i])

        second_square_df = pd.DataFrame(second_diff_list, columns=['SquaredDifference'])
        second_square_df.astype('float64')



        # standard deviation of the difference between means
        standard_deviation = (square_difference_df['SquaredDifference'] - (second_square_df['SquaredDifference']**2 / paired_samples)) / (paired_samples - 1)
        standard_deviation**1/2
        # standard error of the difference between the means
        standard_error = (standard_deviation) / (paired_samples**1/2)

        # calculate the t statistic
        t_stat_list = []
        for k in range(n):
            t_stat = (mean_MSF2 - mean_MSF3) / standard_error
            absolute_t_stat = [abs(ele) for ele in t_stat]
            t_stat_list.append(absolute_t_stat[k])
        t_stat_df = pd.DataFrame(t_stat_list, columns=['T-stats'])
        print(t_stat_df)






        # degrees of freedom
        freedom = paired_samples - 1

        #calculate the critical values
        alpha = 0.05
        critical_val = t.ppf(1.0 - alpha, freedom)

        # #calculate the p-value
        # for k in range(n):
        #     p = (1.0 - t.cdf(t_stat_df['T-stats'], freedom)) * 2.0






    if t_stat_df['T-stats'].any() <= critical_val:

        print("Accept null hypothesis that the means are equal.")
        print("A significant difference does not exist.")

    else:
        print("Reject the null hypothesis that the means are equal.")
        print("A signifcant difference does exist.")


    #     # interpret via p-value
    # if p.any() < alpha:
    #
    #     print("Reject the null hypothesis that the means are equal.")
    #     print("A significant difference does exist.")
    #
    # else:
    #
    #     print("Accept null hypothesis that the means are equal.")
    #     print("A significant difference does not exist.")
    #
    #








db_engine = DBEngine().mysql_engine()
#arima_accuracy(db_engine)
#accuracy(db_engine)
#MSF2_accuracy(db_engine)
#create_weightings_MSF3(db_engine)
t_test(db_engine)

# instrument_master = 'dbo_instrumentmaster'
# forecast = DataForecast(db_engine, instrument_master)
# forecast.calculate_accuracy_train()