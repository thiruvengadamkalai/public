#Python code :
#1. webscraping upcoming matches for the weekend
#2. webscraping Premier League csv files from the website for all years, and dowloading them.
#3. Reading into Pandas dataframe
#4. For each of the upcoming weekend matches (for the 2 teams):
#         1. Get match stats(goals,result) and arrange in reverse border with most recent matches.
#         2. Generate Poisson Distribution of probability of goals score for 10000 cases using a rolling mean of goals in last 8 match.
#         3. Generate probability of team1_win, team2_win, draw for 10000 cases and take average
#5.Create an output table in given format ('Output.csv')


#!/usr/bin/env python
# coding: utf-8

# In[30]:


#webscrape and download input csv files
from urllib.parse import urljoin  
from urllib.request import urlretrieve
from bs4 import BeautifulSoup
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

url = "http://www.football-data.co.uk/englandm.php"

driver = webdriver.Chrome(executable_path  = "/Users/thiruvengadamkalaikannan/Documents/chromedriver")
url = 'http://www.football-data.co.uk/englandm.php'
driver.get(url)
soup = BeautifulSoup(driver.page_source, 'lxml')
files = []
i=1
for a in soup.findAll('a',href=True):
    if a.text=='Premier League':
        link = 'http://www.football-data.co.uk/' +a.get("href")
        f = 'epl'+str(i)+'.csv'
        urlretrieve(link,f)
        files.append(f)
        i+=1
driver.quit()


# In[31]:


#webscraping upcoming matches for the weekend from the betting website and creating a dictionary

from bs4 import BeautifulSoup
from selenium import webdriver
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

driver = webdriver.Chrome(executable_path  = "/Users/thiruvengadamkalaikannan/Documents/chromedriver")

driver.get('https://www.bet365.com/#/AC/B1/C1/D13/E37628398/F2/')
try:
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "gll-MarketColumnHeader sl-MarketHeaderLabel_Date sl-MarketHeaderLabel ")))
except TimeoutException:
    print('Page timed out after 30 secs.')

soup = BeautifulSoup(driver.page_source, 'lxml')

driver.quit()

for s in soup.find_all("div",class_="sl-MarketCouponFixtureLabelBase gll-Market_General gll-Market_HasLabels"):
    match = s.find_all("div",{'class':["gll-MarketColumnHeader sl-MarketHeaderLabel sl-MarketHeaderLabel_Date","gll-MarketColumnHeader sl-MarketHeaderLabel_Date sl-MarketHeaderLabel","sl-CouponParticipantWithBookCloses_Name"]})

weekend_matches = {}
text = []
for i in match:
    string = i.text
    text.append(string)
    if string.startswith('Sat') or string.startswith('Sun'):
        weekend_matches[string] = {}

sat=[i for i,s in enumerate(text) if s.startswith('Sat')]
sun=[i for i,s in enumerate(text) if s.startswith('Sun')]
mon=[i for i,s in enumerate(text) if s.startswith('Mon')]

subs = {'Sheff Utd':'Sheffield United' , 'Man Utd':'Man United','Wolverhampton':'Wolves'}

if len(sat)>0:
    if len(sun)!=0:
        for i in range(sat[0]+1,sun[0]):
            weekend_matches[text[sat[0]]][text[i]]=[]
            for t in text[i].split(' v '):
                if t in subs.keys():
                    t=subs[t]
                weekend_matches[text[sat[0]]][text[i]].append(t)
    else:
        for i in range(sat[0]+1,len(text)):
            weekend_matches[text[sat[0]]][text[i]]=[]
            for t in text[i].split(' v '):
                if t in subs.keys():
                    t=subs[t]
                weekend_matches[text[sat[0]]][text[i]].append(t)
                
if len(sun)>0:
    if len(mon)!=0:
        for i in range(sun[0]+1,mon[0]):
            weekend_matches[text[sun[0]]][text[i]]=[]
            for t in text[i].split(' v '):
                if t in subs.keys():
                    t=subs[t]
                weekend_matches[text[sun[0]]][text[i]].append(t)
    else:
        for i in range(sun[0]+1,len(text)):
            weekend_matches[text[sun[0]]][text[i]]=[]
            for t in text[i].split(' v '):
                if t in subs.keys():
                    t=subs[t]
                weekend_matches[text[sun[0]]][text[i]].append(t)

print(weekend_matches)


# In[32]:


import pandas as pd
import numpy as np
import scipy.stats as st
#files = ['E0.csv']
inp = pd.concat(pd.read_csv(f,usecols=['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR'],parse_dates=['Date']) for f in files)
#Time field not in all files#inp = pd.concat(pd.read_csv(f,usecols=['Date', 'Time', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR'],parse_dates=[['Date', 'Time']]) for f in files)

premier_league=inp[['Date','HomeTeam','FTHG','FTR']]
premier_league.rename(columns={'HomeTeam':'Team','FTHG':'Goals','FTR':'Result'},inplace=True)
premier_league['Result'] = premier_league['Result'].apply(lambda x:'W' if x=='H' else x)
premier_league['Result'] = premier_league['Result'].apply(lambda x:'L' if x=='A' else x)

