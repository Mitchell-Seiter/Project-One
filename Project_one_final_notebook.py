#!/usr/bin/env python
# coding: utf-8

# In[1]:


from sqlalchemy import create_engine
from sqlalchemy import inspect
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns
get_ipython().run_line_magic('config', "InlineBackend.figure_formats = ['svg']  # or retina")
get_ipython().run_line_magic('matplotlib', 'inline')

sns.set(context='notebook', 
    style='whitegrid', 
    font_scale=1.1)

import warnings
warnings.filterwarnings('ignore')


# In[2]:


engine = create_engine("sqlite:///MTA.db")


# In[3]:


insp = inspect(engine)
print(insp.get_table_names())


# In[4]:


df = pd.read_sql('SELECT * FROM MTA;' , engine)


# In[5]:


#df.head()


# In[6]:


copy_df = df #copy of my DF


# In[7]:


#sample_df = df.head(100000) ##smaller data set might use for testing to ease run times


# In[8]:


copy_df = df.sort_values(by = ["C/A", "UNIT" , "SCP" , "DATE" , "TIME"]) 
##cleaning up DF some files were imported out of order


# In[9]:


copy_df = copy_df.reset_index() ##values not in correct indices


# In[10]:


#copy_df.head()


# In[11]:


copy_df = copy_df.drop(columns = ["index"]) ##not needed column


# In[12]:


##copy_df[['ENTRIES']] = copy_df[['ENTRIES']].apply(pd.to_numeric), 
#getting error, headers were imported from multiple txt files


# In[13]:


i = copy_df[(copy_df.ENTRIES == "ENTRIES")].index #dicovering which rows causing errors 


# In[14]:


copy_df = copy_df.drop(i) ##dropping bad rows


# In[15]:


sample_df = copy_df.head(100000)


# In[16]:


#df.LINENAME.unique() some line names that are identical but order is mixed eg. ACENQRS1237W & 1237ACENQRSWd


# In[17]:


copy_df[['ENTRIES']] = copy_df[['ENTRIES']].apply(pd.to_numeric) #converting ENTRIES to numeric
copy_df = copy_df.rename(columns = {"EXITS                                                               " : "EXITS"})


# In[18]:


#sample_df["LINENAME"] = sample_df["LINENAME"].apply(lambda x: ''.join(sorted(x)))
#sample_df.head(100000)
#sample_df["STATION_LINE"] = sample_df["STATION"] + " " + sample_df["LINENAME"]


# In[19]:


copy_df["LINENAME"] = copy_df["LINENAME"].apply(lambda x: ''.join(sorted(x)))                                            


# In[20]:


copy_df["STATION_LINE"] = copy_df["STATION"] + " " + copy_df["LINENAME"]


# In[21]:


#print(len(copy_df.LINENAME.unique()))
#print(len(df.LINENAME.unique()))
copy_df.head()


# In[22]:


turnstiles_daily = (copy_df.groupby(["C/A", "UNIT", "SCP", "STATION_LINE", "DATE" ,"TIME"],as_index=False).ENTRIES.last())


# In[23]:


turnstiles_daily["DAILY_ENTRIES"] = turnstiles_daily["ENTRIES"].diff()


# In[24]:


turnstiles_daily = turnstiles_daily.drop(turnstiles_daily.index[turnstiles_daily['DAILY_ENTRIES'] <= 0.0])
#dropping all negative values


# In[25]:


turnstiles_daily = turnstiles_daily.dropna()


# In[26]:


#turnstiles_daily.describe()#1.5
turnstiles_daily.head()


# In[27]:


IQR = turnstiles_daily.describe().loc["75%"]["DAILY_ENTRIES"] - turnstiles_daily.describe().loc["25%"]["DAILY_ENTRIES"]

IQR


# In[28]:


max_threshold = turnstiles_daily.describe().loc["75%"]["DAILY_ENTRIES"] + IQR * 100
min_threshold = turnstiles_daily.describe().loc["25%"]["DAILY_ENTRIES"] - IQR * 100


# In[29]:


