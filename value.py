from csv import reader
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np


def create_arrays_for_season(season):
    x = []
    y = []
    with open('csv/all_salaries.csv', 'r') as value:
        csv_reader = reader(value)
        #Get header
        header = next(csv_reader)
        #print(header)
        for row in csv_reader:
            #print(row)
            name = row[1]
            length = len(name.split(" "))
            if length == 1:
                first = name.split("\\")[0]
            else:
                first = name.split(" ")[0]
                last = name.split(" ")[1].split("\\")[0]

            if last == "Jokić":
                last = "Jokic"
            if last == "Vučević":
                last = "Vucevic"
            if last == "Bogdanović":
                last = "Bogdanovic"
            if last == "Dragić":
                last = "Dragic"
            if last == "Schröder":
                last = "Schroder"
            if last == "Valančiūnas":
                last = "Valanciunas"
            if last == "Nurkić":
                last = "Nurkic"
            name = first + " " + last
            if first == "Marcus" and last == "Morris":
                name = "Marcus Morris Sr."
            if first == "Kelly" and last == "Oubre":
                name = "Kelly Oubre Jr."
            if last == "Hardaway":
                name = "Tim Hardaway Jr."
            if first == "Otto":
                name = "Otto Porter Jr."
            if name == "Dāvis Bertāns":
                name = "Davis Bertans"
            if name == "J.J. Redick":
                name = "JJ Redick"
            if name == "Larry Nance":
                name = "Larry Nance Jr."
            if name == "Tomáš Satoranský":
                name = "Tomas Satoransky"

            salary = row[4]
            year = int(row[5])
            if salary and year == (season + 1):
                #salary = int(salary[1:])
                df = rapm_df.loc[rapm_df['playerName'] == name]
                if df.empty:
                    continue
                for key, val in df.iterrows():
                    rapm = val['RAPM']
                mp = get_player_minutes_for_season(name, 'csv/adv_' + str(year-1) + '_sort.csv')
                if (mp == -1) or (mp < 1000):
                    continue
                #rapm = df['RAPM']
                x.append(rapm)
                y.append(salary)
                #print(name, " x: ", rapm, "y: ", salary)
    return x,y

def get_player_minutes_for_season(player, season):
    with open(season, 'r') as adv_stats:
        csv_reader = reader(adv_stats)
        #Get header
        header = next(csv_reader)
        #print(header)
        for row in csv_reader:
            #print(row)
            name = row[1]
            length = len(name.split(" "))
            if length == 1:
                first = name.split("\\")[0]
            else:
                mp = int(row[6])
                first = name.split(" ")[0]
                last = name.split(" ")[1].split("\\")[0]

            if player == (first + " " + last):
                return mp
    return -1

rapm_df = pd.read_csv('csv/3yr_RAPM.csv', skiprows = 1)

x, y = [], []
for year in range(2017, 2020):
    print(year)
    x1, y1 = create_arrays_for_season(year)
    x = x + x1
    y = y + y1

#print(x)
#print(y)
#print(len(x))
#print(len(y))
model = LinearRegression()
x = np.array(x)
y = np.array(y)
model.fit(x.reshape(-1,1), y)

dict = {}

with open('csv/1920_salary.csv', 'r') as value:
    csv_reader = reader(value)
    #Get header
    next(csv_reader)
    header = next(csv_reader)
    #print(header)
    for row in csv_reader:
        name = row[1]
        length = len(name.split(" "))
        if length == 1:
            first = name.split("\\")[0]
        else:
            first = name.split(" ")[0]
            last = name.split(" ")[1].split("\\")[0]

        # one dataset doesn't have the accents on the European names or Jr/Sr. Annoying.

        if last == "Jokić":
            last = "Jokic"
        if last == "Vučević":
            last = "Vucevic"
        if last == "Bogdanović":
            last = "Bogdanovic"
        if last == "Dragić":
            last = "Dragic"
        if last == "Schröder":
            last = "Schroder"
        if last == "Valančiūnas":
            last = "Valanciunas"
        if last == "Nurkić":
            last = "Nurkic"
        name = first + " " + last
        if first == "Marcus" and last == "Morris":
            name = "Marcus Morris Sr."
        if first == "Kelly" and last == "Oubre":
            name = "Kelly Oubre Jr."
        if last == "Hardaway":
            name = "Tim Hardaway Jr."
        if first == "Otto":
            name = "Otto Porter Jr."
        if name == "Dāvis Bertāns":
            name = "Davis Bertans"
        if name == "J.J. Redick":
            name = "JJ Redick"
        if name == "Larry Nance":
            name = "Larry Nance Jr."
        if name == "Tomáš Satoranský":
            name = "Tomas Satoransky"
        salary = row[3]
        mp = get_player_minutes_for_season(name, 'csv/adv_' + str(2019) + '_sort.csv')
        if (mp == -1) or (mp < 1000):
            continue
        if salary:
            salary = int(salary[1:])
            df = rapm_df.loc[rapm_df['playerName'] == name]
            if df.empty:
                continue
            #print(df)
            rapm = df['RAPM']
        else: continue
        rapm = np.array(rapm)
        if first == "Kristaps" or first == "D'Angelo":
            rapm = np.array([0.51])
        #print(rapm)
        #print("Name: ", name, "Salary: ", salary, "RAPM", rapm)
        prediction = model.predict([rapm])
        print("Name: ", name, "Salary: ", salary, "RAPM", rapm, "Prediction", prediction, "Difference", float(salary)-float(prediction[0]))

        dict[name] = float(salary)-(float(prediction[0]))

print(sorted(dict.items(), key=lambda x:x[1]))
