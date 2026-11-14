# Supabase through Vellarin Hub

Supabase exposes 230 actions. A sample of real action names (use `find_app_actions` for the rest):

**Reads (run at once)**
- Get a third-party integration
- List third-party auth integrations for project
- Authorize user through OAuth
- Check vanity subdomain availability
- Beta get project's custom hostname config
- Retrieve network bans for project
- Get project network restrictions
- Get project pgsodium config

**Writes (wait for the owner's approval, then run once)**
- Accept Invite External Jit Access
- Create project api key
- Delete an API key from the project
- Delete third party auth config
- Update an API key for the project
- Append Resumable Upload
- Append Resumable Upload Signed
- Apply a database migration

Page: https://hub.vellarin.ai/apps/supabase
