# Program to calculate RAPM for given season, with option to calculate for 3 year or 5 year periods.
# Uses the open source work of https://github.com/903124/statsnba-playbyplay/ and https://github.com/EvanZ/nba-rapm, and adapted for nba_api/

from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.library.parameters import Season
from nba_api.stats.library.parameters import SeasonType
from nba_api.stats.endpoints import playbyplay
from sklearn.feature_extraction import DictVectorizer
from sklearn import linear_model


import pandas as pd

def matchup_to_df(matchups):
    lst = []
    for matchup in sample_game.Matchups:
        matchup_dict = {}
        _home_players = sorted([p.PlayerName for p in matchup.HomePlayers])
        _away_players = sorted([p.PlayerName for p in matchup.AwayPlayers])
        home_players = dict(zip(['h{}'.format(i) for i in range(5)], _home_players))
        away_players = dict(zip(['a{}'.format(i) for i in range(5)], _away_players))

        matchup_dict.update(home_players)
        matchup_dict.update(away_players)
        home_boxscore = matchup.Boxscore.HomeTeamStats
        away_boxscore = matchup.Boxscore.AwayTeamStats

        matchup_dict.update({'home_{}'.format(k):v for k,v in home_boxscore.items()})
        matchup_dict.update({'away_{}'.format(k):v for k,v in away_boxscore.items()})
        lst.append(matchup_dict)
    return lst

def get_rapm_for_season(season):
    #Get all matchups
    all_matchups = []
    nba_teams = teams.get_teams()
    for team in nba_teams:
        print(team['id'])
        gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team['id'],season_nullable=Season.default, season_type_nullable=SeasonType.regular)
        games_dict = gamefinder.get_normalized_dict()
        games = games_dict['LeagueGameFinderResults']
        game = games[0]
        game_id = game['GAME_ID']
        game_matchup = game['MATCHUP']
        df = playbyplay.PlayByPlay(game_id).get_data_frames()[0]
        all_matchups.append(df)
    import time
    start_time = time.time()

    df = pd.DataFrame()
    for i,game_id in enumerate(game_ids):
        if(game_id == game_ids[198] or game_id == game_ids[667]):
            continue
        sample_game_id = game_id
        sample_game = Game(sample_game_id)
        df = df.append(pd.DataFrame(matchup_to_df(sample_game.Matchups)))
    data = df.to_dict('record')
    units = []
    points = []
    weights = []

    for d in data:

        home_poss = int(d['home_Possessions'])
        away_poss = int(d['away_Possessions'])

        home_name = [d['h0'],d['h1'],d['h2'],d['h3'],d['h4']]
        away_name = [d['a0'],d['a1'],d['a2'],d['a3'],d['a4']]
        home_offense_unit = {"{},offense".format(name): 1 for name in home_name}
        home_defense_unit = {"{},defense".format(name): 1 for name in home_name}
        away_offense_unit = {"{},offense".format(name): 1 for name in away_name}
        away_defense_unit = {"{},defense".format(name): 1 for name in away_name}

        home_stint = home_offense_unit.copy()
        home_stint.update(away_defense_unit)
        home_stint.update({'HCA': 1})
        away_stint = away_offense_unit.copy()
        away_stint.update(home_defense_unit)
        away_stint.update({'HCA': -1})

        if home_poss >= 1:
            home_ortg = 100 * int(d['home_PTS']) / home_poss
            units.append(home_stint)
            points.append(home_ortg)
            weights.append(home_poss)

        if away_poss >= 1:
            away_ortg = 100 * int(d['away_PTS']) / away_poss
            units.append(away_stint)
            points.append(away_ortg)
            weights.append(away_poss)

    print(len(units), len(points), len(weights))

    u = DictVectorizer(sparse=False)
    u_mat = u.fit_transform(units)

    #Now use ridge to regularize and solve the matrix

    clf = linear_model.RidgeCV(alphas=(np.array([0.01, 0.1, 1.0, 10, 100, 500, 750, 1000, 1500, 2000, 5000])), cv=5)
    clf.fit(u_mat, points, sample_weight=weights)

    ratings = []
    for player in players:
        ratings.append((player, clf.coef_[players.index(player)]))
    return ratings

print(get_rapm_for_season(2019))
