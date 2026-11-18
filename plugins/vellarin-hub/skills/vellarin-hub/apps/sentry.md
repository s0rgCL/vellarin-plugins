# Sentry through Vellarin Hub

Sentry exposes 210 actions. A sample of real action names (use `find_app_actions` for the rest):

**Reads (run at once)**
- Access project information
- Fetch alerts
- Fetch a monitor
- Fetch an alert
- Fetch an organization's monitors
- Fetch issue event by id
- Fetch organization alert rules
- Fetch organization release threshold statuses

**Writes (wait for the owner's approval, then run once)**
- Add a symbol source to a project
- Add organization member via email
- Add or remove user email by id
- Add team member in organization
- Add team to project
- Bulk mutate an organization's issues
- Bulk remove an organization's issues
- Create an alert for an organization

Page: https://hub.vellarin.ai/apps/sentry
