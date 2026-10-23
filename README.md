# RS Number Manager

Safe Telegram number-inventory manager.

## Environment variables
- BOT_TOKEN = 8878142336:AAEovrL0CQ1wTrwd21xukj2323DeTQlM3oQ
- ADMIN_IDS = comma-separated Telegram user IDs,8713122338

## Behavior
- Tapping COPY NUMBER only copies the displayed number.
- Clicking NEXT atomically reserves the next number.
- A reserved number is never shown again to any user while the process is running.
- Admins can upload a TXT file; one non-empty line = one number.
- This build does not implement OTP interception, temporary SMS activation, verification bypass, or OTP-provider aggregation.

## Important
The current storage is in RAM. A Render restart clears the list and used/reserved state.
For production persistence, use a database with an atomic claim operation.
