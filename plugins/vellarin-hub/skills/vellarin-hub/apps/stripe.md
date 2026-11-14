# Stripe through Vellarin Hub

Stripe exposes 428 actions. A sample of real action names (use `find_app_actions` for the rest):

**Reads (run at once)**
- Download File Contents
- Download Quote PDF
- Find a secret by name and scope
- Find tax association
- Retrieve Account
- List Account Capabilities
- Retrieve Account Capability
- Retrieve Person from Account

**Writes (wait for the owner's approval, then run once)**
- Accept quote
- Activate billing alert
- Add lines to invoice
- Advance test clock
- Apply customer balance to payment intent
- Archive billing alert
- Attach source to customer
- Attach payment to invoice

Page: https://hub.vellarin.ai/apps/stripe
