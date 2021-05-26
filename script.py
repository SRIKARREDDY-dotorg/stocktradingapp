
import asyncio
# from datetime import datetime

from kiteext import KiteExt
import json
import pandas as pd
from time import sleep
import datetime as dt
import os
import numpy as np
import threading
import requests
def main1():
    
    print('Running Algo')
    user = json.loads(open('userzerodha.json', 'r').read().rstrip())

    # NOTE contents of above 'userzerodha.json' must be as below
    # {
    #     "user_id": "AB1234",
    #     "password": "P@ssW0RD",
    #     "pin": "123456"
    # }

    kite = KiteExt()
    kite.login_with_credentials(
        userid=user['user_id'], password=user['password'], pin=user['pin'])

    profile = kite.profile()
    print( '\nlogin successful for ',profile['user_name'].upper(),'\n')

    print(profile)
    enctoken = open('enctoken.txt', 'r').read().rstrip()
    print(os.getcwd(),enctoken)
    kite = KiteExt()

    print(enctoken)
    #code whatever logic you want for the running here
    kite.set_headers(enctoken)
    instruments = kite.instruments(exchange="NSE")
    from datetime import timedelta,time,date
    import datetime
    true_range_startdt = datetime.datetime.now() - timedelta(days=200)
    true_range_startdt = true_range_startdt.replace(hour = 9,minute=15,second=0)
    true_range_startdt = true_range_startdt.strftime('%Y-%m-%d %H:%M:%S')

    true_range_enddt = datetime.datetime.now() 
    true_range_enddt = true_range_enddt.replace(hour = 15,minute=29,second=59)
    true_range_enddt = true_range_enddt.strftime('%Y-%m-%d %H:%M:%S')

    print(true_range_startdt,true_range_enddt)
    instrument_df_1 = pd.read_csv("NSE500_tokens.csv")
    instrument_df = pd.read_csv('New_NSE_145.csv')
    

