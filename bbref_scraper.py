# Webscraper I wrote for personal use to get data from baseball-reference.com
# Wrote functions to be general and account for inconsistencies in available data depending on year
# Started this to be able to teach myself webscraping basics and refamiliarize myself with html and css code

from bs4 import BeautifulSoup, Comment
import requests, pandas as pd, numpy as np


def getVotingTable(award_id, year):
    url = "https://www.baseball-reference.com/awards/awards_{}.shtml"
    url = url.format(year)
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'lxml')
    table_0 = soup.find('table', attrs={'id':award_id})
    if table_0:
        return table_0
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    table_1 = BeautifulSoup(''.join(comments), 'lxml').find('table', attrs={'id':award_id})
    return table_1


def yearCompatible(award_id, year):
    """
    Checks if award type is available for given year
    """
    if 'MVP' in award_id and year >= 1911:
        return award_id
    elif 'CY' in award_id:
        if year >= 1967:
            return award_id
        elif year >= 1956:
            return 'ML_CYA_voting'
        else:
            raise ValueError("No Cy Young data for given year")
    elif 'ROY' in award_id:
        if year >= 1949:
            return award_id
        elif year >= 1947:
            return 'ML_ROY_voting'
        else:
            raise ValueError("No ROY data for given year")
    raise ValueError("No data for given year")


def getAwardVoting(award_type, year):
    """
    Get Voting Results for MVP, Cy Young, and Rookie of the Year for each League
    AL MVP - almvp
    NL MVP - nlmvp
    AL Cy Young - alcy
    NL Cy Young - nlcy
    AL Rookie of the Year - alroy
    NL Rookie of the Year - nlroy
    Rookie of the Year - roy Only compatible if year is 1947 or 1948
    Cy Young - cy Only compatible from 1956 - 1966
    """
    code = {
        'almvp':'AL_MVP_voting',
        'nlmvp':'NL_MVP_voting',
        'alcy':'AL_CYA_voting',
        'nlcy':'NL_CYA_voting',
        'alroy':'AL_ROY_voting',
        'nlroy':'NL_ROY_voting'
    }
    try:
        table_id = code[award_type]
    except KeyError as err:
        print("""Must input valid award code
        AL MVP - almvp
        NL MVP - nlmvp
        AL Cy Young - alcy
        NL Cy Young - nlcy
        AL Rookie of the Year - alroy
        NL Rookie of the Year - nlroy""", err)

    table_id = yearCompatible(table_id, year)
    table = getVotingTable(table_id, year)
    data = []
    rows = table.find_all('tr')
    for tr in rows:
        th = tr.find_all('th', attrs={'class':'poptip'})
        if th:
            head = [r.text for r in th]
        rankings = tr.find('th', attrs={'scope':'row', 'data-stat':'rank'})
        rank = []
        if rankings:
            rank = [rankings.text]
        td = tr.find_all('td')
        for d in td:
            if d.has_attr('data-append-csv'):
                rank.extend([d['data-append-csv']])
            rank.extend([d.text])
        if rank:
            data.append(rank)
    player_index = head.index('Name')
    head.insert(player_index, 'Player ID')
    return pd.DataFrame(data, columns=head)


def mvpHist():
    """
    Returns history of MVP winners and statistics
    """
    url = "https://www.baseball-reference.com/awards/mvp.shtml"
    page = requests.get(url).text
    soup = BeautifulSoup(page, "lxml")
    table = soup.find('table', attrs={'id':'mvp'})
    mvp = []
    rows = table.find_all('tr')
    for tr in rows:
        if tr.has_attr('class') and 'spacer' in tr['class']:
            continue
        th = tr.find_all('th', attrs={'class':'poptip'})
        if th:
            head = [r.text for r in th]
        year = tr.find('th', attrs={'scope':'row', 'data-stat':'year_ID'})
        yr = []
        if year:
            yr = [year.text]
        td = tr.find_all('td')
        for d in td:
            if d.has_attr('data-append-csv'):
                yr.extend([d['data-append-csv']])
            yr.extend([d.text])
        if yr:
            mvp.append(yr)
    player_index = head.index('Name')
    head.insert(player_index, 'Player ID')
    mvp = pd.DataFrame(mvp, columns=head)
    return mvp.drop(columns=['Voting'])


