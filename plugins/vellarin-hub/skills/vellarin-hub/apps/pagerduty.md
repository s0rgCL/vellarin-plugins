# PagerDuty through Vellarin Hub

PagerDuty exposes 356 actions. A sample of real action names (use `find_app_actions` for the rest):

**Reads (run at once)**
- Aggregate escalation policy incident metrics
- Aggregate incident metrics with filters
- Audit escalation policy records
- Count paused incident reports
- Fetch cache variable for event orchestration
- Fetch custom incident field by id
- Fetch escalation polices list
- Fetch event orchestrations

**Writes (wait for the owner's approval, then run once)**
- Add service to incident workflow trigger
- Associate service dependencies
- Associate team with automation action
- Convert service rule by id
- Create a custom field for an incident type
- Create a field option for a custom field
- Create and manage custom incident fields
- Create an incident type

Page: https://hub.vellarin.ai/apps/pagerduty