# %%
    def one_day_1(instrument_df):
        x_labels = []
        y_labels = []    
        for token in instrument_df['0']:
            #print(type(token))
            try:
                print(token)
                df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'day') 
                ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
                ticker_df = ticker_df.reset_index()
                #print(df_hist)
                ticker_df.date=ticker_df.date.astype(str).str[:-6]
                ticker_df.date=pd.to_datetime(ticker_df.date)
                ticker_df.columns
                x_data = ticker_df.index.tolist() 
                #print(x_data)     # the index will be our x axis, not date
                y_data = ticker_df['low']

                # x values for the polynomial fit, 200 points
                x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)

                #x = np.linspace(0, 72, 73)?
                # polynomial fit of degree xx
                #pol = np.polyfit(x_data, y_data, 30)
                #print(pol)
                #y_pol = np.polyval(pol, x)
                data = y_data
                date_val = ticker_df['date']

                #           ___ detection of local minimums and maximums ___

                min_max = np.diff(np.sign(np.diff(data))).nonzero()[0] + 1          # local min & max
                l_min = (np.diff(np.sign(np.diff(data))) > 0).nonzero()[0] + 1      # local min
                l_max = (np.diff(np.sign(np.diff(data))) < 0).nonzero()[0] + 1      # local max
                #print('corresponding LOW values for suspected indeces: ')
            #print(ticker_df.Low.iloc[l_min])

            #extend the suspected x range:
                delta = 25                  # how many ticks to the left and to the right from local minimum on x axis

                dict_i = dict()
                dict_x = dict()

                df_len = len(ticker_df.index)                    # number of rows in dataset

                for element in l_min:                            # x coordinates of suspected minimums
                    l_bound = element - delta                    # lower bound (left)
                    u_bound = element + delta                    # upper bound (right)
                    x_range = range(l_bound, u_bound + 1)        # range of x positions where we SUSPECT to find a low
                    dict_x[element] = x_range                    # just helpful dictionary that holds suspected x ranges for further visualization strips
                    
                    #print('x_range: ', x_range)
                    
                    y_loc_list = list()
                    for x_element in x_range:
                        #print('-----------------')
                        if x_element > 0 and x_element < df_len:                # need to stay within the dataframe
                            #y_loc_list.append(ticker_df.Low.iloc[x_element])   # list of suspected y values that can be a minimum
                            y_loc_list.append(ticker_df.low.iloc[x_element])
                            #print(y_loc_list)
                            #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                    dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                                # to each suspected minimums we append the price values around that x position
                                                                # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                                # x position: [ 40$, 39$, 41$, 45$]
                #print('DICTIONARY for l_min: ', dict_i)
                y_delta = 0.12                               # percentage distance between average lows
                threshold = min(ticker_df['low']) * 1.15      # setting threshold higher than the global low

                y_dict = dict()
                mini = list()
                suspected_bottoms = list()
                                                            #   BUG somewhere here
                for key in dict_i.keys():                     # for suspected minimum x position  
                    mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                            # if the range of days is too high the average will not make much sense
                        
                    price_min = min(dict_i[key])    
                    mini.append(price_min)                    # lowest value for price around suspected 
                    
                    l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                    u_y = mn * (1.0 + y_delta)
                    y_dict[key] = [l_y, u_y, mn, price_min]
                    
                #print('y_dict: ') 
                #print(y_dict) 

                #print('SCREENING FOR DOUBLE BOTTOM:')    
                    
                for key_i in y_dict.keys():    
                    for key_j in y_dict.keys():    
                        if (key_i != key_j) and (y_dict[key_i][3] < threshold):
                            suspected_bottoms.append(key_i)
                suspected_bottoms = sorted(list(set(suspected_bottoms)))
                double_suspect = []
                percent_fall = []
                for i in range(len(y_data)):
                        if i>=15 :
                            try:
                                percent_fall.append((y_data[i-15]-y_data[i])*100/y_data[i])
                            except:
                                pass
                #print(percent_fall)
                for i in range(1,len(suspected_bottoms)):
                    min_loc = 10000000000009
                    min_index = None
                    for l in range(11):
                        #print(l)
                            if (i-1-l)>=0 and abs(suspected_bottoms[i]-suspected_bottoms[i-1-l])<delta and ((abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1-l]])/(min(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1-l]]))*100)<=0.5) :
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                                #print("hi")
                                #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                                for j in range(suspected_bottoms[i-1-l]-8,suspected_bottoms[i-1-l]):
                                    #print(j-20)
                                    if(percent_fall[j-14]>2):
                                        #print(ticker_df.date[suspected_bottoms[i]],ticker_df.date[suspected_bottoms[i-1]])
                                        #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]))
                                        #print((ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5)
                                        #print("date: ",ticker_df.date[suspected_bottoms[i-1]],"open : ",ticker_df.open[suspected_bottoms[i-1]],"high : ",ticker_df.high[suspected_bottoms[i-1]],"low : ",ticker_df.low[suspected_bottoms[i-1]],"close: ",ticker_df.close[suspected_bottoms[i-1]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]))
                                        #print((ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5)
                                        #print("date: ",ticker_df.date[i],"open : ",ticker_df.open[i],"high : ",ticker_df.high[i],"low : ",ticker_df.low[i],"close: ",ticker_df.close[i])
                                        #print(percent_fall[j])
                                    #if abs(ticker_df.open[i] -ticker_df.close[i]) < ( ticker_df.high[i] - ticker_df.low[i])*0.4 :
                                        #if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]) < ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.low[suspected_bottoms[i-1]]) > ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.open[suspected_bottoms[i-1]])):
                                        if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.close[suspected_bottoms[i-1-l]]) < ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.low[suspected_bottoms[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.low[suspected_bottoms[i-1-l]]) > ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.open[suspected_bottoms[i-1-l]])):
                    #open-low > high-open
                                                #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                                #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])             
                                                #print(ticker_df.low[suspected_bottoms[i-1-l]])
                                                if ticker_df.low[suspected_bottoms[i-1-l]]<min_loc:
                                                    min_loc = ticker_df.low[suspected_bottoms[i-1-l]]
                                                    min_index = suspected_bottoms[i-1-l]
                                                    #print(min_index)
                                
                    flag=1
                    if min_index!=None:
                            #print(min_index)
                            for h in range(min_index+1,suspected_bottoms[i]):
                                    if ticker_df.low[h]<ticker_df.low[min_index] or ticker_df.low[h]<ticker_df.low[suspected_bottoms[i]]:
                                        flag=0
                                        break
                            if flag and (datetime.datetime.now().date() - (ticker_df['date'][suspected_bottoms[i]]).date()).days<=50:
                                double_suspect.extend([min_index,suspected_bottoms[i]])
                                
                    
                        
                #print(test)
                # ___ plotting ___
                
                
                #print(double_suspect)
                list1 = []
                list2 = []
                if len(double_suspect)>1:
                    for position in double_suspect:
                    #print((datetime.datetime.now().date() - (ticker_df['date'][position-1]).date()).days)
                        #if (datetime.datetime.now() - (ticker_df['date'][position])).days<100:
                        #print(position)
                            list1.append(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                        #print(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                            list2.append(token)
                if len(list1)==2:
                    #for s in list1:
                    x_labels.extend(list1)
                    y_labels.extend(list2)
                    print(list1,list2)
                if len(list1)>2:
                    x_labels.extend(list1[-4:])
                    y_labels.extend(list2[-4:])
                    print(list1,list2)
                            #print(ticker_df['date'][position-1].date(),token)

                #Double_bottom = pd.DataFrame({'Date':x_labels,'token':[token,token]})
                #for item in y_labels:
                    #print(y_pol[item-1],end=' ')
            except:
                pass    
            # print('dict_x: ', dict_x)   # this dictionary is holding the values of the suspected low price
            # print('y_dict:', y_dict)'''
        Double_bottom = pd.DataFrame({'Date':x_labels,'token':y_labels})

        tokenName = {}
        #instrument_df
        for x in instrument_df['Unnamed: 0']:
            for y in instruments:
                if(y['tradingsymbol']==x):
                    tokenName[x] =y['instrument_token']
        #tokenName
        stock = []
        for item in Double_bottom['token']:
            #print(item)
            for key,val in tokenName.items():
                if(item==val):
                    stock.append(key)  
        Double_bottom_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
        Double_bottom_new.to_csv("new_1_day_Double_bottom_new_low.csv")


    # %%
    def one_day(instrument_df):    
        x_labels = []
        y_labels = []
        for token in instrument_df['0']:
            #print(type(token))
            try:
                print(token)
                df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'day') 
                ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
                ticker_df = ticker_df.reset_index()
                #print(df_hist)
                ticker_df.date=ticker_df.date.astype(str).str[:-6]
                ticker_df.date=pd.to_datetime(ticker_df.date)
                ticker_df.columns
                x_data = ticker_df.index.tolist() 
                #print(x_data)     # the index will be our x axis, not date
                y_data = ticker_df['close']

                # x values for the polynomial fit, 200 points
                x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)

                #x = np.linspace(0, 72, 73)?
                # polynomial fit of degree xx
                #pol = np.polyfit(x_data, y_data, 30)
                #print(pol)
                #y_pol = np.polyval(pol, x)
                data = y_data
                date_val = ticker_df['date']

                #           ___ detection of local minimums and maximums ___

                min_max = np.diff(np.sign(np.diff(data))).nonzero()[0] + 1          # local min & max
                l_min = (np.diff(np.sign(np.diff(data))) > 0).nonzero()[0] + 1      # local min
                l_max = (np.diff(np.sign(np.diff(data))) < 0).nonzero()[0] + 1      # local max
                #print('corresponding LOW values for suspected indeces: ')
            #print(ticker_df.Low.iloc[l_min])

            #extend the suspected x range:
                delta = 25                  # how many ticks to the left and to the right from local minimum on x axis

                dict_i = dict()
                dict_x = dict()

                df_len = len(ticker_df.index)                    # number of rows in dataset

                for element in l_min:                            # x coordinates of suspected minimums
                    l_bound = element - delta                    # lower bound (left)
                    u_bound = element + delta                    # upper bound (right)
                    x_range = range(l_bound, u_bound + 1)        # range of x positions where we SUSPECT to find a low
                    dict_x[element] = x_range                    # just helpful dictionary that holds suspected x ranges for further visualization strips
                    
                    #print('x_range: ', x_range)
                    
                    y_loc_list = list()
                    for x_element in x_range:
                        #print('-----------------')
                        if x_element > 0 and x_element < df_len:                # need to stay within the dataframe
                            #y_loc_list.append(ticker_df.Low.iloc[x_element])   # list of suspected y values that can be a minimum
                            y_loc_list.append(ticker_df.low.iloc[x_element])
                            #print(y_loc_list)
                            #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                    dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                                # to each suspected minimums we append the price values around that x position
                                                                # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                                # x position: [ 40$, 39$, 41$, 45$]
                #print('DICTIONARY for l_min: ', dict_i)
                y_delta = 0.12                               # percentage distance between average lows
                threshold = min(ticker_df['close']) * 1.15      # setting threshold higher than the global low

                y_dict = dict()
                mini = list()
                suspected_bottoms = list()
                                                            #   BUG somewhere here
                for key in dict_i.keys():                     # for suspected minimum x position  
                    mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                            # if the range of days is too high the average will not make much sense
                        
                    price_min = min(dict_i[key])    
                    mini.append(price_min)                    # lowest value for price around suspected 
                    
                    l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                    u_y = mn * (1.0 + y_delta)
                    y_dict[key] = [l_y, u_y, mn, price_min]
                    
                #print('y_dict: ') 
                #print(y_dict) 

                #print('SCREENING FOR DOUBLE BOTTOM:')    
                    
                for key_i in y_dict.keys():    
                    for key_j in y_dict.keys():    
                        if (key_i != key_j) and (y_dict[key_i][3] < threshold):
                            suspected_bottoms.append(key_i)
                suspected_bottoms = sorted(list(set(suspected_bottoms)))
                double_suspect = []
                percent_fall = []
                for i in range(len(y_data)):
                        if i>=15 :
                            try:
                                percent_fall.append((y_data[i-15]-y_data[i])*100/y_data[i])
                            except:
                                pass
                #print(percent_fall)
                for i in range(1,len(suspected_bottoms)):
                    min_loc = 10000000000009
                    min_index = None
                    for l in range(5):
                        #print(l)
                            if abs(suspected_bottoms[i]-suspected_bottoms[i-1-l])<delta and abs(suspected_bottoms[i]-suspected_bottoms[i-1-l])>=5 and ((abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1-l]])/(min(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1-l]]))*100)<=0.5) :
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                                #print("hi")
                                #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                                for j in range(suspected_bottoms[i-1-l]-8,suspected_bottoms[i-1-l]):
                                    #print(j-20)
                                    if(percent_fall[j-14]>2):
                                        #print(ticker_df.date[suspected_bottoms[i]],ticker_df.date[suspected_bottoms[i-1]])
                                        #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]))
                                        #print((ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5)
                                        #print("date: ",ticker_df.date[suspected_bottoms[i-1]],"open : ",ticker_df.open[suspected_bottoms[i-1]],"high : ",ticker_df.high[suspected_bottoms[i-1]],"low : ",ticker_df.low[suspected_bottoms[i-1]],"close: ",ticker_df.close[suspected_bottoms[i-1]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]))
                                        #print((ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5)
                                        #print("date: ",ticker_df.date[i],"open : ",ticker_df.open[i],"high : ",ticker_df.high[i],"low : ",ticker_df.low[i],"close: ",ticker_df.close[i])
                                        #print(percent_fall[j])
                                    #if abs(ticker_df.open[i] -ticker_df.close[i]) < ( ticker_df.high[i] - ticker_df.low[i])*0.4 :
                                        #if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]) < ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.low[suspected_bottoms[i-1]]) > ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.open[suspected_bottoms[i-1]])):
                                        if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.close[suspected_bottoms[i-1-l]]) < ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.low[suspected_bottoms[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.low[suspected_bottoms[i-1-l]]) > ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.open[suspected_bottoms[i-1-l]])):
                    #open-low > high-open
                                                #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                                #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])             
                                                #print(ticker_df.low[suspected_bottoms[i-1-l]])
                                                if ticker_df.close[suspected_bottoms[i-1-l]]<min_loc:
                                                    min_loc = ticker_df.close[suspected_bottoms[i-1-l]]
                                                    min_index = suspected_bottoms[i-1-l]
                                                    #print(min_index)
                                
                    flag=1
                    if min_index!=None:
                            #print(min_index)
                            for h in range(min_index+1,suspected_bottoms[i]):
                                    if ticker_df.close[h]<ticker_df.close[min_index] or ticker_df.close[h]<ticker_df.close[suspected_bottoms[i]]:
                                        flag=0
                                        break
                            if flag and (datetime.datetime.now().date() - (ticker_df['date'][min_index]).date()).days<=50:
                                print(min_index,suspected_bottoms[i])
                                double_suspect.extend([min_index,suspected_bottoms[i]])
                                
                    
                        
                #print(test)
                # ___ plotting ___
                
                
                #print(double_suspect)
                list1 = []
                list2 = []
                if len(double_suspect)>1:
                    for position in double_suspect:
                    #print((datetime.datetime.now().date() - (ticker_df['date'][position-1]).date()).days)
                        #if (datetime.datetime.now() - (ticker_df['date'][position])).days<100:
                        #print(position)
                            list1.append(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                        #print(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                            list2.append(token)
                if len(list1)==2:
                    #for s in list1:
                    x_labels.extend(list1)
                    y_labels.extend(list2)
                    print(list1,list2)
                if len(list1)>2:
                    x_labels.extend(list1[-4:])
                    y_labels.extend(list2[-4:])
                    print(list1,list2)
                            #print(ticker_df['date'][position-1].date(),token)

                #Double_bottom = pd.DataFrame({'Date':x_labels,'token':[token,token]})
                #for item in y_labels:
                    #print(y_pol[item-1],end=' ')
                
            except:
                pass
            # print('dict_x: ', dict_x)   # this dictionary is holding the values of the suspected low price
            # print('y_dict:', y_dict)'''
        Double_bottom = pd.DataFrame({'Date':x_labels,'token':y_labels})

        tokenName = {}
        #instrument_df
        for x in instrument_df['Unnamed: 0']:
            for y in instruments:
                if(y['tradingsymbol']==x):
                    tokenName[x] =y['instrument_token']
        #tokenName
        stock = []
        for item in Double_bottom['token']:
            #print(item)
            for key,val in tokenName.items():
                if(item==val):
                    stock.append(key)  
        Double_bottom_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
        Double_bottom_new.to_csv("new_1_day_Double_bottom_new_close.csv")


    # %%
    #Double_bottom = pd.DataFrame({'Date':x_labels,'token':y_labels})


    # %%
    #x_labels


    # %%
    #instrument_df


    # %%

    '''tokenName = {}
    #instrument_df
    for x in instrument_df['Unnamed: 0']:
        for y in instruments:
            if(y['tradingsymbol']==x):
                tokenName[x] =y['instrument_token']
    #tokenName'''


    # %%
    '''stock = []
    for item in Double_bottom['token']:
        print(item)
        for key,val in tokenName.items():
            if(item==val):
                stock.append(key)  '''


    # %%
    #Double_bottom_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})


    # %%
    #Double_bottom_new.to_csv("new_1_day_Double_bottom_new_close.csv")


    # %%
    #Double_bottom_new.head(20)


    # %%
    def one_hour(instrument_df):
        x_labels = []
        y_labels = []
        for token in instrument_df['token']:
        #print(type(token))
            try:
                print(token)
                df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'60minute') 
                ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
                ticker_df = ticker_df.reset_index()
                #print(df_hist)
                ticker_df.date=ticker_df.date.astype(str).str[:-6]
                ticker_df.date=pd.to_datetime(ticker_df.date)
                ticker_df.columns
                x_data = ticker_df.index.tolist() 
                #print(x_data)     # the index will be our x axis, not date
                y_data = ticker_df['low']

                # x values for the polynomial fit, 200 points
                x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)

                #x = np.linspace(0, 72, 73)?
                # polynomial fit of degree xx
                #pol = np.polyfit(x_data, y_data, 30)
                #print(pol)
                #y_pol = np.polyval(pol, x)
                data = y_data
                date_val = ticker_df['date']

                #           ___ detection of local minimums and maximums ___

                min_max = np.diff(np.sign(np.diff(data))).nonzero()[0] + 1          # local min & max
                l_min = (np.diff(np.sign(np.diff(data))) > 0).nonzero()[0] + 1      # local min
                l_max = (np.diff(np.sign(np.diff(data))) < 0).nonzero()[0] + 1      # local max
                #print('corresponding LOW values for suspected indeces: ')
            #print(ticker_df.Low.iloc[l_min])

            #extend the suspected x range:
                delta = 25                  # how many ticks to the left and to the right from local minimum on x axis

                dict_i = dict()
                dict_x = dict()

                df_len = len(ticker_df.index)                    # number of rows in dataset

                for element in l_min:                            # x coordinates of suspected minimums
                    l_bound = element - delta                    # lower bound (left)
                    u_bound = element + delta                    # upper bound (right)
                    x_range = range(l_bound, u_bound + 1)        # range of x positions where we SUSPECT to find a low
                    dict_x[element] = x_range                    # just helpful dictionary that holds suspected x ranges for further visualization strips
                    
                    #print('x_range: ', x_range)
                    
                    y_loc_list = list()
                    for x_element in x_range:
                        #print('-----------------')
                        if x_element > 0 and x_element < df_len:                # need to stay within the dataframe
                            #y_loc_list.append(ticker_df.Low.iloc[x_element])   # list of suspected y values that can be a minimum
                            y_loc_list.append(ticker_df.low.iloc[x_element])
                            #print(y_loc_list)
                            #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                    dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                                # to each suspected minimums we append the price values around that x position
                                                                # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                                # x position: [ 40$, 39$, 41$, 45$]
                #print('DICTIONARY for l_min: ', dict_i)
                y_delta = 0.12                               # percentage distance between average lows
                threshold = min(ticker_df['low']) * 1.15      # setting threshold higher than the global low

                y_dict = dict()
                mini = list()
                suspected_bottoms = list()
                                                            #   BUG somewhere here
                for key in dict_i.keys():                     # for suspected minimum x position  
                    mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                            # if the range of days is too high the average will not make much sense
                        
                    price_min = min(dict_i[key])    
                    mini.append(price_min)                    # lowest value for price around suspected 
                    
                    l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                    u_y = mn * (1.0 + y_delta)
                    y_dict[key] = [l_y, u_y, mn, price_min]
                    
                #print('y_dict: ') 
                #print(y_dict) 

                #print('SCREENING FOR DOUBLE BOTTOM:')    
                    
                for key_i in y_dict.keys():    
                    for key_j in y_dict.keys():    
                        if (key_i != key_j) and (y_dict[key_i][3] < threshold):
                            suspected_bottoms.append(key_i)
                suspected_bottoms = sorted(list(set(suspected_bottoms)))
                double_suspect = []
                percent_fall = []
                for i in range(len(y_data)):
                        if i>=27 :
                            try:
                                percent_fall.append((y_data[i-27]-y_data[i])*100/y_data[i])
                            except:
                                pass
                #print(percent_fall)
                for i in range(1,len(suspected_bottoms)):
                    min_loc = 10000000000009
                    min_index = None
                    for l in range(5):
                        #print(l)
                            if abs(suspected_bottoms[i]-suspected_bottoms[i-1-l])<delta and abs(suspected_bottoms[i]-suspected_bottoms[i-1-l])>=5 and ((abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1-l]])/(min(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1-l]]))*100)<=0.5) :
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                                #print("hi")
                                #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                                for j in range(suspected_bottoms[i-1-l]-8,suspected_bottoms[i-1-l]):
                                    #print(j-20)
                                    if(percent_fall[j-26]>2):
                                        #print(ticker_df.date[suspected_bottoms[i]],ticker_df.date[suspected_bottoms[i-1]])
                                        #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]))
                                        #print((ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5)
                                        #print("date: ",ticker_df.date[suspected_bottoms[i-1]],"open : ",ticker_df.open[suspected_bottoms[i-1]],"high : ",ticker_df.high[suspected_bottoms[i-1]],"low : ",ticker_df.low[suspected_bottoms[i-1]],"close: ",ticker_df.close[suspected_bottoms[i-1]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]))
                                        #print((ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5)
                                        #print("date: ",ticker_df.date[i],"open : ",ticker_df.open[i],"high : ",ticker_df.high[i],"low : ",ticker_df.low[i],"close: ",ticker_df.close[i])
                                        #print(percent_fall[j])
                                    #if abs(ticker_df.open[i] -ticker_df.close[i]) < ( ticker_df.high[i] - ticker_df.low[i])*0.4 :
                                        #if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]) < ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.low[suspected_bottoms[i-1]]) > ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.open[suspected_bottoms[i-1]])):
                                        if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.close[suspected_bottoms[i-1-l]]) < ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.low[suspected_bottoms[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.low[suspected_bottoms[i-1-l]]) > ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.open[suspected_bottoms[i-1-l]])):
                    #open-low > high-open
                                                #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                                #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])             
                                                #print(ticker_df.low[suspected_bottoms[i-1-l]])
                                                if ticker_df.low[suspected_bottoms[i-1-l]]<min_loc:
                                                    min_loc = ticker_df.low[suspected_bottoms[i-1-l]]
                                                    min_index = suspected_bottoms[i-1-l]
                                                    #print(min_index)
                                
                    flag=1
                    if min_index!=None:
                            #print(min_index)
                            for h in range(min_index+1,suspected_bottoms[i]):
                                    if ticker_df.low[h]<ticker_df.low[min_index] or ticker_df.low[h]<ticker_df.low[suspected_bottoms[i]]:
                                        flag=0
                                        break
                            if flag and (datetime.datetime.now().date() - (ticker_df['date'][suspected_bottoms[i]]).date()).days<=5:
                                double_suspect.extend([min_index,suspected_bottoms[i]])
                                
                    
                        
                #print(test)
                # ___ plotting ___
                
                
                #print(double_suspect)
                list1 = []
                list2 = []
                if len(double_suspect)>1:
                    for position in double_suspect:
                    #print((datetime.datetime.now().date() - (ticker_df['date'][position-1]).date()).days)
                        #if (datetime.datetime.now() - (ticker_df['date'][position])).days<100:
                        #print(position)
                            list1.append(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                        #print(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                            list2.append(token)
                if len(list1)==2:
                    #for s in list1:
                    x_labels.extend(list1)
                    y_labels.extend(list2)
                    print(list1,list2)
                if len(list1)>2:
                    x_labels.extend(list1[-4:])
                    y_labels.extend(list2[-4:])
                    print(list1,list2)
                            #print(ticker_df['date'][position-1].date(),token)

                #Double_bottom = pd.DataFrame({'Date':x_labels,'token':[token,token]})
                #for item in y_labels:
                    #print(y_pol[item-1],end=' ')
                
            except:
                pass
        Double_bottom = pd.DataFrame({'Date':x_labels,'token':y_labels})
        
        tokenName = {}
        #instrument_df
        for x in instrument_df['symbol']:
            for y in instruments:
                if(y['tradingsymbol']==x):
                    tokenName[x] =y['instrument_token']
        #tokenName
        stock = []
        for item in Double_bottom['token']:
            print(item)
            for key,val in tokenName.items():
                if(item==val):
                    stock.append(key)
        Double_bottom_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
        Double_bottom_new.to_csv("new_1_hour_Double_bottom_new_low.csv")
            # print('dict_x: ', dict_x)   # this dictionary is holding the values of the suspected low price
            # print('y_dict:', y_dict)'''


    # %%
    def one_hour_1(instrument_df):
        x_labels = []
        y_labels = []
        for token in instrument_df['token']:
        #print(type(token))
            try:
                print(token)
                df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'60minute') 
                ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
                ticker_df = ticker_df.reset_index()
                #print(df_hist)
                ticker_df.date=ticker_df.date.astype(str).str[:-6]
                ticker_df.date=pd.to_datetime(ticker_df.date)
                ticker_df.columns
                x_data = ticker_df.index.tolist() 
                #print(x_data)     # the index will be our x axis, not date
                y_data = ticker_df['close']

                # x values for the polynomial fit, 200 points
                x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)

                #x = np.linspace(0, 72, 73)?
                # polynomial fit of degree xx
                #pol = np.polyfit(x_data, y_data, 30)
                #print(pol)
                #y_pol = np.polyval(pol, x)
                data = y_data
                date_val = ticker_df['date']

                #           ___ detection of local minimums and maximums ___

                min_max = np.diff(np.sign(np.diff(data))).nonzero()[0] + 1          # local min & max
                l_min = (np.diff(np.sign(np.diff(data))) > 0).nonzero()[0] + 1      # local min
                l_max = (np.diff(np.sign(np.diff(data))) < 0).nonzero()[0] + 1      # local max
                #print('corresponding LOW values for suspected indeces: ')
            #print(ticker_df.Low.iloc[l_min])

            #extend the suspected x range:
                delta = 25                  # how many ticks to the left and to the right from local minimum on x axis

                dict_i = dict()
                dict_x = dict()

                df_len = len(ticker_df.index)                    # number of rows in dataset

                for element in l_min:                            # x coordinates of suspected minimums
                    l_bound = element - delta                    # lower bound (left)
                    u_bound = element + delta                    # upper bound (right)
                    x_range = range(l_bound, u_bound + 1)        # range of x positions where we SUSPECT to find a low
                    dict_x[element] = x_range                    # just helpful dictionary that holds suspected x ranges for further visualization strips
                    
                    #print('x_range: ', x_range)
                    
                    y_loc_list = list()
                    for x_element in x_range:
                        #print('-----------------')
                        if x_element > 0 and x_element < df_len:                # need to stay within the dataframe
                            #y_loc_list.append(ticker_df.Low.iloc[x_element])   # list of suspected y values that can be a minimum
                            y_loc_list.append(ticker_df.close.iloc[x_element])
                            #print(y_loc_list)
                            #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                    dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                                # to each suspected minimums we append the price values around that x position
                                                                # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                                # x position: [ 40$, 39$, 41$, 45$]
                #print('DICTIONARY for l_min: ', dict_i)
                y_delta = 0.12                               # percentage distance between average lows
                threshold = min(ticker_df['close']) * 1.15      # setting threshold higher than the global low

                y_dict = dict()
                mini = list()
                suspected_bottoms = list()
                                                            #   BUG somewhere here
                for key in dict_i.keys():                     # for suspected minimum x position  
                    mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                            # if the range of days is too high the average will not make much sense
                        
                    price_min = min(dict_i[key])    
                    mini.append(price_min)                    # lowest value for price around suspected 
                    
                    l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                    u_y = mn * (1.0 + y_delta)
                    y_dict[key] = [l_y, u_y, mn, price_min]
                    
                #print('y_dict: ') 
                #print(y_dict) 

                #print('SCREENING FOR DOUBLE BOTTOM:')    
                    
                for key_i in y_dict.keys():    
                    for key_j in y_dict.keys():    
                        if (key_i != key_j) and (y_dict[key_i][3] < threshold):
                            suspected_bottoms.append(key_i)
                suspected_bottoms = sorted(list(set(suspected_bottoms)))
                double_suspect = []
                percent_fall = []
                for i in range(len(y_data)):
                        if i>=27 :
                            try:
                                percent_fall.append((y_data[i-27]-y_data[i])*100/y_data[i])
                            except:
                                pass
                #print(percent_fall)
                for i in range(1,len(suspected_bottoms)):
                    min_loc = 10000000000009
                    min_index = None
                    for l in range(5):
                        #print(l)
                            if abs(suspected_bottoms[i]-suspected_bottoms[i-1-l])<delta and abs(suspected_bottoms[i]-suspected_bottoms[i-1-l])>=5 and ((abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1-l]])/(min(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1-l]]))*100)<=0.5) :
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                                #print("hi")
                                #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                                for j in range(suspected_bottoms[i-1-l]-8,suspected_bottoms[i-1-l]):
                                    #print(j-20)
                                    if(percent_fall[j-26]>2):
                                        #print(ticker_df.date[suspected_bottoms[i]],ticker_df.date[suspected_bottoms[i-1]])
                                        #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]))
                                        #print((ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5)
                                        #print("date: ",ticker_df.date[suspected_bottoms[i-1]],"open : ",ticker_df.open[suspected_bottoms[i-1]],"high : ",ticker_df.high[suspected_bottoms[i-1]],"low : ",ticker_df.low[suspected_bottoms[i-1]],"close: ",ticker_df.close[suspected_bottoms[i-1]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]))
                                        #print((ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5)
                                        #print("date: ",ticker_df.date[i],"open : ",ticker_df.open[i],"high : ",ticker_df.high[i],"low : ",ticker_df.low[i],"close: ",ticker_df.close[i])
                                        #print(percent_fall[j])
                                    #if abs(ticker_df.open[i] -ticker_df.close[i]) < ( ticker_df.high[i] - ticker_df.low[i])*0.4 :
                                        #if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]) < ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.low[suspected_bottoms[i-1]]) > ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.open[suspected_bottoms[i-1]])):
                                        if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.close[suspected_bottoms[i-1-l]]) < ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.low[suspected_bottoms[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.low[suspected_bottoms[i-1-l]]) > ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.open[suspected_bottoms[i-1-l]])):
                    #open-low > high-open
                                                #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                                #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])             
                                                #print(ticker_df.low[suspected_bottoms[i-1-l]])
                                                if ticker_df.close[suspected_bottoms[i-1-l]]<min_loc:
                                                    min_loc = ticker_df.close[suspected_bottoms[i-1-l]]
                                                    min_index = suspected_bottoms[i-1-l]
                                                    #print(min_index)
                                
                    flag=1
                    if min_index!=None:
                            #print(min_index)
                            for h in range(min_index+1,suspected_bottoms[i]):
                                    if ticker_df.close[h]<ticker_df.close[min_index] or ticker_df.close[h]<ticker_df.close[suspected_bottoms[i]]:
                                        flag=0
                                        break
                            if flag and (datetime.datetime.now().date() - (ticker_df['date'][suspected_bottoms[i]]).date()).days<=5:
                                double_suspect.extend([min_index,suspected_bottoms[i]])
                                
                    
                        
                #print(test)
                # ___ plotting ___
                
                
                #print(double_suspect)
                list1 = []
                list2 = []
                if len(double_suspect)>1:
                    for position in double_suspect:
                    #print((datetime.datetime.now().date() - (ticker_df['date'][position-1]).date()).days)
                        #if (datetime.datetime.now() - (ticker_df['date'][position])).days<100:
                        #print(position)
                            list1.append(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                        #print(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                            list2.append(token)
                if len(list1)==2:
                    #for s in list1:
                    x_labels.extend(list1)
                    y_labels.extend(list2)
                    print(list1,list2)
                if len(list1)>2:
                    x_labels.extend(list1[-4:])
                    y_labels.extend(list2[-4:])
                    print(list1,list2)
                            #print(ticker_df['date'][position-1].date(),token)

                #Double_bottom = pd.DataFrame({'Date':x_labels,'token':[token,token]})
                #for item in y_labels:
                    #print(y_pol[item-1],end=' ')
                
            except:
                pass
        Double_bottom = pd.DataFrame({'Date':x_labels,'token':y_labels})
        
        tokenName = {}
        #instrument_df
        for x in instrument_df['symbol']:
            for y in instruments:
                if(y['tradingsymbol']==x):
                    tokenName[x] =y['instrument_token']
        #tokenName
        stock = []
        for item in Double_bottom['token']:
            print(item)
            for key,val in tokenName.items():
                if(item==val):
                    stock.append(key)
        Double_bottom_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
        Double_bottom_new.to_csv("new_1_hour_Double_bottom_new_close.csv")
            # print('dict_x: ', dict_x)   # this dictionary is holding the values of the suspected low price
            # print('y_dict:', y_dict)'''


    # %%
    def half_an_hour(instrument_df):
        x_labels = []
        y_labels = []
        for token in instrument_df['token']:
        #print(type(token))
            try:
                print(token)
                df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'30minute') 
                ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
                ticker_df = ticker_df.reset_index()
                #print(df_hist)
                ticker_df.date=ticker_df.date.astype(str).str[:-6]
                ticker_df.date=pd.to_datetime(ticker_df.date)
                ticker_df.columns
                x_data = ticker_df.index.tolist() 
                #print(x_data)     # the index will be our x axis, not date
                y_data = ticker_df['low']

                # x values for the polynomial fit, 200 points
                x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)

                #x = np.linspace(0, 72, 73)?
                # polynomial fit of degree xx
                #pol = np.polyfit(x_data, y_data, 30)
                #print(pol)
                #y_pol = np.polyval(pol, x)
                data = y_data
                date_val = ticker_df['date']

                #           ___ detection of local minimums and maximums ___

                min_max = np.diff(np.sign(np.diff(data))).nonzero()[0] + 1          # local min & max
                l_min = (np.diff(np.sign(np.diff(data))) > 0).nonzero()[0] + 1      # local min
                l_max = (np.diff(np.sign(np.diff(data))) < 0).nonzero()[0] + 1      # local max
                #print('corresponding LOW values for suspected indeces: ')
            #print(ticker_df.Low.iloc[l_min])

            #extend the suspected x range:
                delta = 25                  # how many ticks to the left and to the right from local minimum on x axis

                dict_i = dict()
                dict_x = dict()

                df_len = len(ticker_df.index)                    # number of rows in dataset

                for element in l_min:                            # x coordinates of suspected minimums
                    l_bound = element - delta                    # lower bound (left)
                    u_bound = element + delta                    # upper bound (right)
                    x_range = range(l_bound, u_bound + 1)        # range of x positions where we SUSPECT to find a low
                    dict_x[element] = x_range                    # just helpful dictionary that holds suspected x ranges for further visualization strips
                    
                    #print('x_range: ', x_range)
                    
                    y_loc_list = list()
                    for x_element in x_range:
                        #print('-----------------')
                        if x_element > 0 and x_element < df_len:                # need to stay within the dataframe
                            #y_loc_list.append(ticker_df.Low.iloc[x_element])   # list of suspected y values that can be a minimum
                            y_loc_list.append(ticker_df.low.iloc[x_element])
                            #print(y_loc_list)
                            #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                    dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                                # to each suspected minimums we append the price values around that x position
                                                                # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                                # x position: [ 40$, 39$, 41$, 45$]
                #print('DICTIONARY for l_min: ', dict_i)
                y_delta = 0.12                               # percentage distance between average lows
                threshold = min(ticker_df['low']) * 1.15      # setting threshold higher than the global low

                y_dict = dict()
                mini = list()
                suspected_bottoms = list()
                                                            #   BUG somewhere here
                for key in dict_i.keys():                     # for suspected minimum x position  
                    mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                            # if the range of days is too high the average will not make much sense
                        
                    price_min = min(dict_i[key])    
                    mini.append(price_min)                    # lowest value for price around suspected 
                    
                    l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                    u_y = mn * (1.0 + y_delta)
                    y_dict[key] = [l_y, u_y, mn, price_min]
                    
                #print('y_dict: ') 
                #print(y_dict) 

                #print('SCREENING FOR DOUBLE BOTTOM:')    
                    
                for key_i in y_dict.keys():    
                    for key_j in y_dict.keys():    
                        if (key_i != key_j) and (y_dict[key_i][3] < threshold):
                            suspected_bottoms.append(key_i)
                suspected_bottoms = sorted(list(set(suspected_bottoms)))
                double_suspect = []
                percent_fall = []
                for i in range(len(y_data)):
                        if i>=27 :
                            try:
                                percent_fall.append((y_data[i-27]-y_data[i])*100/y_data[i])
                            except:
                                pass
                #print(percent_fall)
                for i in range(1,len(suspected_bottoms)):
                    min_loc = 10000000000009
                    min_index = None
                    for l in range(5):
                        #print(l)
                            if abs(suspected_bottoms[i]-suspected_bottoms[i-1-l])<delta and abs(suspected_bottoms[i]-suspected_bottoms[i-1-l])>=5 and ((abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1-l]])/(min(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1-l]]))*100)<=0.5) :
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                                #print("hi")
                                #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                                for j in range(suspected_bottoms[i-1-l]-8,suspected_bottoms[i-1-l]):
                                    #print(j-20)
                                    if(percent_fall[j-26]>2):
                                        #print(ticker_df.date[suspected_bottoms[i]],ticker_df.date[suspected_bottoms[i-1]])
                                        #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]))
                                        #print((ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5)
                                        #print("date: ",ticker_df.date[suspected_bottoms[i-1]],"open : ",ticker_df.open[suspected_bottoms[i-1]],"high : ",ticker_df.high[suspected_bottoms[i-1]],"low : ",ticker_df.low[suspected_bottoms[i-1]],"close: ",ticker_df.close[suspected_bottoms[i-1]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]))
                                        #print((ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5)
                                        #print("date: ",ticker_df.date[i],"open : ",ticker_df.open[i],"high : ",ticker_df.high[i],"low : ",ticker_df.low[i],"close: ",ticker_df.close[i])
                                        #print(percent_fall[j])
                                    #if abs(ticker_df.open[i] -ticker_df.close[i]) < ( ticker_df.high[i] - ticker_df.low[i])*0.4 :
                                        #if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]) < ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.low[suspected_bottoms[i-1]]) > ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.open[suspected_bottoms[i-1]])):
                                        if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.close[suspected_bottoms[i-1-l]]) < ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.low[suspected_bottoms[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.low[suspected_bottoms[i-1-l]]) > ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.open[suspected_bottoms[i-1-l]])):
                    #open-low > high-open
                                                #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                                #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])             
                                                #print(ticker_df.low[suspected_bottoms[i-1-l]])
                                                if ticker_df.low[suspected_bottoms[i-1-l]]<min_loc:
                                                    min_loc = ticker_df.low[suspected_bottoms[i-1-l]]
                                                    min_index = suspected_bottoms[i-1-l]
                                                    #print(min_index)
                                
                    flag=1
                    if min_index!=None:
                            #print(min_index)
                            for h in range(min_index+1,suspected_bottoms[i]):
                                    if ticker_df.low[h]<ticker_df.low[min_index] or ticker_df.low[h]<ticker_df.low[suspected_bottoms[i]]:
                                        flag=0
                                        break
                            if flag and (datetime.datetime.now().date() - (ticker_df['date'][suspected_bottoms[i]]).date()).days<=5:
                                double_suspect.extend([min_index,suspected_bottoms[i]])
                                
                    
                        
                #print(test)
                # ___ plotting ___
                
                
                #print(double_suspect)
                list1 = []
                list2 = []
                if len(double_suspect)>1:
                    for position in double_suspect:
                    #print((datetime.datetime.now().date() - (ticker_df['date'][position-1]).date()).days)
                        #if (datetime.datetime.now() - (ticker_df['date'][position])).days<100:
                        #print(position)
                            list1.append(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                        #print(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                            list2.append(token)
                if len(list1)==2:
                    #for s in list1:
                    x_labels.extend(list1)
                    y_labels.extend(list2)
                    print(list1,list2)
                if len(list1)>2:
                    x_labels.extend(list1[-4:])
                    y_labels.extend(list2[-4:])
                    print(list1,list2)
                            #print(ticker_df['date'][position-1].date(),token)

                #Double_bottom = pd.DataFrame({'Date':x_labels,'token':[token,token]})
                #for item in y_labels:
                    #print(y_pol[item-1],end=' ')
                
            except:
                pass
            # print('dict_x: ', dict_x)   # this dictionary is holding the values of the suspected low price
            # print('y_dict:', y_dict)'''
        Double_bottom = pd.DataFrame({'Date':x_labels,'token':y_labels})
        
        tokenName = {}
        #instrument_df
        for x in instrument_df['symbol']:
            for y in instruments:
                if(y['tradingsymbol']==x):
                    tokenName[x] =y['instrument_token']
        #tokenName
        stock = []
        for item in Double_bottom['token']:
            print(item)
            for key,val in tokenName.items():
                if(item==val):
                    stock.append(key)
        Double_bottom_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
        Double_bottom_new.to_csv("new_half_an_hour_Double_bottom_new_low.csv")


    # %%
    def half_an_hour_1(instrument_df):
        x_labels = []
        y_labels = []
        for token in instrument_df['token']:
        #print(type(token))
            try:
                print(token)
                df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'30minute') 
                ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
                ticker_df = ticker_df.reset_index()
                #print(df_hist)
                ticker_df.date=ticker_df.date.astype(str).str[:-6]
                ticker_df.date=pd.to_datetime(ticker_df.date)
                ticker_df.columns
                x_data = ticker_df.index.tolist() 
                #print(x_data)     # the index will be our x axis, not date
                y_data = ticker_df['close']

                # x values for the polynomial fit, 200 points
                x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)

                #x = np.linspace(0, 72, 73)?
                # polynomial fit of degree xx
                #pol = np.polyfit(x_data, y_data, 30)
                #print(pol)
                #y_pol = np.polyval(pol, x)
                data = y_data
                date_val = ticker_df['date']

                #           ___ detection of local minimums and maximums ___

                min_max = np.diff(np.sign(np.diff(data))).nonzero()[0] + 1          # local min & max
                l_min = (np.diff(np.sign(np.diff(data))) > 0).nonzero()[0] + 1      # local min
                l_max = (np.diff(np.sign(np.diff(data))) < 0).nonzero()[0] + 1      # local max
                #print('corresponding LOW values for suspected indeces: ')
            #print(ticker_df.Low.iloc[l_min])

            #extend the suspected x range:
                delta = 25                  # how many ticks to the left and to the right from local minimum on x axis

                dict_i = dict()
                dict_x = dict()

                df_len = len(ticker_df.index)                    # number of rows in dataset

                for element in l_min:                            # x coordinates of suspected minimums
                    l_bound = element - delta                    # lower bound (left)
                    u_bound = element + delta                    # upper bound (right)
                    x_range = range(l_bound, u_bound + 1)        # range of x positions where we SUSPECT to find a low
                    dict_x[element] = x_range                    # just helpful dictionary that holds suspected x ranges for further visualization strips
                    
                    #print('x_range: ', x_range)
                    
                    y_loc_list = list()
                    for x_element in x_range:
                        #print('-----------------')
                        if x_element > 0 and x_element < df_len:                # need to stay within the dataframe
                            #y_loc_list.append(ticker_df.Low.iloc[x_element])   # list of suspected y values that can be a minimum
                            y_loc_list.append(ticker_df.close.iloc[x_element])
                            #print(y_loc_list)
                            #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                    dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                                # to each suspected minimums we append the price values around that x position
                                                                # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                                # x position: [ 40$, 39$, 41$, 45$]
                #print('DICTIONARY for l_min: ', dict_i)
                y_delta = 0.12                               # percentage distance between average lows
                threshold = min(ticker_df['close']) * 1.15      # setting threshold higher than the global low

                y_dict = dict()
                mini = list()
                suspected_bottoms = list()
                                                            #   BUG somewhere here
                for key in dict_i.keys():                     # for suspected minimum x position  
                    mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                            # if the range of days is too high the average will not make much sense
                        
                    price_min = min(dict_i[key])    
                    mini.append(price_min)                    # lowest value for price around suspected 
                    
                    l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                    u_y = mn * (1.0 + y_delta)
                    y_dict[key] = [l_y, u_y, mn, price_min]
                    
                #print('y_dict: ') 
                #print(y_dict) 

                #print('SCREENING FOR DOUBLE BOTTOM:')    
                    
                for key_i in y_dict.keys():    
                    for key_j in y_dict.keys():    
                        if (key_i != key_j) and (y_dict[key_i][3] < threshold):
                            suspected_bottoms.append(key_i)
                suspected_bottoms = sorted(list(set(suspected_bottoms)))
                double_suspect = []
                percent_fall = []
                for i in range(len(y_data)):
                        if i>=27 :
                            try:
                                percent_fall.append((y_data[i-27]-y_data[i])*100/y_data[i])
                            except:
                                pass
                #print(percent_fall)
                for i in range(1,len(suspected_bottoms)):
                    min_loc = 10000000000009
                    min_index = None
                    for l in range(5):
                        #print(l)
                            if abs(suspected_bottoms[i]-suspected_bottoms[i-1-l])<delta and abs(suspected_bottoms[i]-suspected_bottoms[i-1-l])>=5 and ((abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1-l]])/(min(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1-l]]))*100)<=0.5) :
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                                #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                                #print("hi")
                                #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                                for j in range(suspected_bottoms[i-1-l]-8,suspected_bottoms[i-1-l]):
                                    #print(j-20)
                                    if(percent_fall[j-26]>2):
                                        #print(ticker_df.date[suspected_bottoms[i]],ticker_df.date[suspected_bottoms[i-1]])
                                        #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]))
                                        #print((ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5)
                                        #print("date: ",ticker_df.date[suspected_bottoms[i-1]],"open : ",ticker_df.open[suspected_bottoms[i-1]],"high : ",ticker_df.high[suspected_bottoms[i-1]],"low : ",ticker_df.low[suspected_bottoms[i-1]],"close: ",ticker_df.close[suspected_bottoms[i-1]])
                                        #print(abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]))
                                        #print((ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5)
                                        #print("date: ",ticker_df.date[i],"open : ",ticker_df.open[i],"high : ",ticker_df.high[i],"low : ",ticker_df.low[i],"close: ",ticker_df.close[i])
                                        #print(percent_fall[j])
                                    #if abs(ticker_df.open[i] -ticker_df.close[i]) < ( ticker_df.high[i] - ticker_df.low[i])*0.4 :
                                        #if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.close[suspected_bottoms[i-1]]) < ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.low[suspected_bottoms[i-1]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1]] -ticker_df.low[suspected_bottoms[i-1]]) > ( ticker_df.high[suspected_bottoms[i-1]] - ticker_df.open[suspected_bottoms[i-1]])):
                                        if (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.close[suspected_bottoms[i]]) < ( ticker_df.high[suspected_bottoms[i]] - ticker_df.low[suspected_bottoms[i]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.close[suspected_bottoms[i-1-l]]) < ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.low[suspected_bottoms[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_bottoms[i]] -ticker_df.low[suspected_bottoms[i]]) > ( ticker_df.high[suspected_bottoms[i]] - ticker_df.open[suspected_bottoms[i]])) and (abs(ticker_df.open[suspected_bottoms[i-1-l]] -ticker_df.low[suspected_bottoms[i-1-l]]) > ( ticker_df.high[suspected_bottoms[i-1-l]] - ticker_df.open[suspected_bottoms[i-1-l]])):
                    #open-low > high-open
                                                #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                                #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])             
                                                #print(ticker_df.low[suspected_bottoms[i-1-l]])
                                                if ticker_df.close[suspected_bottoms[i-1-l]]<min_loc:
                                                    min_loc = ticker_df.close[suspected_bottoms[i-1-l]]
                                                    min_index = suspected_bottoms[i-1-l]
                                                    #print(min_index)
                                
                    flag=1
                    if min_index!=None:
                            #print(min_index)
                            for h in range(min_index+1,suspected_bottoms[i]):
                                    if ticker_df.close[h]<ticker_df.close[min_index] or ticker_df.close[h]<ticker_df.close[suspected_bottoms[i]]:
                                        flag=0
                                        break
                            if flag and (datetime.datetime.now().date() - (ticker_df['date'][suspected_bottoms[i]]).date()).days<=5:
                                double_suspect.extend([min_index,suspected_bottoms[i]])
                                
                    
                        
                #print(test)
                # ___ plotting ___
                
                
                #print(double_suspect)
                list1 = []
                list2 = []
                if len(double_suspect)>1:
                    for position in double_suspect:
                    #print((datetime.datetime.now().date() - (ticker_df['date'][position-1]).date()).days)
                        #if (datetime.datetime.now() - (ticker_df['date'][position])).days<100:
                        #print(position)
                            list1.append(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                        #print(ticker_df['date'][position].strftime('%Y-%m-%d %H:%M:%S'))
                            list2.append(token)
                if len(list1)==2:
                    #for s in list1:
                    x_labels.extend(list1)
                    y_labels.extend(list2)
                    print(list1,list2)
                if len(list1)>2:
                    x_labels.extend(list1[-4:])
                    y_labels.extend(list2[-4:])
                    print(list1,list2)
                            #print(ticker_df['date'][position-1].date(),token)

                #Double_bottom = pd.DataFrame({'Date':x_labels,'token':[token,token]})
                #for item in y_labels:
                    #print(y_pol[item-1],end=' ')
                
            except:
                pass
            # print('dict_x: ', dict_x)   # this dictionary is holding the values of the suspected low price
            # print('y_dict:', y_dict)'''
        Double_bottom = pd.DataFrame({'Date':x_labels,'token':y_labels})
        
        tokenName = {}
        #instrument_df
        for x in instrument_df['symbol']:
            for y in instruments:
                if(y['tradingsymbol']==x):
                    tokenName[x] =y['instrument_token']
        #tokenName
        stock = []
        for item in Double_bottom['token']:
            print(item)
            for key,val in tokenName.items():
                if(item==val):
                    stock.append(key)
        Double_bottom_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
        Double_bottom_new.to_csv("new_half_an_hour_Double_bottom_new_close.csv")
    t1 = threading.Thread(target=one_hour, args=(instrument_df,))
    t2 = threading.Thread(target=one_hour_1, args=(instrument_df,))
    t3 = threading.Thread(target=half_an_hour, args=(instrument_df,))
    t4 = threading.Thread(target=half_an_hour_1, args=(instrument_df,))
    t5 = threading.Thread(target=one_day, args=(instrument_df_1,))
    t6 = threading.Thread(target=one_day_1, args=(instrument_df_1,))
    
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
    files = {'document':open('new_1_hour_Double_bottom_new_close.csv','rb')}
    todays = datetime.datetime.now()
    today = todays.strftime('%Y-%m-%d %H:%M:%S')
    resp = requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendDocument?chat_id=-1001253024203&caption={}'.format(today),files=files)
    print("documents sent",resp.status_code)

    files = {'document':open('new_1_hour_Double_bottom_new_low.csv','rb')}
    resp = requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendDocument?chat_id=-1001253024203&caption={}'.format(today),files=files)
    print("documents sent",resp.status_code)

    files = {'document':open('new_half_an_hour_Double_bottom_new_close.csv','rb')}
    resp = requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendDocument?chat_id=-1001253024203&caption={}'.format(today),files=files)
    print("documents sent",resp.status_code)

    files = {'document':open('new_half_an_hour_Double_bottom_new_low.csv','rb')}
    resp = requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendDocument?chat_id=-1001253024203&caption={}'.format(today),files=files)
    print("documents sent",resp.status_code)

    Time = todays.time()
    Time = Time.strftime('%H:%M:%S')

    if(Time>='15:10:00'):
        files = {'document':open('new_1_day_Double_bottom_new_close.csv','rb')}
        resp = requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendDocument?chat_id=-1001253024203&caption={}'.format(today),files=files)
        print("documents sent",resp.status_code)

        files = {'document':open('new_1_day_Double_bottom_new_low.csv','rb')}
        resp = requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendDocument?chat_id=-1001253024203&caption={}'.format(today),files=files)
        print("documents sent",resp.status_code)

    

def fire_and_forget(f):
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, *kwargs)

    return wrapped


@fire_and_forget
def foo():
    main1()
    print("ALgo run completed")


def main():
    print("Hello Mayur")

    f = open("last_executed.txt", "r")
   
    last_run_date = dt.datetime.strptime(f.read(), "%d-%m-%y").date()
    if dt.datetime.now().date() >= last_run_date:
        foo()
        #print("I didn't wait for foo()")

        f = open("last_executed.txt", "w")
        f.write(dt.datetime.now().strftime("%d-%m-%y"))
        f.close()
    
    return "This is good"


if __name__ == '__main__':
    main()
