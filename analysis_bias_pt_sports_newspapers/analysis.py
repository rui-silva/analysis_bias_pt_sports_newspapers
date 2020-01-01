import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import pandas as pd
import datetime as dt
from categorical_yearplot import cyearplot
from covers_dataset import CoversDataset, get_file_path_date, get_file_path_newspaper
from utils import LabelClass, Clubs, Newspaper

PT_MONTH_LABELS = [
    'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out',
    'Nov', 'Dez'
]
PT_DAY_LABELS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom']


def filter_newspapers(df, newspapers):
    return df[df["Newspaper"].isin(newspapers)]


def filter_df_game_data_by_team_and_result(game_data_df, cond_team, cond_result):
    is_home_team_and_wins = (game_data_df['Home_Team'] == cond_team) & (
        game_data_df['Home_Score'] > game_data_df['Away_Score'])
    is_away_team_and_wins = (game_data_df['Away_Team'] == cond_team) & (
        game_data_df['Away_Score'] > game_data_df['Home_Score'])
    is_home_team_and_not_wins = (game_data_df['Home_Team'] == cond_team) & (
        game_data_df['Home_Score'] <= game_data_df['Away_Score'])
    is_away_team_and_not_wins = (game_data_df['Away_Team'] == cond_team) & (
        game_data_df['Away_Score'] <= game_data_df['Home_Score'])

    if cond_result == 'win':
        team_idxs = is_home_team_and_wins | is_away_team_and_wins
    elif cond_result == 'non-win':
        team_idxs = is_home_team_and_not_wins | is_away_team_and_not_wins
    return game_data_df[team_idxs]


def produce_cover_counts(df):
    counts = np.zeros(len(LabelClass))
    for index, row in df.iterrows():
        counts[list(row['Highlighted_Labels'])] += 1

    return counts[Clubs.ids()]


def cover_data_to_pandas():
    MAX_AREA_TOL = .3
    df = []

    dataset = CoversDataset('./data/')
    for i in range(len(dataset)):
        _, target = dataset[i]
        image_path = dataset.images[i]
        date = get_file_path_date(image_path)

        newspaper_name = get_file_path_newspaper(image_path).lower()
        areas = target['area']

        # Some newspapers dont publish on holidays. Skip those
        if len(areas) == 0:
            continue

        labels = target['labels']

        benfica_areas = areas[labels == LabelClass.BENFICA.id]
        porto_areas = areas[labels == LabelClass.PORTO.id]
        sporting_areas = areas[labels == LabelClass.SPORTING.id]
        other_areas = areas[labels == LabelClass.OTHER.id]
        cover_total_area = target['image_width'] * target['image_height']

        max_area = np.max(target['area'])
        max_coverage_labels = tuple(
            np.unique(labels[np.isclose(areas,
                                        max_area,
                                        atol=0,
                                        rtol=MAX_AREA_TOL)]))

        df.append({
            'Date': dt.datetime.strptime(date, '%Y-%m-%d'),
            'Newspaper': newspaper_name,
            'Highlighted_Labels': max_coverage_labels,
        })

    df = pd.DataFrame(df)
    return df