turnstiles_daily = turnstiles_daily.drop(turnstiles_daily.index[turnstiles_daily['DAILY_ENTRIES'] <= min_threshold])
turnstiles_daily = turnstiles_daily.drop(turnstiles_daily.index[turnstiles_daily['DAILY_ENTRIES'] >= max_threshold])


# In[30]:


turnstiles_daily.head()


# In[31]:


station_daily = turnstiles_daily.groupby(["STATION_LINE"])[['DAILY_ENTRIES']].sum().reset_index()


# In[32]:


station_daily = station_daily.sort_values(by = ["DAILY_ENTRIES"], ascending = False).reset_index()


# In[33]:


station_daily["DAILY_ENTRIES"] = station_daily["DAILY_ENTRIES"] / 90.0
#obtaining the average daily entries. .mean did not work as expected. 
station_daily = station_daily.round(pd.Series(0, index=["DAILY_ENTRIES"]))


# In[34]:


station_daily = station_daily.drop(columns = ["index"])


# In[35]:


station_list = list(station_daily.head(50)["STATION_LINE"])


# In[36]:


station_daily.head(15)


# In[37]:


busiest_times = turnstiles_daily.groupby("TIME")[['DAILY_ENTRIES']].sum()


# In[38]:


busiest_times = busiest_times.drop(busiest_times.index[busiest_times['DAILY_ENTRIES'] <= 1000000])
busiest_times = busiest_times.sort_values(by = ["TIME"], ascending = True).reset_index()


# In[39]:


time_mask = ((busiest_times.TIME != '21:00:00') & (busiest_times.TIME != '17:00:00') &
             (busiest_times.TIME != '13:00:00') & (busiest_times.TIME != '09:00:00') &
            (busiest_times.TIME != '01:00:00'))

#mask = ((df.calories > 100) &  (df.sugars < 8) & ((df.mfr == 'K') | (df.mfr == 'G')))


# In[40]:


busiest_times = busiest_times[time_mask]


# In[41]:


busiest_days = turnstiles_daily.groupby("DATE")[['DAILY_ENTRIES']].sum().reset_index()


# In[42]:


busiest_days["DATE"] = pd.to_datetime(busiest_days["DATE"])
busiest_days["DAY_OF_WEEK"] = busiest_days["DATE"].dt.dayofweek


# In[43]:


busiest_days = busiest_days.groupby(["DAY_OF_WEEK"]).DAILY_ENTRIES.mean()


# In[44]:


busiest_days.head()


# In[51]:


first_plot = (plt.plot(busiest_days),plt.title('Average Number of Entries by Day'), plt.xlabel('Days of the Week'),
              plt.ylabel('Number of Entries'))
x_labels = ("Mon", "Tues", "Wed" , "Thur" ,"Fri" , "Sat", "Sun") 
positions = (0,1, 2, 3,4,5,6)
plt.xticks(positions, x_labels)


# In[52]:


plot_peak_times = sns.barplot(x = busiest_times["DAILY_ENTRIES"], y = busiest_times["TIME"])
#plot.set_xticklabels(plot.get_xticklabels(),rotation = 30)


# In[53]:


plot_top_stations = (sns.barplot(x = station_daily["DAILY_ENTRIES"], y = station_daily.head(10).STATION_LINE))


# In[54]:


#mask = (station_daily['STATION_LINE'] == 'CATHEDRAL PKWY 1')


# In[55]:


#print(len(sorted(station_list[0:50])))


# In[56]:


uni_table = pd.read_sql('SELECT * FROM MTA;' , engine)


# In[57]:


uni_table = pd.read_sql('SELECT "C/A", UNIT, SCP, STATION, LINENAME, DATE, TIME, ENTRIES FROM MTA;' , engine)


# In[58]:


uni_table = pd.read_sql('SELECT * FROM MTA WHERE "TIME" LIKE "%00" GROUP BY "C/A", "UNIT" , "SCP" , "DATE" , "TIME" HAVING SUM(ENTRIES) ORDER BY "C/A", "UNIT" , "SCP" , "DATE" , "TIME"', engine)