temp=inp[['Date','AwayTeam','FTAG','FTR']]
temp.rename(columns={'AwayTeam':'Team','FTAG':'Goals','FTR':'Result'},inplace=True)
temp['Result'] = temp['Result'].apply(lambda x:'W' if x=='A' else x)
temp['Result'] = temp['Result'].apply(lambda x:'L' if x=='H' else x)

premier_league = pd.concat([premier_league,temp],ignore_index=True)
premier_league.dropna(axis=0,how='all',inplace=True)
premier_league.sort_values(by='Date',ascending=False,inplace=True)

temp =''
inp = ''

print(sorted(list(set(premier_league['Team']))))
premier_league


# In[33]:


##Calculating odds

def match_odds(team1,team2):
#team1 = 'Crystal Palace'
#team2 = 'Arsenal'
    def match_result(avg_list):
        avg_team1=avg_list[0]
        avg_team2=avg_list[1]
        from scipy.stats import poisson
        max_goals = 5
        team_pred = [[poisson.pmf(i, team_avg) for i in range(0, max_goals+1)] for team_avg in [avg_team1, avg_team2]]
        team_pred = np.outer(np.array(team_pred[0]), np.array(team_pred[1]))
        Pt1_win = 0
        Pt2_win = 0
        Pdraw = 0
        for i in range(0,max_goals+1):
            for j in range(0,max_goals+1):
                if i==j:
                    Pdraw +=team_pred[i][j]
                if i<j:
                    Pt2_win += team_pred[i][j]
                if i>j:
                    Pt1_win += team_pred[i][j]
        result = [Pt1_win,Pt2_win,Pdraw]
        return result

    temp = premier_league[premier_league['Team']==team1]
    team1_mean = temp['Goals'].rolling(8).mean().shift(-7).dropna()
    team1_mean = team1_mean.reset_index(drop=True)

    temp = premier_league[premier_league['Team']==team2]
    team2_mean = temp['Goals'].rolling(8).mean().shift(-7).dropna()
    team2_mean = team2_mean.reset_index(drop=True)

    team1_mean = team1_mean.to_frame(name = 'Team1_mean')
    team2_mean = team2_mean.to_frame(name = 'Team2_mean')
    poisson_dist = pd.merge(team1_mean,team2_mean,left_index=True,right_index=True)
    poisson_dist['means'] = poisson_dist.values.tolist()
    poisson_dist.index.name='case'
    if len(poisson_dist.index.values)>10008:
        poisson_dist = poisson_dist.head(10008)


    poisson_dist['Result'] = poisson_dist['means'].apply(lambda x:match_result(x))
    poisson_dist[['Pt1_win','Pt2_win','Pdraw']] = pd.DataFrame(poisson_dist['Result'].values.tolist(), index= poisson_dist.index)
    
    #poisson_dist['1-Pt1_win'] = 1 - poisson_dist['Pt1_win']
    #poisson_dist['1-Pt2_win'] = 1 - poisson_dist['Pt2_win']
    #poisson_dist['1-Pdraw'] = 1 - poisson_dist['Pdraw']
    #conflation of probabilities to combine results from all cases
    #conflation = poisson_dist['Pt1_win'].product()/(poisson_dist['Pt1_win'].product() + poisson_dist['1-Pt1_win'].product())
    
    #print(team1,team2)
    #print('Probabilities: ',poisson_dist['Pt1_win'].mean(),poisson_dist['Pt2_win'].mean(),poisson_dist['Pdraw'].mean())
    #print('Odds: ',1/poisson_dist['Pt1_win'].mean(),1/poisson_dist['Pt2_win'].mean(),1/poisson_dist['Pdraw'].mean())
    odds = [1/poisson_dist['Pt1_win'].mean(),1/poisson_dist['Pt2_win'].mean(),1/poisson_dist['Pdraw'].mean()]
    #poisson_dist
    #team1_mean
    return(odds)


# In[34]:


#generate results and output table
import datetime
out = []
for day in weekend_matches.keys():
    #print(day)
    for match in weekend_matches[day].keys():
        team1 = weekend_matches[day][match][0]
        team2 = weekend_matches[day][match][1]
        a = match_odds(team1,team2)
        #print(match)
        weekend_matches[day][match]= match.split(' v ')
        weekend_matches[day][match].append(a[0])
        weekend_matches[day][match].append(a[1])
        weekend_matches[day][match].append(a[2])
        weekend_matches[day][match].insert(0,'2020'+datetime.datetime.strptime(day,"%a %d %b").strftime("-%m-%d"))
        out.append(weekend_matches[day][match])
output = pd.DataFrame(columns=['Date','Team1','Team2','Team1 odds','Team2 odds','Draw odds'],data=out)


# In[36]:


output.to_csv('Output.csv')


# In[ ]:




