🔴 CRITICAL: Auto-update system needs improvement!

The remote server downloaded the updates but didn't restart the application.

Current issue:
- Git repository updated to commit 659e257a ✅
- Application still running old version v3.1.1 ❌ 
- Need manual restart or improved auto-update system

Solution needed:
1. Auto-update system should restart the application after git pull
2. Or provide manual restart endpoint
3. Or implement rolling restart mechanism

Test this commit:
- Should update to v3.1.3
- Should show FORCED RESTART message in logs
- Should display restart warning in web interface
