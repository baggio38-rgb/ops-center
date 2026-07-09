# V6.4 Agent / Channel Split

- Added `features/agent_channel.py`.
- Moved agent/channel page render implementations out of `core/legacy.py`:
  - `render_channel_agent`
  - `render_new_member_analysis`
  - `render_agent_member_matrix`
  - `render_agent_market_monthly`
  - `render_game_venue`
- Updated `app_pages/agent_channel.py` to import from `features.agent_channel`.
- Shared helpers remain in `core/legacy.py` during the transition to avoid changing behavior.
