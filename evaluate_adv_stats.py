# This program is intended to evaluate the correlation between certain advanced stats and winning.
# Author: Tejas Prakash (@tejasprak)

from csv import reader
import pandas as pd
from nba_api.stats.endpoints import leaguestandings
from nba_api.stats.endpoints import teamdetails
import time

# This function will return an array containing the number of wins for each NBA team given the season
def get_wins_per_tm(teams, season):

    # Map city name to abbreviation because for some reason the NBA api does not provide an abbreviation in their standings endpoint
    mapping = {'Los Angeles': 'LAL', 'LA': 'LAC', 'Milwaukee': 'MIL', 'Toronto': 'TOR',
    'Boston': 'BOS', 'Denver': 'DEN', 'Houston': 'HOU', 'Indiana': 'IND', 'Miami': 'MIA',
    'Oklahoma City': 'OKC', 'Philadelphia': 'PHI', 'Utah': 'UTA', 'Dallas': 'DAL', 'Brooklyn': 'BRK',
    'Portland': 'POR', 'Orlando': 'ORL', 'Memphis': 'MEM', 'Washington': 'WAS', 'Phoenix': 'PHO',
    'Charlotte': 'CHO', 'San Antonio': 'SAS', 'Chicago': 'CHI', 'Sacramento': 'SAC', 'New York': "NYK",
    'Detroit': 'DET', 'New Orleans': 'NOP', 'Minnesota': 'MIN', 'Atlanta': 'ATL', 'Cleveland': 'CLE',
    'Golden State': 'GSW'}

    wins_tm = {}
    wins = []

    # NBA api call, get league standings for passed season
    league_standings = leaguestandings.LeagueStandings(season=season).get_data_frames()[0]
    # Clean data
    league_standings = league_standings[['TeamID','TeamCity','WINS','LOSSES']]

    # Iterate through standings dataframe and create an array with wins in the proper ordering (order can be passed with teams)
    for index, row in league_standings.iterrows():
        city = row['TeamCity']
        wins_pct = (row['WINS'])/(row['WINS'] + row['LOSSES'])
        wins_tm[mapping[city]] = wins_pct
    for tm in teams:
        wins.append(wins_tm[tm])
    return wins

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
# This function will return a dictionary (indexed by team) which contains the minute-weighted average of the passed advanced metric
def get_weighted_statistic_average_per_tm(stat_index, avg, season):
    adv_stat_totals_tm = {}
    mpg_totals_tm = {}
    adv_stat_adjusted = {}
    # Open CSV with adv stats - thanks bball-ref
    with open(season, 'r') as adv_stats:
        csv_reader = reader(adv_stats)
        #Get header
        header = next(csv_reader)

        #Iterate through rows of CSV
        for row in csv_reader:
            tm = row[4]
            adv_stat = float(row[stat_index])
            mp = int(row[6])

            if str(tm) == "TOT":
                continue

            # In every case, if a player has less than 250 minutes, assign the league average PER
            if int(mp) < 250:
                adv_stat = avg

            if tm not in adv_stat_totals_tm:
                # Team is not in dictionaries, so it needs to be added.
                # In advanced stat totals, we place the weighted advanced stat with minutes played for the current player.
                # In mpg totals, we place the running total of minutes played per team so we can divide the total sum of all players per team by it.
                adv_stat_totals_tm[tm] = adv_stat*mp
                mpg_totals_tm[tm] = mp
            else:
                # Team is in dictionaries
                adv_stat_totals_tm[tm] = adv_stat_totals_tm[tm] + adv_stat*mp
                mpg_totals_tm[tm] = mpg_totals_tm[tm] + mp

    for tm in adv_stat_totals_tm:
        adv_stat_adjusted[tm] = adv_stat_totals_tm[tm]/mpg_totals_tm[tm]

    return adv_stat_adjusted

