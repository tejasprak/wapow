from django.shortcuts import render
from nba_api.stats.library.parameters import *
from nba_api.stats.endpoints import leaguegamelog
from nba_api.stats.endpoints import commonplayerinfo
from nba_api.stats.endpoints import playercareerstats
import requests
from nba_api.stats.static import players
import json
import collections
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import base64
import numpy as np
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from os import path


matplotlib.use('Agg')


def plot_graph(df):
    x = []
    y = []
    n = []
    for row in df.itertuples():
        x.append(row.raptor_offense)
        y.append(row.raptor_defense)
        name = row.player_name
        if len(name.split(" ")) == 2:
            fname, lname = name.split(" ")
            name = fname[0] + ". "  + lname
        n.append("  " + name)
    fig, ax = plt.subplots(figsize=(18,10))
    ax.scatter(x, y)
    for i, txt in enumerate(n):
        if float(x[i]) > 4 or float(y[i]) > 3.5 or float(x[i]) < -3.25 or float(y[i]) < -3.25:
            ax.annotate(txt, (x[i], y[i]))

    #plt.xticks(np.arange(-5, 10, 0.5))
    #plt.yticks(np.arange(-5, 6, 0.5))
    plt.xticks(np.arange(int(min(x)), int(max(x))+1, 1))
    plt.yticks(np.arange(int(min(y)), int(max(y))+1, 1))
    fig.suptitle('RAPTOR Offense vs Defense', fontsize=20)
    plt.xlabel('RAPTOR_Offense', fontsize=18)
    plt.ylabel('RAPTOR_Defense', fontsize=18)
    plt.savefig('testplot.png')
    with open("testplot.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string

# Create your views here.
def index(request):
    return render(request, 'nbasite/index.html')

def player(request, player_name_url):
    # Get first name and last name from URL and find the ID
    first_name = player_name_url.split("_")[0]
    last_name = player_name_url.split("_")[1]
    player = players.find_players_by_full_name(first_name + " " + last_name)
    player_id = player[0]['id']
    image = "https://cdn.nba.com/headshots/nba/latest/1040x760/" + str(player_id) + ".png"
    #print(image)

    #Use function to get player info
    player_info = get_player_info(player_id)

    #Get player season by season stats
    season_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
    season_stats = season_stats.season_totals_regular_season.get_json()
    #season_stats = json.loads(season_stats)
    df = json.loads(season_stats)
    #df = df['data']
    season = pd.DataFrame.from_dict(df, orient='index')
    #season = season[["SEASON_ID","TEAM_ABBREVIATION","GP","GS","MIN","PLAYER_AGE","PTS","AST","REB","DREB","OREB","BLK","STL","FGM","FGA","FG_PCT","FTM","FTA","FT_PCT","FG3M","FG3A","FG3_PCT", "PF"]]
    season.rename(columns={"TEAM_ABBREVIATION": 'TM', 'PLAYER_AGE': 'AGE', 'SEASON_ID': 'SEASON'}, inplace=True)
    season.sort_index(axis=0,ascending=True, inplace=True)
    season = season.to_html()
    context_dict = {'image': image, 'player_name': first_name + " " + last_name, 'player_info': player_info, 'seasons': season}
    return render(request, 'nbasite/player.html', context_dict)

def eval(request):

    return render(request, 'nbasite/eval.html');


class SeasonForm(forms.Form):
    CHOICES =(
    ("5year", "5 Year RAPM ((15-16 -> 19-20))"),
    ("3yr", "3 Year RAPM ((17-18 -> 19-20))"),
    ("2015", "2015"),
    ("2016", "2016"),
    ("2017", "2017"),
    ("2018", "2018"),
    ("2019", "2019"),
    )
    Choose_RAPM_Season_Or_Rolling = forms.ChoiceField(choices=CHOICES)

def rapm(request):
    season = "None"
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = SeasonForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            season = str(form.cleaned_data['Choose_RAPM_Season_Or_Rolling'])
            print(season)
            #return HttpResponseRedirect('rapm')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = SeasonForm()


    if season != "None":
        filename = "nbasite/csv/" + str(season) + "_rapm.csv"
    else:
        filename = 'nbasite/csv/5year_RAPM.csv'
    df = pd.read_csv(filename, skiprows = 1)
    df = df[['playerId','playerName','RAPM','RAPM_Rank','RAPM__Off', 'RAPM__Off_Rank','RAPM__Def', 'RAPM__Def_Rank','teamName','season']]
    df = df.sort_values('RAPM_Rank')
    html = df.to_html(index=False)
    html = html[37:]
    html = """<table style="margin-left:auto;margin-right:auto;" class="sortable">""" + html
    context_dict = {'projections': html, 'form': form}
    return render(request, 'nbasite/rapm.html', context_dict)

def calculate_rapm(request):
    context_dict = {}
    return render(request, 'nbasite/calculate_rapm.html',context_dict)


def value(request):
    MINUTES_PLAYED_LIMIT = 1000
    #Get most current CSV with RAPTOR projections from 538 site
    df = pd.read_csv("https://projects.fivethirtyeight.com/nba-model/2020/latest_RAPTOR_by_player.csv")

    #Clean data to prepare for HTML
    del df['player_id']
    del df['poss']
    del df['pace_impact']
    del df['war_reg_season']
    del df['war_playoffs']
    del df['raptor_box_offense']
    del df['raptor_box_defense']
    del df['raptor_box_total']
    del df['raptor_onoff_offense']
    del df['raptor_onoff_defense']
    del df['raptor_onoff_total']
    del df['predator_offense']
    del df['predator_defense']
    del df['predator_total']
    #del df['predator_total']
    df = df[df.mp > MINUTES_PLAYED_LIMIT]
    df.raptor_total = df.raptor_total.astype(float)
    df = df.sort_values(by='raptor_total',ascending=False)

    encoded_string = plot_graph(df)

    html = df.to_html(index=False)
    html = html[37:]
    html = """<table class="sortable">""" + html
    context_dict = {'projections': html, 'image': encoded_string.decode('utf-8')}
    return render(request, 'nbasite/value.html', context_dict)