def games_data_to_pandas():
    min_date = dt.datetime(year=2019, month=1, day=1)
    max_date = dt.datetime(year=2019, month=12, day=31)
    import csv
    df = []
    with open('./data/games_data.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for line_count, row in enumerate(csv_reader):
            date = dt.datetime.strptime(row['date'], '%Y-%m-%d')
            if date < min_date or date > max_date:
                continue
            df.append({
                'Date': date,
                'Home_Team': row['home_team'],
                'Away_Team': row['away_team'],
                'Home_Score': row['home_score'],
                'Away_Score': row['away_score']
            })

    df = pd.DataFrame(df)
    df = df.drop_duplicates()  # paranoid cleanup

    return df


def year_calendar_plot(covers_df):
    from matplotlib.patches import Patch
    fig, axes = plt.subplots(nrows=3,
                             ncols=1,
                             squeeze=False,
                             subplot_kw={},
                             gridspec_kw={})
    axes = axes.T[0]

    for newspaper_idx, newspaper_name in enumerate(Newspaper.names()):
        newspaper_df = filter_newspapers(covers_df, [newspaper_name.lower()])
        total_covers = len(newspaper_df)
        benfica_covers, porto_covers, sporting_covers, other_covers = produce_cover_counts(
            newspaper_df)
        newspaper_df = newspaper_df.set_index('Date')['Highlighted_Labels']
        ax = cyearplot(newspaper_df,
                       daylabels=PT_DAY_LABELS,
                       monthlabels=PT_MONTH_LABELS,
                       linewidth=2,
                       cmap=ListedColormap(Clubs.colors()),
                       ax=axes[newspaper_idx])
        ax.set_title(newspaper_name.capitalize())
        ax.legend(handles=[
            Patch(facecolor='r',
                  edgecolor='r',
                  label=f'Benfica {benfica_covers / total_covers:.1%}'),
            Patch(facecolor='b',
                  edgecolor='b',
                  label=f'Porto {porto_covers / total_covers:.1%}'),
            Patch(facecolor='green',
                  edgecolor='green',
                  label=f'Sporting {sporting_covers / total_covers:.1%}'),
            Patch(facecolor='gray',
                  edgecolor='gray',
                  label=f'Other {other_covers / total_covers:.1%}')
        ],
                  loc='lower center',
                  ncol=4,
                  bbox_to_anchor=(0.5, -.5))

        fig.set_figheight(10)
        fig.set_figwidth(10)
        plt.tight_layout()
        plt.savefig('./calendar_view.png', bbox_inches='tight')


def tidify_covers_df(df):
    def one_hot(labels, size):
        res = np.zeros(size)
        res[labels] += 1
        return res

    df = df.set_index('Date')[['Newspaper', 'Highlighted_Labels']]

    # Split labels into columns
    # - one hot encoding of labels
    df['Highlighted_Labels'] = df['Highlighted_Labels'].map(
        lambda x: one_hot(list(x), len(LabelClass))[Clubs.ids()])
    # - split vector to multiple cols
    df[['benfica', 'porto', 'sporting',
        'other']] = pd.DataFrame(df.Highlighted_Labels.values.tolist(),
                                 index=df.index)
    df = df.drop(columns=['Highlighted_Labels'])
    return df


def month_plot(data):
    import matplotlib.ticker as mtick

    data = tidify_covers_df(data)
    fig, axes = plt.subplots(nrows=1,
                             ncols=3,
                             squeeze=False,
                             subplot_kw={},
                             gridspec_kw={})
    axes = axes[0]

    for newspaper_idx, n in enumerate(Newspaper.names()):
        newspaper_name = n.lower()
        newspaper_df = filter_newspapers(data, [newspaper_name])
        agg_df = newspaper_df.groupby(
            newspaper_df.index.month)[['benfica', 'porto',
                                       'sporting']].agg(['mean'])

        agg_df = agg_df

        ax = axes[newspaper_idx]
        ax.set_prop_cycle(color=['red', 'blue', 'green'])
        ax.plot(agg_df[['benfica', 'porto', 'sporting']], 'o--', linewidth=2)
        ax.set_title(newspaper_name.capitalize())
        ax.set_xticks([i for i in range(1, 12 + 1)])
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0))
        ax.set_xticklabels(PT_MONTH_LABELS)
        if newspaper_idx == 0:
            ax.set_ylabel('Percentagem de capas com destaque')

        ybot, ytop = ax.set_ylim(0, 1)
        xleft, xright = ax.set_xlim(0.5, 12.5)
        aspect_ratio = 1.0
        ax.set_aspect(aspect=(xright - xleft) / (ytop - ybot) * aspect_ratio)

        ax.grid()
        # print(agg_df)

    fig.set_figheight(7)
    fig.set_figwidth(23)
    plt.savefig('./month_view.png', bbox_inches='tight')


