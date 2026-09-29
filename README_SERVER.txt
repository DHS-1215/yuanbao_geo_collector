Tencent Yuanbao GEO Collector - Windows Server Deployment

1. Extract yuanbao_geo_collector to:
   C:\yuanbao_geo_collector

2. Run:
   setup_server.bat

3. Wait until:
   SERVER SETUP SUCCESS

4. Run:
   run_yuanbao_geo_all.bat

5. On the first collection:
   - Chrome may open automatically.
   - Sign in to Tencent Yuanbao manually.
   - Complete any human verification manually.
   - Return to the terminal and continue.

6. If the current Yuanbao account quota is exhausted:
   - Keep the collection program running.
   - Open the Yuanbao Chrome window.
   - Sign out of the current account.
   - Sign in to another authorized account.
   - Confirm Yuanbao works normally.
   - Return to the terminal.
   - Enter R to retry the current task.

7. If you do not want to continue after quota exhaustion:
   - Enter Q.
   - The current Checkpoint will be preserved.
   - Run run_yuanbao_geo_all.bat again later.
   - Choose Resume last unfinished collection.
   - Previously successful tasks will be skipped.

8. When collection completes successfully:
   - The GEO package will be generated under output.
   - The final ZIP can be copied to the GEO Analysis System for import.

Do not copy browser profiles, cookies, account passwords,
or .env files from another computer.

The server is responsible only for collection and package generation.
It does not import data into the central GEO Analysis System.
