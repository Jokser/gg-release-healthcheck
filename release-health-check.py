from jira.client import JIRA
from git import Repo
import logging
import sys
import re

# Configuration parameters:
target_versions = ["gg-8.5.2", "2.5.2"]
projects = ["IGN", "GG", "WC"]
git_branches = ["ignite-2.5-master", "ignite-2.5.2"]
gridgain_remote_repo_name = "gg" # Type your git remote name for https://github.com/gridgain/apache-ignite repo
public_repo_path = "/home/gridgain/projects/incubator-ignite"
private_repo_path = "/home/gridgain/projects/ggprivate"
jira_url = "https://ggsystems.atlassian.net"
jira_login = "" # Type your email here
jira_password = "" # Type your password here

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Create logger
log = logging.getLogger("GIT-JIRA")

# Defines a function for connecting to Jira
def connect_jira(log, jira_server, jira_user, jira_password):
    '''
    Connect to JIRA. Return None on error
    '''
    try:
        log.info("Connecting to JIRA: %s" % jira_server)
        jira_options = {'server': jira_server}
        jira = JIRA(options=jira_options, basic_auth=(jira_user, jira_password))
                                        # ^--- Note the tuple
        return jira
    except Exception,e:
        log.error("Failed to connect to JIRA: %s" % e)
        return None

# Defines a function for extracting ticket name from Jira issue      
def extract_ticket_name(jira_issue):
  if jira_issue.key.startswith("IGN"):
    origin_ticket_search = re.search("\\[([a-zA-Z0-9-]+)\\](.*)", jira_issue.fields.summary.strip())
    if origin_ticket_search:
      return origin_ticket_search.group(1)
    else:
      log.warning("Failed to retreive origin IGNITE ticket for %s: %s" % (jira_issue.key, jira_issue.fields.summary))
      return "UNKNOWN"
  else:
    if "Backport" in jira_issue.fields.issuetype.name:
      backport_ticket_search = re.search("Backport ([a-zA-Z0-9-]+)(.*)", jira_issue.fields.summary.strip())
      if backport_ticket_search:
        return backport_ticket_search.group(1)
      else:
        log.warning("Failed to retrieve backport ticket name for %s: %s" % (jira_issue.key, jira_issue.fields.summary))
    return jira_issue.key

# Extract commits for specified branches from git repository
def extract_commits(repo_path, remote_prefix):
  log.info("Preparing %s" % repo_path)
  commits = {}
  repo = Repo(repo_path)
  for remote in repo.remotes:
    print remote
    remote.fetch()
  log.info("Fetched remotes %s" % repo_path)
  for branch in git_branches:
    branch_commits = list(repo.iter_commits(remote_prefix + branch, max_count=15000))
    commits[branch] = branch_commits
    log.info("Extracted %d commits from %s, branch: %s" % (len(branch_commits), repo_path, branch))
  return commits

# Prepare git repositories      
public_repo_commits = extract_commits(public_repo_path, gridgain_remote_repo_name + "/")
private_repo_commits = extract_commits(private_repo_path, "origin/")

# Create a connection object, jira
jira = connect_jira(log, jira_url, jira_login, jira_password)  
  
block_size = 100
block_num = 0

while True:
  start_idx = block_num*block_size
  issues = jira.search_issues("project in (%s) and status in (Resolved, Closed) and resolution in (Fixed, Done) and fixVersion in (%s)" % (', '.join(projects), ', '.join(target_versions)), start_idx, block_size)
  if len(issues) == 0:
      # Retrieve issues until there are no more to come
      break
  log.info("Retrieved issues: %d" % len(issues))
  block_num += 1
  
  # Check issues
  for issue in issues:
    ticket_name = extract_ticket_name(issue)
    missed_branches = []
    if ticket_name != "UNKNOWN":
      for branch in git_branches:
        commits = []
        if ticket_name.startswith("IGNITE"):
          commits = public_repo_commits[branch]
        else:
          commits = private_repo_commits[branch]

        contains = any(ticket_name.lower() in commit.message.lower() for commit in commits)
        if not contains:
          missed_branches.append(branch)
    
    if missed_branches:
      log.warning("%s: %s missed in %s. %s" % (issue.key, issue.fields.summary, str(missed_branches), issue.fields.assignee))
