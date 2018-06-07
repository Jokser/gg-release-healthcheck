# Gridgain release health checker
Script checks that all JIRA tickets targeted for specified version are located in corresponding specified branches.

Before run install necessary python libraries:
`pip install jira GitPython`

Specify your configuration at the top of .py file:
```
target_versions = ["gg-8.5.2", "2.5.2"]
projects = ["IGN", "GG", "WC"]
git_branches = ["ignite-2.5-master", "ignite-2.5.2"]
gridgain_remote_repo_name = "gg"
public_repo_path = "/home/gridgain/projects/incubator-ignite"
private_repo_path = "/home/gridgain/projects/ggprivate"
jira_url = "https://ggsystems.atlassian.net"
jira_login = "" # Type your email here
jira_password = "" # Type your password here
```