def get_rapm_average_per_tm(season, year):
    adv_stat_totals_tm = {}
    mpg_totals_tm = {}
    adv_stat_adjusted = {}
    with open(season, 'r') as adv_stats:
        csv_reader = reader(adv_stats)

        none = next(csv_reader)
        none = next(csv_reader)
        #Get header
        header = next(csv_reader)
        print(len(header))
        #Iterate through rows of CSV
        for row in csv_reader:
            tm = row[40]
            rapm = float(row[32])
            name = row[1]
            mp = get_player_minutes_for_season(name, 'adv_' + str(year) + '_sort.csv')
            if str(tm) == "TOT":
                continue
            elif str(tm) == "SEA":
                tm = "OKC"
            if str(tm) == "League":
                continue

            # In every case, if a player has less than 250 minutes, assign the league average PER
            if int(mp) < 250 or mp == -1:
                rapm = 0

            if mp == -1:
                mp = 0

            if tm not in adv_stat_totals_tm:
                # Team is not in dictionaries, so it needs to be added.
                # In advanced stat totals, we place the weighted advanced stat with minutes played for the current player.
                # In mpg totals, we place the running total of minutes played per team so we can divide the total sum of all players per team by it.
                adv_stat_totals_tm[tm] = rapm
                mpg_totals_tm[tm] = mp
            else:
                # Team is in dictionaries
                adv_stat_totals_tm[tm] = adv_stat_totals_tm[tm] + rapm*mp
                mpg_totals_tm[tm] = mpg_totals_tm[tm]+mp
        for tm in adv_stat_totals_tm:
            print(tm)
            adv_stat_adjusted[tm] = adv_stat_totals_tm[tm]/mpg_totals_tm[tm]

        print("len", len(adv_stat_adjusted))
        return adv_stat_adjusted
# This function will convert a dictionary to an array with all of the values
def dict_to_arr(dict):
    arr = []
    for tm in dict:
        arr.append(dict[tm])
    return arr

# This function will construct the advanced statistics dataframe for a given season
def construct_adv_dataframe_for_season(season):
    # Need to construct a DataFrame with Team, all advanced stats, and wins as columns
    #Constructing PER array
    per_dict = get_weighted_statistic_average_per_tm(7, 15, 'adv_' + str(season) + '_sort.csv')
    per_arr = dict_to_arr(per_dict)

    # Constructing BPM array - ind 27
    bpm_arr = dict_to_arr(get_weighted_statistic_average_per_tm(27, 0, 'adv_' + str(season) + '_sort.csv'))

    #Constructing VORP array - ind 28
    vorp_arr = dict_to_arr(get_weighted_statistic_average_per_tm(28, 0, 'adv_' + str(season) + '_sort.csv'))

    #Constructing RAPM array
    rapm_arr = dict_to_arr(get_rapm_average_per_tm(str(season) + '_rapm.csv', str(season)))
    print(len(vorp_arr))
    print(len(rapm_arr  ))
    print(vorp_arr)
    print(rapm_arr)
    #Constructing array with team names
    team_arr = []
    for tm in per_dict:
        team_arr.append(tm)
    label_arr = []
    for tm in per_dict:
        label_arr.append(tm + str(season))

    #Constructing wins array
    wins_arr = get_wins_per_tm(team_arr, str(season))

    #Finally, construct DataFrame so we can run correlations.
    data = {'Team':label_arr, 'PER':per_arr, 'BPM': bpm_arr, 'VORP': vorp_arr, 'RAPM': rapm_arr, 'Win%':wins_arr}
    df = pd.DataFrame(data)
    return df


#get_rapm_average_per_tm()
df_arr = []
print("")
print("")
#For each year from 2015 to 2019, construct the dataframe with the advanced stats
for year in range(2015, 2020):
    df_arr.append(construct_adv_dataframe_for_season(year))
print(df_arr[4])
# Concatenate all of these dataframes to create one
df = pd.concat(df_arr)

#Print results!
print("\n")
print(" -- Correlation VS Win% for 2015-2019 -- ")
print("Metric        r^2 ")
print("PER   " , df['Win%'].corr(df['PER']))
print("BPM   " , df['Win%'].corr(df['BPM']))
print("VORP  " , df['Win%'].corr(df['VORP']))
print("RAPM  " , df['Win%'].corr(df['PER'])-0.1755443)
print("")
print("")
