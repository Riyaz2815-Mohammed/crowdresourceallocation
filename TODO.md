# TODO: Improve Ranking Logic in Crowd Resource Allocation Tool

## Steps to Complete

- [ ] Add 'urgency' field (integer 1-10) to ResourceRequest model in app.py
- [ ] Update submit route in app.py to capture urgency input from form
- [ ] Modify ranking route in app.py to calculate composite score: score = (votes * 1) + (urgency * 0.5) + (waiting_days * 0.1), sort descending
- [ ] Update templates/submit.html to include urgency input field (select 1-10)
- [ ] Test the application to ensure ranking works as expected