#SQL Queries filtering unwanted time values, and dropping unwanted columns, grouping in needed groups                         


# In[59]:


w = uni_table[(uni_table.ENTRIES == "ENTRIES")].index
uni_table = uni_table.drop(w)
uni_table[['ENTRIES']] = uni_table[['ENTRIES']].apply(pd.to_numeric) #converting ENTRIES to numeric
uni_table = uni_table.rename(columns = {"EXITS                                                               " : "EXITS"})
uni_table["LINENAME"] = uni_table["LINENAME"].apply(lambda x: ''.join(sorted(x)))
uni_table["STATION_LINE"] = uni_table["STATION"] + " " + uni_table["LINENAME"]


# In[60]:


uni_table.head()


# In[61]:


uni_table = (copy_df.groupby(["C/A", "UNIT", "SCP", "STATION_LINE", "DATE" ,"TIME"],as_index=False).ENTRIES.last())


# In[62]:


uni_table["DAILY_ENTRIES"] = uni_table["ENTRIES"].diff()

uni_table = uni_table.drop(uni_table.index[uni_table['DAILY_ENTRIES'] <= 0.0])
uni_table = uni_table.dropna()


# In[63]:


IQR_uni = uni_table.describe().loc["75%"]["DAILY_ENTRIES"] - uni_table.describe().loc["25%"]["DAILY_ENTRIES"]

max_threshold = uni_table.describe().loc["75%"]["DAILY_ENTRIES"] + IQR_uni * 100
min_threshold = uni_table.describe().loc["25%"]["DAILY_ENTRIES"] - IQR_uni * 100

uni_table = uni_table.drop(uni_table.index[uni_table['DAILY_ENTRIES'] <= min_threshold])
uni_table = uni_table.drop(uni_table.index[uni_table['DAILY_ENTRIES'] >= max_threshold])


# In[64]:


busiest_uni = uni_table.groupby(["STATION_LINE"])[['DAILY_ENTRIES']].sum()


# In[65]:


NYU_Sciences_mask = ((station_daily.STATION_LINE == '8 ST-NYU NRW') 
                     | (station_daily.STATION_LINE == 'ASTOR PL 6') |
                        (station_daily.STATION_LINE == 'W 4 ST-WASH SQ ABCDEFM'))

Colu_Barnard_mask = ((station_daily.STATION_LINE == 'CATHEDRAL PKWY 1') 
                     | (station_daily.STATION_LINE == '116 ST-COLUMBIA 1')) 
                        
CUNYman_Pace_mask = ((station_daily.STATION_LINE == 'CANAL ST ACE') 
                     | (station_daily.STATION_LINE == 'CHAMBERS ST 123') | 
                        (station_daily.STATION_LINE == 'FRANKLIN AV 2345S') |
                        (station_daily.STATION_LINE == 'FULTON ST G') |
                        (station_daily.STATION_LINE == 'FPATH NEW WTC 1'))

CUNYhunt_NYUnurs_mask = ((station_daily.STATION_LINE == '1 AV L') 
                     | (station_daily.STATION_LINE == '14 ST-UNION SQ 456LNQRW') |
                        (station_daily.STATION_LINE == '28 ST 6'))
                  

NYCtech_NYUengin_mask = ((station_daily.STATION_LINE == 'BOROUGH HALL 2345R') 
                     | (station_daily.STATION_LINE == 'COURT SQ-23 ST EGM') | 
                        (station_daily.STATION_LINE == 'HIGH ST AC') |
                        (station_daily.STATION_LINE == 'YORK ST F'))


# In[66]:


#NYU ARTS AND COLLEGES [8th Street Station, Astor, W 4 ST]
#Columbia Univ & Barnard College [116th ST Station, Cathedral PK 110 ST]
#CUNY Borough of Manhattan Community College [ Chambers, Franklin, Canal, FULTON, WTC] (Also close to PACE COllEGE)
#CUNY Hunter College & NYU college of nursing and hospital [1st AV, 14st Union SQ 28th ST Station]
#NYC Colllege of Tech and NYU Engineering School [Bourough, Court, High, York]


