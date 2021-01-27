# Readme
Basic tool for searching commit messagse across multiple gitlab repositories.

To run the tool you must:
  * Install required packages from pipfile or requirements.txt
    * `pip install -r requirements.txt`
    * OR `pipenv install` if you are using pipenv
  * Setup os environment vars 
    * `GITLAB_URL` - Url to gitlab server
    * `GITLAB_API_TOKEN` - [Gitlab Personal Access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html). used to log into your account
