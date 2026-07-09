# Coding Standard

## Python
- Pages should not contain complex SQL.
- Use `services/*_service.py` for data access.
- Use `components/` for reusable UI.
- Use `utils/formatter.py` for number/date formatting.

## SQL
- Dashboard pages read Aggregate tables first.
- Do not calculate core business metrics inside Streamlit.
- SQL files should be numbered by layer:
  - 001-099 Raw / Fact / Dim
  - 100-199 Dashboard Aggregates
  - 200-299 World Cup
  - 300-399 Member
  - 400-499 Risk
  - 500-599 Finance

## Versioning
- Feature work starts from `develop`.
- Stable releases merge into `main`.
- Tag stable releases like `v6.1.0`.