# In[101]:


busiest_uni1 = station_daily[NYU_Sciences_mask]
busiest_uni2 = station_daily[Colu_Barnard_mask]
busiest_uni3 = station_daily[CUNYman_Pace_mask]
busiest_uni4 = station_daily[CUNYhunt_NYUnurs_mask]
busiest_uni5 = station_daily[NYCtech_NYUengin_mask]


# In[104]:


busiest_uni1["CAMPUSES"] = "NYU Sciences"
busiest_uni2["CAMPUSES"] = "Columbia and Barnard"
busiest_uni3["CAMPUSES"] = "CUNY Manhattan and Pace"
busiest_uni4["CAMPUSES"] = "CUNY Hunter and NYU Nursing"
busiest_uni5["CAMPUSES"] = "NYC Tech and NYU Engineering"


# In[105]:


busiest_uni = pd.concat([busiest_uni1, busiest_uni2, busiest_uni3, busiest_uni4, busiest_uni5])
a = busiest_uni.groupby(["CAMPUSES", "STATION_LINE"], as_index = False).DAILY_ENTRIES.sum()


# In[76]:



a.head(20)


# In[106]:


sns.catplot( data=busiest_uni[NYU_Sciences_mask], kind="bar", x="DAILY_ENTRIES", y="STATION_LINE")


# In[72]:


sns.catplot(data=busiest_uni[Colu_Barnard_mask], kind="bar", x="DAILY_ENTRIES", y="STATION_LINE")


# In[73]:


sns.catplot(data=busiest_uni[CUNYman_Pace_mask], kind="bar",x="DAILY_ENTRIES", y="STATION_LINE")


# In[74]:


sns.catplot(data=busiest_uni[CUNYhunt_NYUnurs_mask], kind="bar",x="DAILY_ENTRIES", y="STATION_LINE")


# In[75]:


NYCtech_NYUengin = sns.barplot(x=busiest_uni[NYCtech_NYUengin_mask].DAILY_ENTRIES, y=busiest_uni[NYCtech_NYUengin_mask].STATION_LINE)


# In[ ]:


def get_station_traffic():
    print("Please select one or more of the following by number [END TO QUIT]:")
    value = "ok"
    dfx = pd.DataFrame()
    for idx, i in enumerate(station_list):
        print(idx, i)
    while value != "END":
        
        value = input()
        if value.isnumeric():
            value = int(value)
            value_line = station_list[value]
            value_mask = (station_daily.STATION_LINE == value_line)
            dfx = dfx.append(station_daily[value_mask])
            #plot1 = sns.barplot(y = station_daily["DAILY_ENTRIES"], x = station_daily[lines].STATION_LINE)
            plot1 = sns.barplot(y = station_daily["DAILY_ENTRIES"], x = dfx.STATION_LINE)
            print(station_daily[value_mask])
            


# In[ ]:


#####BEGIN JUPYTER SLIDES HERE


# ![](https://i.imgur.com/LA6hyQA.png)

# <h2> Introduction </h2>
# 
# - Motivation: to increase overall womens particapation in tech fields
# - Objective: raise awareness and involvement for the oganization WTWY
# - Goald: find how WTWY can be most effective in gaining support around NYC
#     
# ![Metis Logo](https://mms.businesswire.com/media/20181211005178/en/549272/2/metis_logo_black_horiz.jpg)

# <h2> Methodology </h2>
# 
# <h4> Primary Data source: </h4> Most of the primary data came from the MTA NYC turnstile data, with some tertiary data coming from CollegeSimply for enrollment numbers, and google maps to check locations. 
# 
# ![Metis Logo](https://mms.businesswire.com/media/20181211005178/en/549272/2/metis_logo_black_horiz.jpg)

# <h2> Methodology Cont </h2>
# 
# - Using Python and SQL we are able to clean up our data sources and present it graphically making it easier to read and more accessible.
# - Key metrics we are looking at include busiest subways, peak times, including days and hours, and proximity to universities/colleges. 
# 
# ![Metis Logo](https://mms.businesswire.com/media/20181211005178/en/549272/2/metis_logo_black_horiz.jpg)