def next_day_analysis(covers_df, games_df):
    covers_df = tidify_covers_df(covers_df)

    for newspaper in Newspaper.names():
        print('=======')
        newspaper = newspaper.lower()
        for club in ['Benfica', 'Porto', 'Sporting']:
            print(f'\nAnalysis {newspaper} - {club}')
            _next_day_analysis(covers_df, games_df, newspaper, club)


def _next_day_analysis(covers_df, games_df, newspaper, team):
    # Create a DF with the dates after a win or non win of the team
    # - extract wins and non wins
    win_games_df = filter_df_game_data_by_team_and_result(
        games_df, team, 'win')
    no_win_games_df = filter_df_game_data_by_team_and_result(
        games_df, team, 'non-win')

    # - compute the dates after events
    dates_after_win = win_games_df['Date'] + dt.timedelta(days=1)
    dates_after_no_win = no_win_games_df['Date'] + dt.timedelta(days=1)
    # - create df
    date_after_win_df = pd.DataFrame({
        'Date': dates_after_win,
        'after_win': 1
    }).set_index('Date')
    date_after_no_win_df = pd.DataFrame({
        'Date': dates_after_no_win,
        'after_no_win': 1
    }).set_index('Date')

    # Get the newspaper covers that highlighted the team
    # - filter newspaper
    covers_df = filter_newspapers(covers_df, [newspaper])
    # - filter only rows for covers where team is highlighted
    club_covers_df = covers_df[covers_df[team.lower()] == 1]

    highlighted_wins_df = club_covers_df.join(date_after_win_df, how='inner')
    highlighted_non_wins_df = club_covers_df.join(date_after_no_win_df,
                                                  how='inner')

    # Report results
    total_wins = len(dates_after_win)
    total_non_wins = len(dates_after_no_win)
    total_highlighted_wins = highlighted_wins_df['after_win'].sum()
    total_highlighted_non_wins = highlighted_non_wins_df['after_no_win'].sum()

    print(f'Number of wins: {total_wins}')
    print(f'Number of non_wins: {total_non_wins}')
    print(f'Pct highlighted wins: {total_highlighted_wins / total_wins:.0%}')
    print(
        f'Pct highlighted non wins: {total_highlighted_non_wins / total_non_wins:.0%}'
    )

    # Additional results for debug purposes:
    # - print the highlighted/not highlighted wins and non wins
    print(f'Highlighted wins: {highlighted_wins_df.index}')
    print(f'Highlighted non_wins: {highlighted_non_wins_df.index}')

    unhighlighted_wins_df = club_covers_df.join(date_after_win_df, how='right')
    unhighlighted_wins_df = unhighlighted_wins_df[
        unhighlighted_wins_df['Newspaper'].isna()]
    print(f'Unhighlighted wins: {unhighlighted_wins_df.index}')

    unhighlighted_non_wins_df = club_covers_df.join(date_after_no_win_df,
                                                    how='right')
    unhighlighted_non_wins_df = unhighlighted_non_wins_df[
        unhighlighted_non_wins_df['Newspaper'].isna()]
    print(f'Unhighlighted non_wins: {unhighlighted_non_wins_df.index}')


def main():
    try:
        covers_df = pd.read_pickle('./data/covers_df.pkl')
    except FileNotFoundError:
        covers_df = cover_data_to_pandas()
        pd.to_pickle(covers_df, './data/covers_df.pkl')

    try:
        games_df = pd.read_pickle('./data/games_df.pkl')
    except FileNotFoundError:
        games_df = games_data_to_pandas()
        pd.to_pickle(games_df, './data/games_df.pkl')

    print('Creating calendar plot')
    year_calendar_plot(covers_df)

    print('Creating month plot')
    month_plot(covers_df)

    print('Next day analysis')
    next_day_analysis(covers_df, games_df)


main()
