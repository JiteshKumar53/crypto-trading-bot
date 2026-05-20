# CAPSULE-002: Deployment Verification

**Purpose:** Ensure that "code built" equals "code deployed and running". Prevent the repeated mistake of building watchdogs/services but never starting them.

**Origin:** Evolution Event EV-20260520-002 (Watchdog built but never deployed — 3 failures)
**Severity:** CRITICAL
**Owner:** Operations Team (Jarvis)

---

## ENFORCEMENT RULES

### Rule 1: Deploy Before Declare (GENE-003)
- Code is NOT "fixed" until the process is running
- Manual test success ≠ production deployment
- Service file created ≠ service running

### Rule 2: Process Verification Required
- After any deployment, verify with `ps aux | grep <process_name>`
- After any deployment, check PID file exists
- After any deployment, verify process uptime > 0

### Rule 3: Health Check Verification
- After deployment, run health check within 60 seconds
- Health check must verify: process running, output generated, no errors
- If health check fails → deployment failed

### Rule 4: Output Verification
- After deployment, verify output file is created/updated
- For watchdog: verify report file exists and is recent (< 5 minutes)
- For daemon: verify log file shows activity

### Rule 5: No Assumption
- Never assume a service is running because it was configured
- Never assume a cron job is firing because it was added
- Never assume a process is healthy because it was started

---

## DEPLOYMENT CHECKLIST

```
DEPLOYMENT CHECKLIST (must complete all):
□ Code written
□ Code tested locally
□ Process started
□ PID verified (ps aux)
□ PID file written
□ Health check passed
□ Output file generated
□ Output verified correct
□ Auto-restart configured (if applicable)
□ Logging active
□ Alert on failure configured
□ CEO informed of deployment status
```

---

## VERIFICATION SCRIPT

```python
def verify_deployment(process_name: str, pid_file: Path, output_file: Path) -> DeploymentStatus:
    """Verify a service is actually deployed and running."""
    
    status = DeploymentStatus()
    
    # Check 1: Process running
    import subprocess
    result = subprocess.run(
        ["pgrep", "-f", process_name],
        capture_output=True
    )
    status.process_running = result.returncode == 0
    status.pid = result.stdout.decode().strip() if status.process_running else None
    
    # Check 2: PID file exists
    status.pid_file_exists = pid_file.exists()
    
    # Check 3: Output file recent
    if output_file.exists():
        mtime = output_file.stat().st_mtime
        age_seconds = time.time() - mtime
        status.output_recent = age_seconds < 300  # 5 minutes
    else:
        status.output_recent = False
    
    # Overall status
    status.deployed = all([
        status.process_running,
        status.pid_file_exists,
        status.output_recent
    ])
    
    return status
```

---

## TESTS REQUIRED

1. `test_deployment_verifies_process_running`
2. `test_deployment_fails_if_process_not_running`
3. `test_deployment_verifies_output_file`
4. `test_deployment_fails_if_output_stale`
5. `test_deployment_checklist_all_items_required`

---

## AUDIT TRAIL

- Creation: 2026-05-20 22:35 CEST
- Evolution Event: EV-20260520-002
- Genes: GENE-003
- Tests: tests/test_deployment_verification.py