# <h2> Results </h2>
# 
# 
# <img align="left" width="500" height="500" src="https://i.imgur.com/1cvXfCN.png">
# 
# 
# 
# <img align="right" width="500" height="500" src="https://i.imgur.com/zcl7T9t.png">
# 
# 
# 

# <h2> Results Cont </h2>
# 
# <img align="left" width="400" height="400" src="https://i.imgur.com/kQcAmfG.png">
# 
# <img align="right" width="400" height="400" src="https://i.imgur.com/nVToXW5.png">

# <h2> Results Cont </h2>
# 
# <img align="left" width="400" height="400" src="https://i.imgur.com/iT4uZqr.png">
# 
# 
# <img align="right" width="400" height="400" src="https://i.imgur.com/tajAADS.png">

# <h2> Results Cont </h2>
# 
# 
# <p align="center">
#   <img width="460" height="300" src="https://i.imgur.com/UAjQssE.png">
# </p>

# <h2> Conclusion </h2>
# 
# - Would focus efforts during the middle of the week (Tuesday-Friday)
# - Heaviest traffic for subway stops is centered around the early/late evening
# - For the most part there is a clear heavier use subway stop around the various campus. Would try at those stops first.
# 
# ![Metis Logo](https://mms.businesswire.com/media/20181211005178/en/549272/2/metis_logo_black_horiz.jpg)

# <h2> Future Work </h2>
# 
# - With a little more given time we could further isolate the most heavily trafficked subway stations in close proximity to university campuses. 
# - Could incorporate more geo location data to make sure the WTWY representatives are most efficient in collecting support. 
# 
# ![Metis Logo](https://mms.businesswire.com/media/20181211005178/en/549272/2/metis_logo_black_horiz.jpg)

# In[115]:


get_station_traffic()


# ![](https://i.imgur.com/LA6hyQA.png)

# In[ ]:


###END SLIDES


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[109]:


sns.catplot( data=busiest_uni[NYU_Sciences_mask], kind="bar", x="DAILY_ENTRIES", y="STATION_LINE").set(title = "NYU Sciences")
plt.savefig('NYUscience123' , bbox_inches='tight')


# In[110]:


sns.catplot(data=busiest_uni[CUNYhunt_NYUnurs_mask], kind="bar",x="DAILY_ENTRIES", y="STATION_LINE").set(title = "CUNY Hunters and NYU Nursing")
plt.savefig('Nurses123' , bbox_inches='tight')


# In[111]:


NYCtech_NYUengin = sns.barplot(x=busiest_uni[NYCtech_NYUengin_mask].DAILY_ENTRIES, y=busiest_uni[NYCtech_NYUengin_mask].STATION_LINE).set(title="NYC Tech and NYU Engineering")
plt.savefig('Techengine123' , bbox_inches='tight')


# In[98]:


sns.catplot(data=busiest_uni[Colu_Barnard_mask], kind="bar", x="DAILY_ENTRIES", y="STATION_LINE").set(title="Columbia and Barnard")
plt.savefig("ColombiaBarnard")


# In[97]:


sns.catplot( data=busiest_uni[CUNYman_Pace_mask], kind="bar", x="DAILY_ENTRIES", y="STATION_LINE").set(title='CUNY Manhattan and Pace')
plt.savefig('CUNYman')


# In[94]:


plot_peak_times = sns.barplot(x = busiest_times["DAILY_ENTRIES"], y = busiest_times["TIME"]).set(title='Entries by hours')
plt.savefig('Busy_Times3')


# In[89]:


first_plot = (plt.plot(busiest_days),plt.title('Average Number of Entries by Day'), plt.xlabel('Days of the Week'),
              plt.ylabel('Number of Entries'))
x_labels = ("Mon", "Tues", "Wed" , "Thur" ,"Fri" , "Sat", "Sun") 
positions = (0,1, 2, 3,4,5,6)
plt.xticks(positions, x_labels)
plt.savefig('Busy_Days')


# In[ ]:




