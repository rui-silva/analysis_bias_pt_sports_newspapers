import itertools
import datetime as dt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
import calendar


def cyearplot(data,
              year=None,
              vmin=None,
              vmax=None,
              cmap='Reds',
              fillcolor='whitesmoke',
              linewidth=1,
              linecolor='white',
              daylabels=calendar.day_abbr[:],
              dayticks=True,
              monthlabels=calendar.month_abbr[1:],
              monthticks=True,
              ax=None,
              **kwargs):
    """
    Extends ttresslar/calmap to plot (https://github.com/ttresslar/calmap)
    categorical year plots. Each date may be associated with multiple labels.
    The square associated with such dates is filled with multiple colors vertically.
    """

    if year is None:
        year = data.index.sort_values()[0].year

    # Min and max per day.
    if vmin is None:
        vmin = data.min()[0]
    if vmax is None:
        vmax = data.max()[0]

    if ax is None:
        ax = plt.gca()

    # Filter on year.
    by_day = data[str(year)]

    # Add missing days.
    dates_in_year = pd.date_range(start=str(year), end=str(year + 1),
                                  freq='D')[:-1]
    by_day = by_day.reindex(dates_in_year, fill_value=np.nan)

    # Create data frame we can pivot later.
    by_day = pd.DataFrame(
        dict({
            'day': by_day.index.dayofweek,
            'week': by_day.index.week,
            'data': by_day,
            'fill': 1
        }))

    # There may be some days assigned to previous year's last week or
    # next year's first week. We create new week numbers for them so
    # the ordering stays intact and week/day pairs unique.
    by_day.loc[(by_day.index.month == 1) & (by_day.week > 50), 'week'] = 0
    by_day.loc[(by_day.index.month == 12) & (by_day.week < 10), 'week'] \
        = by_day.week.max() + 1

    plot_data = by_day.pivot('day', 'week', 'data')

    label_combos = data.map(lambda x: len(x)).unique()
    lcm = np.lcm.reduce(label_combos)

    def expand_cols(x):
        if x is np.nan:
            x = (np.nan, )
        return list(
            itertools.chain.from_iterable(
                itertools.repeat(n, lcm // len(x)) for n in x))

    # First, expand the labels so that each cell has lcm columns.
    # Then reshape so that the rows correspond to the weekdays.
    # Finally, expand the labels so that each cell has lcm rows.
    plot_data = plot_data.applymap(expand_cols)
    plot_data = np.vstack(plot_data.values.tolist()).reshape(7, -1)
    plot_data = np.repeat(plot_data, lcm, axis=0)
    plot_data = np.ma.masked_where(np.isnan(plot_data), plot_data)

    # Compute the cells that dont need to be filled
    fill_data = np.array(by_day.pivot('day', 'week', 'fill').values)
    fill_data = np.repeat(np.repeat(fill_data, lcm, axis=0), lcm, axis=1)
    fill_data = np.ma.masked_where(np.isnan(fill_data), fill_data)

    ax.imshow(fill_data, vmin=0, vmax=1, cmap=ListedColormap([fillcolor]))
    ax.imshow(plot_data, vmin=vmin, vmax=vmax, cmap=cmap)

    # Get indices for monthlabels.
    if monthticks is True:
        monthticks = range(len(monthlabels))
    elif monthticks is False:
        monthticks = []
    elif isinstance(monthticks, int):
        monthticks = range(len(monthlabels))[monthticks // 2::monthticks]

    # Get indices for daylabels.
    if dayticks is True:
        dayticks = range(len(daylabels))
    elif dayticks is False:
        dayticks = []
    elif isinstance(dayticks, int):
        dayticks = range(len(daylabels))[dayticks // 2::dayticks]

    # Ticks for x/y axis labels
    ax.set_yticks(np.arange(lcm / 2 - .5, (6 + 1) * lcm, lcm))
    ax.set_yticklabels(daylabels)
    ax.set_xticks([
        by_day.ix[dt.date(year, i + 1, 15)].week * lcm - lcm / 2 - .5
        for i in monthticks
    ])
    ax.set_xticklabels([monthlabels[i] for i in monthticks], ha='center')

    # Ticks for the grid-like effect
    ax.set_yticks(np.arange(lcm - .5, (6 + 1) * lcm, lcm), minor=True)
    last_week = by_day['week'].max()
    ax.set_xticks(np.arange(lcm - .5, last_week * lcm, lcm), minor=True)
    ax.grid(which='minor', color=linecolor, linestyle='-', linewidth=linewidth)

    return ax
