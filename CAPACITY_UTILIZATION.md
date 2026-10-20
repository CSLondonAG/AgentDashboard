# Capacity-based utilization

The agent dashboard uses the same utilization rules as the department dashboard.

- An agent has two concurrent chat slots.
- One active chat uses 50% chat capacity; two use 100%.
- `Available_All` is email-assignable only while the agent has no active chat.
- `Available_Email_and_Web` is fully email-assignable.
- Email activity recorded during an active chat in `Available_All` is reported
  as excess demand and excluded from email utilization.
- Combined shift utilization uses capacity-adjusted chat load plus valid email
  load divided by the union of available presence time.

Work intervals are calculated at timestamp precision and clipped to the selected
date range. Overlapping chat intervals are preserved to measure concurrency.