def cyHist():
    """
    Returns history of Cy Young winners and statistics
    """
    url = "https://www.baseball-reference.com/awards/cya.shtml"
    page = requests.get(url).text
    soup = BeautifulSoup(page, "lxml")
    table = soup.find('table', attrs={'id':'cya'})
    cy = []
    rows = table.find_all('tr')
    for tr in rows:
        if tr.has_attr('class') and 'spacer' in tr['class']:
            continue
        th = tr.find_all('th', attrs={'class':'poptip'})
        if th:
            head = [r.text for r in th]
        year = tr.find('th', attrs={'scope':'row', 'data-stat':'year_ID'})
        yr = []
        if year:
            yr = [year.text]
        td = tr.find_all('td')
        for d in td:
            if d.has_attr('data-append-csv'):
                yr.extend([d['data-append-csv']])
            yr.extend([d.text])
        if yr:
            cy.append(yr)
    player_index = head.index('Name')
    head.insert(player_index, 'Player ID')
    cy = pd.DataFrame(cy, columns=head)
    return cy.drop(columns=['Voting'])


def getPlayerStats(player_id):
    """
    returns player career statistics
    """
    url = "https://www.baseball-reference.com/players/{}/{}.shtml"
    url = url.format(player_id[0], player_id)
    page = requests.get(url).text
    soup = BeautifulSoup(page, "lxml")
    table = soup.find('table', attrs={'class': 'stats_table'})
    stats = []
    for tr in table.find_all('tr'):
        if tr.has_attr('class') and ('spacer' in tr['class'] or 'minors_table' in tr['class']):
            continue
        if tr.find('th', attrs={'data-stat': 'player_stats_summary_explain'}):
            continue
        th = tr.find_all('th', attrs={'class': 'poptip'})
        if th:
            head = [r.text for r in th]
        year = tr.find('th', attrs={'scope': 'row', 'data-stat': 'year_ID'})
        yr = []
        if year:
            yr = [year.text]
        td = tr.find_all('td')
        yr.extend(d.text for d in td)
        if yr:
            stats.append(yr)
    return pd.DataFrame(stats, columns=head)


def getPlayerGameLog(player_id, year, stat_type=None):
    """
    Get Player's game log for given year
    :param player_id: Unique code for individual player
    :param year: Year to get stats from
    :param stat_type: 'b' or 'p' to indicate batting or pitching stats
    :return: game log
    """
    position = getPosition(player_id)
    if stat_type is None:
        stat_type = 'p' if 'Pitcher' in position else 'b'
    url = "https://www.baseball-reference.com/players/gl.fcgi?id={}&t={}&year={}"
    url = url.format(player_id, stat_type, year)
    page = requests.get(url).text
    soup = BeautifulSoup(page, "lxml")
    table = soup.find(isGameLogTable)
    good_table = table.find('tbody')
    thead = table.find('thead').find_all('th')
    head = [h.text for h in thead]
    gamelog = []
    for tr in good_table.find_all('tr'):
        if tr.has_attr('class') and 'spacer' in tr['class']:
            continue
        rank = tr.find('th', attrs={'scope': 'row', 'data-stat': 'ranker'})
        rk = []
        if rank:
            rk = [rank.text]
        td = tr.find_all('td')
        rk.extend(d.text for d in td)
        if rk:
            gamelog.append(rk)
    return pd.DataFrame(gamelog, columns=head)


def isGameLogTable(tag):
    return tag.name == "table" and tag.has_attr('id') and 'gamelogs' in tag['id']


def getPosition(player_id):
    url = "https://www.baseball-reference.com/players/{}/{}.shtml"
    url = url.format(player_id[0], player_id)
    page = requests.get(url).text
    soup = BeautifulSoup(page, "lxml")
    div = soup.find('div', attrs={'itemtype': "https://schema.org/Person"})
    p = div.find('p')
    return p.text


def getPlayerID(fname, lname):
    return (lname[:5] + fname[:2] + '01').lower()


def getCareerYears(player_id, game_limit=None):
    stats = getPlayerStats(player_id)
    if game_limit:
        stats = stats.loc[stats['G'] > game_limit]
    return np.asarray(stats['Year'].astype(int))


# def isStandardTable(tag):
#     return tag.has_attr('class') and tag.has_attr('id') and 'stats_table' in tag['class'] and 'standard' in tag['id'][0]
