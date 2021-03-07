from tabulate import tabulate
from pypika import Query, Table, Field, Criterion, Order
from multiprocessing import Pool
import gitlab

from datetime import datetime, timedelta
from itertools import repeat
import sqlite3
import os
import webbrowser
import pytz
import csv

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--repos", action='append',
                    help="Repos to search: -r repo1 -r 'repo 2'. If blank searches all repos you are a member of.")
parser.add_argument("-s", "--search", action='append',
                    help="Strings to search for in the commit message: -s '#CODE' -s 'phrase'")
parser.add_argument("-a", "--author", action='append',
                    help="Authors to search: -s 'dennis' -a 'author2'")
parser.add_argument("-b", "--begin", help="Date to begin search. dd/mm/YY")
parser.add_argument("-e", "--end", help="Date to begin search. dd/mm/YY")
parser.add_argument(
    "-o", "--output", help="Format to output search (html/print/csv).", default="print")
parser.add_argument(
    "-q", "--query", help="Write your own query. -q 'select count(*) from commits'")
parser.add_argument("-u", "--update", help="Update the database to the most recent commits.",
                    default=False, action='store_true')
parser.add_argument("-d", "--drop", help="Drops the commits table.",
                    default=False, action='store_true')
args = parser.parse_args()

def get_new_commits(begin, project):
    """Function to get new commits from a project.

    Args:
        begin (datetime): date which specifies when to get commits from.
        project (gitlab project): project to get the commits from.

    Returns:
        List of tuples: [(project,commit)...]   
    """
    
    try:
        commits = []
        commits = project.commits.list(since=begin, per_page=-1)
        commits = [(project, commit) for commit in commits]
        num_commits = len(commits)
        if num_commits > 0:
            print(str(num_commits) + " new commits for project " + project.name)
    except:
        return []
    return commits


def setup_table(conn):
    """Setup tables for commits to be stored.
    """
    conn.execute('''CREATE TABLE IF NOT EXISTS COMMITS
         (ID                TEXT PRIMARY KEY   NOT NULL,
         PROJECT            TEXT    NOT NULL,
         AUTHOR             TEXT    NOT NULL,
         MESSAGE            TEXT    NOT NULL,
         LINK               TEXT    NOT NULL,
         DATE               TIMESTAMP  NOT NULL);''')
    conn.execute('''CREATE INDEX IF NOT EXISTS  project_index 
                        ON COMMITS(PROJECT);''')
    conn.execute('''CREATE INDEX IF NOT EXISTS  date_index 
                        ON COMMITS(DATE);''')
    conn.execute('''CREATE INDEX IF NOT EXISTS  author_index 
                        ON COMMITS(AUTHOR);''')


def refresh_table(conn):
    """Drop tables and setup tables again
    """
    conn.execute('''DROP TABLE IF EXISTS COMMITS''')
    setup_table(conn)


def get_most_recent_date(conn):
    """Get the date of the most recent commit from the datebase.

    Returns:
        String: Date and time of the most recent commit from the database
    """
    cursor = conn.execute(
        "SELECT PROJECT, MAX(DATE) FROM COMMITS GROUP BY PROJECT;")
    ret = dict()
    for row in cursor:
        ret[row[0]] = str(datetime.fromisoformat(row[1]) + timedelta(seconds=1))
    return ret


def print_row(row, desc):
    """Print a row of the database based on the colum headers into a table.

    Args:
        row: row of the database to be printed
        desc: contains the header of the row
    """
    entry = [[desc[i][0], row[i]] for i in range(len(row))]
    print(tabulate(entry, tablefmt='fancy_grid', colalign=("right",)))


def update_commits(conn,gl):
    """Update commits database with most recent commits.
    """
    print("Updating commits database:")
    projects = gl.projects.list(starred=True, lazy=True, all=True)
    pool = Pool()
    begins = get_most_recent_date(conn)
    test = [(begins[p.name],p) for p in projects]
    commits = [entry for sublist in pool.starmap(
        get_new_commits, test) for entry in sublist]
    pool.close()
    pool.join()

    for project, commit in commits:
        dt = datetime.fromisoformat(commit.committed_date)
        dt = dt.replace(tzinfo=pytz.utc) - dt.utcoffset()
        conn.execute("""INSERT OR REPLACE INTO COMMITS (ID, PROJECT, AUTHOR, MESSAGE, LINK, DATE)
                        VALUES(?,?,?,?,?,?)""", (commit.id, project.name, commit.author_name, commit.message, commit.web_url, dt,))
    conn.commit()
    print(str(len(commits)) + " new commits")

def output_print(cursor):
    """Output query result into std out.

    Args:
        cursor: output from a sql query execution.
    """
    for row in cursor:
        print_row(row, cursor.description)

def output_csv(cursor):
    """Output search results to html and open in browser.

    Args:
        cursor: output from a sql query execution.
    """
    with open('output.csv', 'w', newline='') as f:
        wr = csv.writer(f, quoting=csv.QUOTE_ALL)
        for row in cursor:
            wr.writerow(row)


def search_commits(conn, repos, search, author, begin, end):
    """Search commits currently in the database.

    Args:
        repos: List of repos to search in.
        search (List of Strings): List of strings to search the commit messages for.
        author (List of Strings): List of authors names to search for.
        begin (datetime): Datetime to begin the search from.
        end (datetime): Datetime to end the search at.
    """
    commit_table = Table('COMMITS')
    sql = commit_table.select(
        commit_table.PROJECT, commit_table.LINK,
        commit_table.AUTHOR, commit_table.MESSAGE,
        commit_table.DATE
    ).orderby(commit_table.DATE, order=Order.asc)

    if repos != None:
        sql = sql.where(commit_table.PROJECT.isin(repos))
    if search != None:
        sql = sql.where(Criterion.any(
            [commit_table.MESSAGE.like("%"+x+"%") for x in search]))
    if author != None:
        sql = sql.where(Criterion.any(
            [commit_table.AUTHOR.like("%"+x+"%") for x in author]))
    if begin != None:
        sql = sql.where(commit_table.DATE >= begin)
    if end != None:
        sql = sql.where(commit_table.DATE <= end)

    return conn.execute(sql.get_sql())

def run():
    conn = sqlite3.connect('commits.db')
    gl = gitlab.Gitlab(os.getenv('GITLAB_URL'),
                        private_token=os.getenv('GITLAB_API_TOKEN'))

    setup_table(conn)
    if args.begin != None:
        args.begin = datetime.strptime(
            args.begin, '%d/%m/%Y').strftime('%Y-%m-%d')
    if args.end != None:
        args.end = datetime.strptime(args.end, '%d/%m/%Y').strftime('%Y-%m-%d')

    if args.drop:
        if input("Are you sure you want to drop the commits table? [y/N] ").lower() == "y":
            refresh_table(conn)

    if args.update:
        update_commits(conn,gl)

    out = None
    if args.query != None:
        out = conn.execute(args.query)
        conn.commit()
    elif args.search != None:
        out = search_commits(conn, args.repos, args.search,
                              args.author, args.begin, args.end)
    if out != None:
        globals()["output_"+args.output](out)
    conn.close()
