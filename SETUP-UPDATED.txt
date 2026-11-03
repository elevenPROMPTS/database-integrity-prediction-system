DATABASE INTEGRITY SYSTEM - UPDATED ADMIN EDIT FEATURE

IMPORTANT SECURITY NOTE
The uploaded project contained a database password directly in backend/database.py.
This updated copy removes that password. Change/rotate the old PostgreSQL password before using this project again.

1. Open Command Prompt.
2. Set your NEW PostgreSQL password in this terminal (do not share it in chat):

   set DB_PASSWORD=YOUR_NEW_POSTGRES_PASSWORD

Optional settings if your PostgreSQL connection differs from the defaults:
   set DB_HOST=127.0.0.1
   set DB_PORT=5432
   set DB_NAME=integrity_system
   set DB_USER=postgres

3. Start the backend:

   cd "C:\Users\YOUR_WINDOWS_USERNAME\database-integrity-system\backend"
   venv\Scripts\activate
   uvicorn main:app --reload

4. Open http://127.0.0.1:8000/
5. Sign in using your existing admin account.
6. In the Admin dashboard, choose a student, edit name/email/semester, then click Check & save changes.

WHAT THE NEW FEATURE DOES
- Requires a logged-in admin session for the admin student list and update endpoint.
- Only allows updating name, email, and semester through parameterized SQL.
- Runs the activity metrics through the existing Isolation Forest model before saving.
- If the model returns ANOMALY, the edit is not applied and a threat is logged.
- If the model returns NORMAL, the edit is committed and query activity is logged.
- The dashboard refreshes activity counts and recent threats automatically.

NOTES / LIMITATIONS
- The session token store is in memory and resets when the FastAPI server restarts. This is suitable for a local classroom prototype, not production authentication.
- Existing student pages and the legacy /log-activity demo endpoint are retained. The new admin edit route is protected by the session token.
- The Isolation Forest was trained on synthetic sample data. Its ANOMALY result is a prototype signal, not proof of an attack. Its thresholds may need calibration for your actual environment.
- This project still uses the existing users table's password column. For a public deployment, passwords must be securely hashed and authentication should use a production-grade session/token design.
