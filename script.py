
import asyncio
# from datetime import datetime
import pytz
from datetime import timedelta,date
import datetime
import time
from kiteext import KiteExt
import json
import config
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import threading
from pandas.plotting import table
import requests
start=datetime.datetime.now()
def main1():
    
    print('Running Algo')
    #user = json.loads(open('userzerodha.json', 'r').read().rstrip())

    # NOTE contents of above 'userzerodha.json' must be as below
    # {
    #     "user_id": "AB1234",
    #     "password": "P@ssW0RD",
    #     "pin": "123456"
    # }

    
    
    #user = json.loads(open('userzerodha.json', 'r').read().rstrip())
    #print(user)
    kite = KiteExt()
    #kite.login_with_credentials(
    #userid=user['user_id'], password=user['password'], twofa=user['twofa'])
    kite.login_with_credentials(userid=config.username, password=config.password, pin=config.pin)
    with open('enctoken.txt', 'w') as wr:
          wr.write(kite.enctoken)

    print(kite.profile())
    enctoken = open('enctoken.txt', 'r').read().rstrip()
    print(os.getcwd(),enctoken)
    #kite = KiteExt()
    print(enctoken)
    kite.set_headers(enctoken)
    ##print(kite.profile())
    instruments = kite.instruments(exchange="NSE")
    
    today=(datetime.datetime.now()).date()
    today=today.strftime('%Y-%m-%d')
    true_range_startdt = datetime.datetime.now() - timedelta(days=5)
    startdt = true_range_startdt
    true_range_startdt = true_range_startdt.replace(hour = 9,minute=15,second=0)
    true_range_startdt = true_range_startdt.strftime('%Y-%m-%d %H:%M:%S')

    true_range_enddt = datetime.datetime.now() 
    enddt= true_range_enddt
    true_range_enddt = true_range_enddt.replace(hour = 15,minute=29,second=59)
    true_range_enddt = true_range_enddt.strftime('%Y-%m-%d %H:%M:%S')

    print(true_range_startdt,true_range_enddt)
    instrument_df = pd.read_csv("https://raw.githubusercontent.com/Raj4b5/Invest-yourself/master/New_NSE_145.csv")
    instrument_df_1 = pd.read_csv("https://raw.githubusercontent.com/Raj4b5/Invest-yourself/master/New_NSE_145.csv")
    
    def halfanhour(instrument_df):
      x_labels = []
      y_labels = []
      for token in instrument_df['token']:
          try:         
              df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'30minute') 
              ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
              ticker_df.date=ticker_df.date.astype(str).str[:-6]
              ticker_df.date=pd.to_datetime(ticker_df.date)
              ticker_df = ticker_df.reset_index()
              x_data = ticker_df.index.tolist() 
              #print(x_data)     # the index will be our x axis, not date
              y_data = ticker_df['open']

              # x values for the polynomial fit, 200 points
              x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)
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

              for element in l_max:                            # x coordinates of suspected minimums
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
                          y_loc_list.append(ticker_df.open.iloc[x_element])
                          #print(y_loc_list)
                          #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                  dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                              # to each suspected minimums we append the price values around that x position
                                                              # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                              # x position: [ 40$, 39$, 41$, 45$]
              #print('DICTIONARY for l_min: ', dict_i)
              y_delta = 0.12                               # percentage distance between average lows
              threshold = max(ticker_df['open']) * 0.75      # setting threshold higher than the global low

              y_dict = dict()
              maxi = list()
              suspected_tops = list()
                                                          #   BUG somewhere here
              for key in dict_i.keys():                     # for suspected minimum x position  
                  mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                          # if the range of days is too high the average will not make much sense

                  price_max = max(dict_i[key])    
                  maxi.append(price_max)                    # lowest value for price around suspected 

                  l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                  u_y = mn * (1.0 + y_delta)
                  y_dict[key] = [l_y, u_y, mn, price_max]

              #print('y_dict: ') 
              #print(y_dict) 

              #print('SCREENING FOR DOUBLE BOTTOM:')    

              for key_i in y_dict.keys():    
                  for key_j in y_dict.keys():    
                      if (key_i != key_j) and (y_dict[key_i][3] > threshold):
                          suspected_tops.append(key_i)
              percent_rise=[]
              for i in range(len(y_data)):
                  if i>=25 :
                      try:
                          percent_rise.append((y_data[i]-y_data[i-25])*100/y_data[i-25])
                      except:
                          pass

              #percent_fall
              suspected_tops = sorted(list(set(suspected_tops)))
              double_suspect = []

              for i in range(1,len(suspected_tops)):
                  #print(ticker_df.date[suspected_bottoms[i]])
                  max_loc = -10000000000009
                  max_index = None
                  for l in range(6):
                      #print(l)

                          if (i-1-l)>=0 and abs(suspected_tops[i]-suspected_tops[i-1-l])<25 and ((abs(y_data[suspected_tops[i]]-y_data[suspected_tops[i-1-l]])/(min(y_data[suspected_tops[i]],y_data[suspected_tops[i-1-l]]))*100)<=0.5) and (suspected_tops[i-l-1]-22)>=0:
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                              #print("hi")
                              #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                              for j in range(suspected_tops[i-l-1]-8,suspected_tops[i-l-1]):
                                  #print(j-20)
                                  if(percent_rise[j-25]>3):
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

                                      if (abs(ticker_df.open[suspected_tops[i]] -ticker_df.close[suspected_tops[i]]) < ( ticker_df.high[suspected_tops[i]] - ticker_df.low[suspected_tops[i]])*0.5) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.close[suspected_tops[i-1-l]]) < ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.low[suspected_tops[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_tops[i]] -ticker_df.low[suspected_tops[i]]) > ( ticker_df.high[suspected_tops[i]] - ticker_df.open[suspected_tops[i]])) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.low[suspected_tops[i-1-l]]) > ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.open[suspected_tops[i-1-l]])):
                  #open-low > high-open
                                              #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                              #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])
                                              if ticker_df.open[suspected_tops[i-1-l]]>max_loc:
                                                          max_loc = ticker_df.open[suspected_tops[i-1-l]]
                                                          max_index = suspected_tops[i-1-l]

                  flag=1
                  if max_index!=None:
                          #print(min_index,ticker_df.date[min_index])
                          for h in range(max_index+1,suspected_tops[i]):
                                  if ticker_df.open[h]>ticker_df.open[max_index] or ticker_df.open[h]>ticker_df.open[suspected_tops[i]]:
                                      flag=0
                                      break
                          if flag:
                              double_suspect.extend([max_index,suspected_tops[i]])


                      #                    double_suspect.extend([suspected_bottoms[i-1-l],suspected_bottoms[i]])
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
          except:
              pass
      Double_top = pd.DataFrame({'Date':x_labels,'token':y_labels})

      tokenName = {}
      #instrument_df
      for x in instrument_df['symbol']:
          for y in instruments:
              if(y['tradingsymbol']==x):
                  tokenName[x] =y['instrument_token']
      #tokenName
      stock = []

      for item in Double_top['token']:
          found=False
          #print(item)
          for key,val in tokenName.items():
              if(item==val):
                  found=True
                  stock.append(key)  
          if not found:
            print("stock",item)
      Double_top_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
      Double_top_new.to_csv("new_halfan_hour_Double_peak_new_open.csv")
      df=Double_top_new
      ax = plt.subplot(111, frame_on=False) # no visible frame
      ax.xaxis.set_visible(False)  # hide the x axis
      ax.yaxis.set_visible(False)  # hide the y axis
      table(ax, df, rowLabels=['']*df.shape[0], loc='center')
      plt.savefig('mytable.png')
      
      files={'photo':open('mytable.png')}
      resp=requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendPhoto?chat_id=-418248825&caption={}'.format('halfanhour_doublepeak_open '+today),files=files)
      print(resp.status_code)
    
    def halfanhour_1(instrument_df):
      x_labels = []
      y_labels = []
      for token in instrument_df['token']:
          try:         
              df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'30minute') 
              ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
              ticker_df.date=ticker_df.date.astype(str).str[:-6]
              ticker_df.date=pd.to_datetime(ticker_df.date)
              ticker_df = ticker_df.reset_index()
              x_data = ticker_df.index.tolist() 
              #print(x_data)     # the index will be our x axis, not date
              y_data = ticker_df['high']

              # x values for the polynomial fit, 200 points
              x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)
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

              for element in l_max:                            # x coordinates of suspected minimums
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
                          y_loc_list.append(ticker_df.high.iloc[x_element])
                          #print(y_loc_list)
                          #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                  dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                              # to each suspected minimums we append the price values around that x position
                                                              # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                              # x position: [ 40$, 39$, 41$, 45$]
              #print('DICTIONARY for l_min: ', dict_i)
              y_delta = 0.12                               # percentage distance between average lows
              threshold = max(ticker_df['high']) * 0.75      # setting threshold higher than the global low

              y_dict = dict()
              maxi = list()
              suspected_tops = list()
                                                          #   BUG somewhere here
              for key in dict_i.keys():                     # for suspected minimum x position  
                  mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                          # if the range of days is too high the average will not make much sense

                  price_max = max(dict_i[key])    
                  maxi.append(price_max)                    # lowest value for price around suspected 

                  l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                  u_y = mn * (1.0 + y_delta)
                  y_dict[key] = [l_y, u_y, mn, price_max]

              #print('y_dict: ') 
              #print(y_dict) 

              #print('SCREENING FOR DOUBLE BOTTOM:')    

              for key_i in y_dict.keys():    
                  for key_j in y_dict.keys():    
                      if (key_i != key_j) and (y_dict[key_i][3] > threshold):
                          suspected_tops.append(key_i)
              percent_rise=[]
              for i in range(len(y_data)):
                  if i>=25 :
                      try:
                          percent_rise.append((y_data[i]-y_data[i-25])*100/y_data[i-25])
                      except:
                          pass

              #percent_fall
              suspected_tops = sorted(list(set(suspected_tops)))
              double_suspect = []

              for i in range(1,len(suspected_tops)):
                  #print(ticker_df.date[suspected_bottoms[i]])
                  max_loc = -10000000000009
                  max_index = None
                  for l in range(6):
                      #print(l)

                          if (i-1-l)>=0 and abs(suspected_tops[i]-suspected_tops[i-1-l])<25 and ((abs(y_data[suspected_tops[i]]-y_data[suspected_tops[i-1-l]])/(min(y_data[suspected_tops[i]],y_data[suspected_tops[i-1-l]]))*100)<=0.5) and (suspected_tops[i-l-1]-22)>=0:
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                              #print("hi")
                              #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                              for j in range(suspected_tops[i-l-1]-8,suspected_tops[i-l-1]):
                                  #print(j-20)
                                  if(percent_rise[j-25]>3):
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

                                      if (abs(ticker_df.open[suspected_tops[i]] -ticker_df.close[suspected_tops[i]]) < ( ticker_df.high[suspected_tops[i]] - ticker_df.low[suspected_tops[i]])*0.5) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.close[suspected_tops[i-1-l]]) < ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.low[suspected_tops[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_tops[i]] -ticker_df.low[suspected_tops[i]]) > ( ticker_df.high[suspected_tops[i]] - ticker_df.open[suspected_tops[i]])) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.low[suspected_tops[i-1-l]]) > ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.open[suspected_tops[i-1-l]])):
                  #open-low > high-open
                                              #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                              #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])
                                              if ticker_df.high[suspected_tops[i-1-l]]>max_loc:
                                                          max_loc = ticker_df.high[suspected_tops[i-1-l]]
                                                          max_index = suspected_tops[i-1-l]

                  flag=1
                  if max_index!=None:
                          #print(min_index,ticker_df.date[min_index])
                          for h in range(max_index+1,suspected_tops[i]):
                                  if ticker_df.high[h]>ticker_df.high[max_index] or ticker_df.high[h]>ticker_df.high[suspected_tops[i]]:
                                      flag=0
                                      break
                          if flag:
                              double_suspect.extend([max_index,suspected_tops[i]])


                      #                    double_suspect.extend([suspected_bottoms[i-1-l],suspected_bottoms[i]])
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
          except:
              pass
      Double_top = pd.DataFrame({'Date':x_labels,'token':y_labels})

      tokenName = {}
      #instrument_df
      for x in instrument_df['symbol']:
          for y in instruments:
              if(y['tradingsymbol']==x):
                  tokenName[x] =y['instrument_token']
      #tokenName
      stock = []

      for item in Double_top['token']:
          found=False
          #print(item)
          for key,val in tokenName.items():
              if(item==val):
                  found=True
                  stock.append(key)  
          if not found:
            print("stock",item)
      Double_top_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
      Double_top_new.to_csv("new_halfan_hour_Double_peak_new_high.csv")
      df=Double_top_new
      ax = plt.subplot(111, frame_on=False) # no visible frame
      ax.xaxis.set_visible(False)  # hide the x axis
      ax.yaxis.set_visible(False)  # hide the y axis
      table(ax, df, rowLabels=['']*df.shape[0], loc='center')
      plt.savefig('mytable.png')
      
      files={'photo':open('mytable.png')}
      resp=requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendPhoto?chat_id=-418248825&caption={}'.format('halfanhour_doublepeak_high '+today),files=files)
      print(resp.status_code)
    

    #token_name=instrument_df[instrument_df['token']==1207553].symbol
    def one_hour(instrument_df):
      x_labels = []
      y_labels = []
      for token in instrument_df['token']:
          try:         
              df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'60minute') 
              ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
              ticker_df.date=ticker_df.date.astype(str).str[:-6]
              ticker_df.date=pd.to_datetime(ticker_df.date)
              ticker_df = ticker_df.reset_index()
              x_data = ticker_df.index.tolist() 
              #print(x_data)     # the index will be our x axis, not date
              y_data = ticker_df['open']

              # x values for the polynomial fit, 200 points
              x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)
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

              for element in l_max:                            # x coordinates of suspected minimums
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
                          y_loc_list.append(ticker_df.open.iloc[x_element])
                          #print(y_loc_list)
                          #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                  dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                              # to each suspected minimums we append the price values around that x position
                                                              # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                              # x position: [ 40$, 39$, 41$, 45$]
              #print('DICTIONARY for l_min: ', dict_i)
              y_delta = 0.12                               # percentage distance between average lows
              threshold = max(ticker_df['open']) * 0.75      # setting threshold higher than the global low

              y_dict = dict()
              maxi = list()
              suspected_tops = list()
                                                          #   BUG somewhere here
              for key in dict_i.keys():                     # for suspected minimum x position  
                  mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                          # if the range of days is too high the average will not make much sense

                  price_max = max(dict_i[key])    
                  maxi.append(price_max)                    # lowest value for price around suspected 

                  l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                  u_y = mn * (1.0 + y_delta)
                  y_dict[key] = [l_y, u_y, mn, price_max]

              #print('y_dict: ') 
              #print(y_dict) 

              #print('SCREENING FOR DOUBLE BOTTOM:')    

              for key_i in y_dict.keys():    
                  for key_j in y_dict.keys():    
                      if (key_i != key_j) and (y_dict[key_i][3] > threshold):
                          suspected_tops.append(key_i)
              percent_rise=[]
              for i in range(len(y_data)):
                  if i>=25 :
                      try:
                          percent_rise.append((y_data[i]-y_data[i-25])*100/y_data[i-25])
                      except:
                          pass

              #percent_fall
              suspected_tops = sorted(list(set(suspected_tops)))
              double_suspect = []

              for i in range(1,len(suspected_tops)):
                  #print(ticker_df.date[suspected_bottoms[i]])
                  max_loc = -10000000000009
                  max_index = None
                  for l in range(6):
                      #print(l)

                          if (i-1-l)>=0 and abs(suspected_tops[i]-suspected_tops[i-1-l])<25 and ((abs(y_data[suspected_tops[i]]-y_data[suspected_tops[i-1-l]])/(min(y_data[suspected_tops[i]],y_data[suspected_tops[i-1-l]]))*100)<=0.5) and (suspected_tops[i-l-1]-22)>=0:
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                              #print("hi")
                              #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                              for j in range(suspected_tops[i-l-1]-8,suspected_tops[i-l-1]):
                                  #print(j-20)
                                  if(percent_rise[j-25]>3):
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

                                      if (abs(ticker_df.open[suspected_tops[i]] -ticker_df.close[suspected_tops[i]]) < ( ticker_df.high[suspected_tops[i]] - ticker_df.low[suspected_tops[i]])*0.5) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.close[suspected_tops[i-1-l]]) < ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.low[suspected_tops[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_tops[i]] -ticker_df.low[suspected_tops[i]]) > ( ticker_df.high[suspected_tops[i]] - ticker_df.open[suspected_tops[i]])) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.low[suspected_tops[i-1-l]]) > ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.open[suspected_tops[i-1-l]])):
                  #open-low > high-open
                                              #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                              #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])
                                              if ticker_df.open[suspected_tops[i-1-l]]>max_loc:
                                                          max_loc = ticker_df.open[suspected_tops[i-1-l]]
                                                          max_index = suspected_tops[i-1-l]

                  flag=1
                  if max_index!=None:
                          #print(min_index,ticker_df.date[min_index])
                          for h in range(max_index+1,suspected_tops[i]):
                                  if ticker_df.open[h]>ticker_df.open[max_index] or ticker_df.open[h]>ticker_df.open[suspected_tops[i]]:
                                      flag=0
                                      break
                          if flag:
                              double_suspect.extend([max_index,suspected_tops[i]])


                      #                    double_suspect.extend([suspected_bottoms[i-1-l],suspected_bottoms[i]])
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
          except:
              pass
      Double_top = pd.DataFrame({'Date':x_labels,'token':y_labels})

      tokenName = {}
      #instrument_df
      for x in instrument_df['symbol']:
          for y in instruments:
              if(y['tradingsymbol']==x):
                  tokenName[x] =y['instrument_token']
      #tokenName
      stock = []

      for item in Double_top['token']:
          found=False
          #print(item)
          for key,val in tokenName.items():
              if(item==val):
                  found=True
                  stock.append(key)  
          if not found:
            print("stock",item)
      Double_top_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
      Double_top_new.to_csv("new_1_hour_Double_peak_new_open.csv")
      df=Double_top_new
      ax = plt.subplot(111, frame_on=False) # no visible frame
      ax.xaxis.set_visible(False)  # hide the x axis
      ax.yaxis.set_visible(False)  # hide the y axis
      table(ax, df, rowLabels=['']*df.shape[0], loc='center')
      plt.savefig('mytable.png')
      
      files={'photo':open('mytable.png')}
      resp=requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendPhoto?chat_id=-418248825&caption={}'.format('onehour_doublepeak_open '+today),files=files)
      print(resp.status_code)
    

    def one_hour_1(instrument_df):
      x_labels = []
      y_labels = []
      for token in instrument_df['token']:
          try:         
              df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'60minute') 
              ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
              ticker_df.date=ticker_df.date.astype(str).str[:-6]
              ticker_df.date=pd.to_datetime(ticker_df.date)
              ticker_df = ticker_df.reset_index()
              x_data = ticker_df.index.tolist() 
              #print(x_data)     # the index will be our x axis, not date
              y_data = ticker_df['high']

              # x values for the polynomial fit, 200 points
              x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)
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

              for element in l_max:                            # x coordinates of suspected minimums
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
                          y_loc_list.append(ticker_df.high.iloc[x_element])
                          #print(y_loc_list)
                          #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                  dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                              # to each suspected minimums we append the price values around that x position
                                                              # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                              # x position: [ 40$, 39$, 41$, 45$]
              #print('DICTIONARY for l_min: ', dict_i)
              y_delta = 0.12                               # percentage distance between average lows
              threshold = max(ticker_df['high']) * 0.75      # setting threshold higher than the global low

              y_dict = dict()
              maxi = list()
              suspected_tops = list()
                                                          #   BUG somewhere here
              for key in dict_i.keys():                     # for suspected minimum x position  
                  mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                          # if the range of days is too high the average will not make much sense

                  price_max = max(dict_i[key])    
                  maxi.append(price_max)                    # lowest value for price around suspected 

                  l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                  u_y = mn * (1.0 + y_delta)
                  y_dict[key] = [l_y, u_y, mn, price_max]

              #print('y_dict: ') 
              #print(y_dict) 

              #print('SCREENING FOR DOUBLE BOTTOM:')    

              for key_i in y_dict.keys():    
                  for key_j in y_dict.keys():    
                      if (key_i != key_j) and (y_dict[key_i][3] > threshold):
                          suspected_tops.append(key_i)
              percent_rise=[]
              for i in range(len(y_data)):
                  if i>=25 :
                      try:
                          percent_rise.append((y_data[i]-y_data[i-25])*100/y_data[i-25])
                      except:
                          pass

              #percent_fall
              suspected_tops = sorted(list(set(suspected_tops)))
              double_suspect = []

              for i in range(1,len(suspected_tops)):
                  #print(ticker_df.date[suspected_bottoms[i]])
                  max_loc = -10000000000009
                  max_index = None
                  for l in range(6):
                      #print(l)

                          if (i-1-l)>=0 and abs(suspected_tops[i]-suspected_tops[i-1-l])<25 and ((abs(y_data[suspected_tops[i]]-y_data[suspected_tops[i-1-l]])/(min(y_data[suspected_tops[i]],y_data[suspected_tops[i-1-l]]))*100)<=0.5) and (suspected_tops[i-l-1]-22)>=0:
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                              #print("hi")
                              #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                              for j in range(suspected_tops[i-l-1]-8,suspected_tops[i-l-1]):
                                  #print(j-20)
                                  if(percent_rise[j-25]>3):
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

                                      if (abs(ticker_df.open[suspected_tops[i]] -ticker_df.close[suspected_tops[i]]) < ( ticker_df.high[suspected_tops[i]] - ticker_df.low[suspected_tops[i]])*0.5) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.close[suspected_tops[i-1-l]]) < ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.low[suspected_tops[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_tops[i]] -ticker_df.low[suspected_tops[i]]) > ( ticker_df.high[suspected_tops[i]] - ticker_df.open[suspected_tops[i]])) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.low[suspected_tops[i-1-l]]) > ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.open[suspected_tops[i-1-l]])):
                  #open-low > high-open
                                              #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                              #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])
                                              if ticker_df.high[suspected_tops[i-1-l]]>max_loc:
                                                          max_loc = ticker_df.high[suspected_tops[i-1-l]]
                                                          max_index = suspected_tops[i-1-l]

                  flag=1
                  if max_index!=None:
                          #print(min_index,ticker_df.date[min_index])
                          for h in range(max_index+1,suspected_tops[i]):
                                  if ticker_df.high[h]>ticker_df.high[max_index] or ticker_df.high[h]>ticker_df.high[suspected_tops[i]]:
                                      flag=0
                                      break
                          if flag:
                              double_suspect.extend([max_index,suspected_tops[i]])


                      #                    double_suspect.extend([suspected_bottoms[i-1-l],suspected_bottoms[i]])
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
          except:
              pass
      Double_top = pd.DataFrame({'Date':x_labels,'token':y_labels})

      tokenName = {}
      #instrument_df
      for x in instrument_df['symbol']:
          for y in instruments:
              if(y['tradingsymbol']==x):
                  tokenName[x] =y['instrument_token']
      #tokenName
      stock = []

      for item in Double_top['token']:
          found=False
          #print(item)
          for key,val in tokenName.items():
              if(item==val):
                  found=True
                  stock.append(key)  
          if not found:
            print("stock",item)
      Double_top_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
      Double_top_new.to_csv("new_1_hour_Double_peak_new_high.csv")
      df=Double_top_new
      ax = plt.subplot(111, frame_on=False) # no visible frame
      ax.xaxis.set_visible(False)  # hide the x axis
      ax.yaxis.set_visible(False)  # hide the y axis
      table(ax, df, rowLabels=['']*df.shape[0], loc='center')
      plt.savefig('mytable.png')
      
      files={'photo':open('mytable.png')}
      resp=requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendPhoto?chat_id=-418248825&caption={}'.format('onehour_doublepeak_high '+today),files=files)
      print(resp.status_code)
    

    # %%
    def one_day(instrument_df_1):
      x_labels = []
      y_labels = []
      for token in instrument_df_1['token']:
          try:         
              df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'day') 
              ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
              ticker_df.date=ticker_df.date.astype(str).str[:-6]
              ticker_df.date=pd.to_datetime(ticker_df.date)
              ticker_df = ticker_df.reset_index()
              x_data = ticker_df.index.tolist() 
              #print(x_data)     # the index will be our x axis, not date
              y_data = ticker_df['open']

              # x values for the polynomial fit, 200 points
              x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)
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

              for element in l_max:                            # x coordinates of suspected minimums
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
                          y_loc_list.append(ticker_df.open.iloc[x_element])
                          #print(y_loc_list)
                          #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                  dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                              # to each suspected minimums we append the price values around that x position
                                                              # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                              # x position: [ 40$, 39$, 41$, 45$]
              #print('DICTIONARY for l_min: ', dict_i)
              y_delta = 0.12                               # percentage distance between average lows
              threshold = max(ticker_df['open']) * 0.75      # setting threshold higher than the global low

              y_dict = dict()
              maxi = list()
              suspected_tops = list()
                                                          #   BUG somewhere here
              for key in dict_i.keys():                     # for suspected minimum x position  
                  mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                          # if the range of days is too high the average will not make much sense

                  price_max = max(dict_i[key])    
                  maxi.append(price_max)                    # lowest value for price around suspected 

                  l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                  u_y = mn * (1.0 + y_delta)
                  y_dict[key] = [l_y, u_y, mn, price_max]

              #print('y_dict: ') 
              #print(y_dict) 

              #print('SCREENING FOR DOUBLE BOTTOM:')    

              for key_i in y_dict.keys():    
                  for key_j in y_dict.keys():    
                      if (key_i != key_j) and (y_dict[key_i][3] > threshold):
                          suspected_tops.append(key_i)
              percent_rise=[]
              for i in range(len(y_data)):
                  if i>=20 :
                      try:
                          percent_rise.append((y_data[i]-y_data[i-20])*100/y_data[i-20])
                      except:
                          pass

              #percent_fall
              suspected_tops = sorted(list(set(suspected_tops)))
              double_suspect = []

              for i in range(1,len(suspected_tops)):
                  #print(ticker_df.date[suspected_bottoms[i]])
                  max_loc = -10000000000009
                  max_index = None
                  for l in range(6):
                      #print(l)

                          if (i-1-l)>=0 and abs(suspected_tops[i]-suspected_tops[i-1-l])<20 and ((abs(y_data[suspected_tops[i]]-y_data[suspected_tops[i-1-l]])/(min(y_data[suspected_tops[i]],y_data[suspected_tops[i-1-l]]))*100)<=0.5) and (suspected_tops[i-l-1]-22)>=0:
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                              #print("hi")
                              #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                              for j in range(suspected_tops[i-l-1]-8,suspected_tops[i-l-1]):
                                  #print(j-20)
                                  if(percent_rise[j-20]>3):
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

                                      if (abs(ticker_df.open[suspected_tops[i]] -ticker_df.close[suspected_tops[i]]) < ( ticker_df.high[suspected_tops[i]] - ticker_df.low[suspected_tops[i]])*0.5) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.close[suspected_tops[i-1-l]]) < ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.low[suspected_tops[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_tops[i]] -ticker_df.low[suspected_tops[i]]) > ( ticker_df.high[suspected_tops[i]] - ticker_df.open[suspected_tops[i]])) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.low[suspected_tops[i-1-l]]) > ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.open[suspected_tops[i-1-l]])):
                  #open-low > high-open
                                              #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                              #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])
                                              if ticker_df.open[suspected_tops[i-1-l]]>max_loc:
                                                          max_loc = ticker_df.open[suspected_tops[i-1-l]]
                                                          max_index = suspected_tops[i-1-l]

                  flag=1
                  if max_index!=None:
                          #print(min_index,ticker_df.date[min_index])
                          for h in range(max_index+1,suspected_tops[i]):
                                  if ticker_df.open[h]>ticker_df.open[max_index] or ticker_df.open[h]>ticker_df.open[suspected_tops[i]]:
                                      flag=0
                                      break
                          if flag:
                              double_suspect.extend([max_index,suspected_tops[i]])


                      #                    double_suspect.extend([suspected_bottoms[i-1-l],suspected_bottoms[i]])
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
          except:
              pass
      Double_top = pd.DataFrame({'Date':x_labels,'token':y_labels})

      tokenName = {}
      #instrument_df
      for x in instrument_df_1['symbol']:
          for y in instruments:
              if(y['tradingsymbol']==x):
                  tokenName[x] =y['instrument_token']
      #tokenName
      stock = []

      for item in Double_top['token']:
          found=False
          #print(item)
          for key,val in tokenName.items():
              if(item==val):
                  found=True
                  stock.append(key)  
          if not found:
            print("stock",item)
      Double_top_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
      Double_top_new.to_csv("new_1_day_Double_peak_new_open.csv")
      df=Double_top_new
      ax = plt.subplot(111, frame_on=False) # no visible frame
      ax.xaxis.set_visible(False)  # hide the x axis
      ax.yaxis.set_visible(False)  # hide the y axis
      table(ax, df, rowLabels=['']*df.shape[0], loc='center')
      plt.savefig('mytable.png')
      
      files={'photo':open('mytable.png')}
      resp=requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendPhoto?chat_id=-418248825&caption={}'.format('oneday_doublepeak_open '+today),files=files)
      print(resp.status_code)
    
                    
    def one_day_1(instrument_df_1):
      x_labels = []
      y_labels = []
      for token in instrument_df_1['token']:
          try:         
              df_hist=kite.historical_data(token,true_range_startdt,true_range_enddt,'day') 
              ticker_df=pd.DataFrame.from_dict(df_hist, orient='columns', dtype=None)
              ticker_df.date=ticker_df.date.astype(str).str[:-6]
              ticker_df.date=pd.to_datetime(ticker_df.date)
              ticker_df = ticker_df.reset_index()
              x_data = ticker_df.index.tolist() 
              #print(x_data)     # the index will be our x axis, not date
              y_data = ticker_df['high']

              # x values for the polynomial fit, 200 points
              x = np.linspace(0, max(ticker_df.index.tolist()), max(ticker_df.index.tolist()) + 1)
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

              for element in l_max:                            # x coordinates of suspected minimums
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
                          y_loc_list.append(ticker_df.high.iloc[x_element])
                          #print(y_loc_list)
                          #print('ticker_df.Low.iloc[x_element]', ticker_df.Low.iloc[x_element])
                  dict_i[element] = y_loc_list                 # key in element is suspected x position of minimum
                                                              # to each suspected minimums we append the price values around that x position
                                                              # so 40: [53.70000076293945, 53.93000030517578, 52.84000015258789, 53.290000915527344]
                                                              # x position: [ 40$, 39$, 41$, 45$]
              #print('DICTIONARY for l_min: ', dict_i)
              y_delta = 0.12                               # percentage distance between average lows
              threshold = max(ticker_df['high']) * 0.75      # setting threshold higher than the global low

              y_dict = dict()
              maxi = list()
              suspected_tops = list()
                                                          #   BUG somewhere here
              for key in dict_i.keys():                     # for suspected minimum x position  
                  mn = sum(dict_i[key])/len(dict_i[key])    # this is averaging out the price around that suspected minimum
                                                          # if the range of days is too high the average will not make much sense

                  price_max = max(dict_i[key])    
                  maxi.append(price_max)                    # lowest value for price around suspected 

                  l_y = mn * (1.0 - y_delta)                #these values are trying to get an U shape, but it is kinda useless 
                  u_y = mn * (1.0 + y_delta)
                  y_dict[key] = [l_y, u_y, mn, price_max]

              #print('y_dict: ') 
              #print(y_dict) 

              #print('SCREENING FOR DOUBLE BOTTOM:')    

              for key_i in y_dict.keys():    
                  for key_j in y_dict.keys():    
                      if (key_i != key_j) and (y_dict[key_i][3] > threshold):
                          suspected_tops.append(key_i)
              percent_rise=[]
              for i in range(len(y_data)):
                  if i>=20 :
                      try:
                          percent_rise.append((y_data[i]-y_data[i-20])*100/y_data[i-20])
                      except:
                          pass

              #percent_fall
              suspected_tops = sorted(list(set(suspected_tops)))
              double_suspect = []

              for i in range(1,len(suspected_tops)):
                  #print(ticker_df.date[suspected_bottoms[i]])
                  max_loc = -10000000000009
                  max_index = None
                  for l in range(6):
                      #print(l)

                          if (i-1-l)>=0 and abs(suspected_tops[i]-suspected_tops[i-1-l])<20 and ((abs(y_data[suspected_tops[i]]-y_data[suspected_tops[i-1-l]])/(min(y_data[suspected_tops[i]],y_data[suspected_tops[i-1-l]]))*100)<=0.5) and (suspected_tops[i-l-1]-22)>=0:
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i-1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i-1]])
                              #print(abs(y_data[suspected_bottoms[i]]-y_data[suspected_bottoms[i+1]])/(max(y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]]))*100,y_data[suspected_bottoms[i]],y_data[suspected_bottoms[i+1]])
                              #print("hi")
                              #print(ticker_df.date[suspected_bottoms[i-1-l]],ticker_df.date[suspected_bottoms[i]],l)
                              for j in range(suspected_tops[i-l-1]-8,suspected_tops[i-l-1]):
                                  #print(j-20)
                                  if(percent_rise[j-20]>3):
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

                                      if (abs(ticker_df.open[suspected_tops[i]] -ticker_df.close[suspected_tops[i]]) < ( ticker_df.high[suspected_tops[i]] - ticker_df.low[suspected_tops[i]])*0.5) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.close[suspected_tops[i-1-l]]) < ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.low[suspected_tops[i-1-l]])*0.5) and (abs(ticker_df.open[suspected_tops[i]] -ticker_df.low[suspected_tops[i]]) > ( ticker_df.high[suspected_tops[i]] - ticker_df.open[suspected_tops[i]])) and (abs(ticker_df.open[suspected_tops[i-1-l]] -ticker_df.low[suspected_tops[i-1-l]]) > ( ticker_df.high[suspected_tops[i-1-l]] - ticker_df.open[suspected_tops[i-1-l]])):
                  #open-low > high-open
                                              #print("date: ",ticker_df.date[suspected_bottoms[i]],"open : ",ticker_df.open[suspected_bottoms[i]],"high : ",ticker_df.high[suspected_bottoms[i]],"low : ",ticker_df.low[suspected_bottoms[i]],"close: ",ticker_df.close[suspected_bottoms[i]])
                                              #print("date: ",ticker_df.date[suspected_bottoms[i-1-l]],"open : ",ticker_df.open[suspected_bottoms[i-1-l]],"high : ",ticker_df.high[suspected_bottoms[i-1-l]],"low : ",ticker_df.low[suspected_bottoms[i-1-l]],"close: ",ticker_df.close[suspected_bottoms[i-1-l]])
                                              if ticker_df.high[suspected_tops[i-1-l]]>max_loc:
                                                          max_loc = ticker_df.high[suspected_tops[i-1-l]]
                                                          max_index = suspected_tops[i-1-l]

                  flag=1
                  if max_index!=None:
                          #print(min_index,ticker_df.date[min_index])
                          for h in range(max_index+1,suspected_tops[i]):
                                  if ticker_df.high[h]>ticker_df.high[max_index] or ticker_df.high[h]>ticker_df.high[suspected_tops[i]]:
                                      flag=0
                                      break
                          if flag:
                              double_suspect.extend([max_index,suspected_tops[i]])


                      #                    double_suspect.extend([suspected_bottoms[i-1-l],suspected_bottoms[i]])
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
          except:
              pass
      Double_top = pd.DataFrame({'Date':x_labels,'token':y_labels})

      tokenName = {}
      #instrument_df
      for x in instrument_df_1['symbol']:
          for y in instruments:
              if(y['tradingsymbol']==x):
                  tokenName[x] =y['instrument_token']
      #tokenName
      stock = []

      for item in Double_top['token']:
          found=False
          #print(item)
          for key,val in tokenName.items():
              if(item==val):
                  found=True
                  stock.append(key)  
          if not found:
            print("stock",item)
      Double_top_new = pd.DataFrame({'Date':x_labels,'token':y_labels,'stock':stock})
      Double_top_new.to_csv("new_1_day_Double_peak_new_high.csv")
      df=Double_top_new
      ax = plt.subplot(111, frame_on=False) # no visible frame
      ax.xaxis.set_visible(False)  # hide the x axis
      ax.yaxis.set_visible(False)  # hide the y axis
      table(ax, df, rowLabels=['']*df.shape[0], loc='center')
      plt.savefig('mytable.png')
      
      files={'photo':open('mytable.png')}
      resp=requests.post('https://api.telegram.org/bot1772481683:AAGCtefuhSLBeRtNdFxRYkLX-a9eG8H5qyY/sendPhoto?chat_id=-418248825&caption={}'.format('oneday_doublepeak_high '+today),files=files)
      print(resp.status_code)
            

    # %%
    while(datetime.datetime.now(pytz.timezone('Asia/Kolkata'))<datetime.datetime.now(pytz.timezone('Asia/Kolkata')).replace(hour=9,minute=16)):
            pass        
    while(datetime.datetime.now(pytz.timezone('Asia/Kolkata'))<datetime.datetime.now(pytz.timezone('Asia/Kolkata')).replace(hour=15,minute=30)):
        #    doji_buy_sell()
        ##    i = i+1
        t1 = threading.Thread(target=one_hour, args=(instrument_df,))
        t2 = threading.Thread(target=one_hour_1, args=(instrument_df,))
        t3 = threading.Thread(target=halfanhour, args=(instrument_df,))
        t4 = threading.Thread(target=halfanhour_1, args=(instrument_df,))
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

                #orb_test()
                #t3=threading.Thread(target=orb_test,args=())
                #mints=[13,28,43,58]
                #if(datetime.datetime.now(pytz.timezone('Asia/Kolkata')).minute in mints):

                    #inverted_hamm(instrument_df)
                    #print(DATABASE_DOJI)
                    #doji_bs_order(1000,DATABASE_DOJI)
                    




def fire_and_forget(f):
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, *kwargs)

    return wrapped


@fire_and_forget
def foo():
    main1()
    print("ALgo run completed")


def main():
    print("Hello world")

    f = open("last_executed.txt", "r")
   
    last_run_date = datetime.datetime.strptime(f.read(), "%d-%m-%y").date()
    if datetime.datetime.now().date() >= last_run_date:
        foo()
        #print("I didn't wait for foo()")

        f = open("last_executed.txt", "w")
        f.write(datetime.datetime.now().strftime("%d-%m-%y"))
        f.close()
    
    return "This is good"


if __name__ == '__main__':
    main()
