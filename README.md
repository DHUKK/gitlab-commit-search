# Readme
Basic tool for searching commit messagse across multiple gitlab repositories.

## Getting started
  * Install required packages from pipfile or requirements.txt
    * `pip install -r requirements.txt`
    * OR `pipenv install` if you are using pipenv
  * Setup os environment vars 
    * `GITLAB_URL` - URL to Gitlab server
    * `GITLAB_API_TOKEN` - [Gitlab Personal Access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html). Used to log into your account
     
## Usage
```
usage: gitlab-commit-search.py [-h] [-r REPOS] [-s SEARCH] [-a AUTHOR] [-b BEGIN] [-e END] [-o OUTPUT] [-q QUERY] [-u] [-d]

optional arguments:
  -h, --help            show this help message and exit
  -r REPOS, --repos REPOS
                        Repos to search: -r repo1 -r 'repo 2'. If blank searches all repos you are a member of.
  -s SEARCH, --search SEARCH
                        Strings to search for in the commit message: -s '#CODE' -s 'phrase'
  -a AUTHOR, --author AUTHOR
                        Authors to search: -s 'dennis' -a 'author2'
  -b BEGIN, --begin BEGIN
                        Date to begin search. dd/mm/YY
  -e END, --end END     Date to begin search. dd/mm/YY
  -o OUTPUT, --output OUTPUT
                        Format to output search (html/print/csv).
  -q QUERY, --query QUERY
                        Write your own query. -q 'select count(*) from commits'
  -u, --update          Update the database to the most recent commits.
  -d, --drop            Drops the commits table.
  ```
