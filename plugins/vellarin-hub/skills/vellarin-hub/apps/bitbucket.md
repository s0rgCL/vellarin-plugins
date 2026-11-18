# Bitbucket through Vellarin Hub

Bitbucket exposes 116 actions. A sample of real action names (use `find_app_actions` for the rest):

**Reads (run at once)**
- Browse repository path
- Get branch
- Get Commit Build Status
- Get Commit Changes
- Get commit comment
- Get Commit Diff
- Get current user (v2)
- Get deployment environment variables

**Writes (wait for the owner's approval, then run once)**
- Approve Pull Request
- Create a branch
- Create an issue
- Create an issue comment
- Create a pull request
- Create pull request comment
- Create commit report annotations
- List commits from revision (POST)

Page: https://hub.vellarin.ai/apps/bitbucket
