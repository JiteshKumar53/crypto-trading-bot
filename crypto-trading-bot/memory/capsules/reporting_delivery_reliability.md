# CAPSULE-003: Reporting Delivery Reliability

**Purpose:** Ensure CEO reports are not just generated but actually delivered and accessible. Prevent the mistake of assuming file generation equals delivery.

**Origin:** Evolution Event EV-20260520-003 (Reports generated but not delivered)
**Severity:** HIGH
**Owner:** Reporting Team

---

## ENFORCEMENT RULES

### Rule 1: Generated ≠ Delivered (GENE-004)
- File saved to disk ≠ CEO can see it
- Report must be accessible via at least one channel
- If no channel works → delivery failed

### Rule 2: Delivery Status Tracking
- Every report must record delivery status:
  - `generated`: File created
  - `saved`: Written to disk
  - `delivered`: CEO acknowledged or channel confirmed
  - `failed`: No delivery path available

### Rule 3: Multi-Channel Fallback (GENE-005)
- Primary: Chat message (if session active)
- Secondary: Dashboard file (always accessible)
- Tertiary: Email (if configured)
- Quaternary: Telegram (if configured)
- If ALL fail → status is UNHEALTHY

### Rule 4: CEO Accessibility Check
- If chat is the only channel → CEO must be present
- If CEO is not in chat → delivery requires external channel
- If no external channels configured → delivery is degraded

### Rule 5: Delivery Confirmation
- If CEO receives report → they can acknowledge
- If no acknowledgment within 5 minutes of scheduled time → alert
- If 2 consecutive reports without acknowledgment → UNHEALTHY

---

## DELIVERY STATUS TRACKING

```python
@dataclass
class DeliveryStatus:
    timestamp: str
    report_type: str
    generated: bool = False
    saved_to_disk: bool = False
    chat_delivered: bool = False
    dashboard_updated: bool = False
    email_sent: bool = False
    telegram_sent: bool = False
    ceo_acknowledged: bool = False
    
    @property
    def fully_delivered(self) -> bool:
        return any([
            self.ceo_acknowledged,
            self.chat_delivered,
            (self.dashboard_updated and self.email_sent),
            (self.dashboard_updated and self.telegram_sent)
        ])
    
    @property
    def status(self) -> str:
        if self.ceo_acknowledged:
            return "delivered_confirmed"
        if self.fully_delivered:
            return "delivered_unconfirmed"
        if self.saved_to_disk:
            return "saved_only"
        if self.generated:
            return "generated_only"
        return "failed"
```

---

## MULTI-CHANNEL DELIVERY

```python
def deliver_report(report: str, channels: List[str]) -> DeliveryResult:
    """Deliver report through all available channels."""
    
    result = DeliveryResult()
    
    for channel in channels:
        try:
            if channel == "chat":
                # Requires active session
                result.chat_delivered = send_chat_message(report)
            elif channel == "dashboard":
                # Always works
                write_dashboard_file(report)
                result.dashboard_updated = True
            elif channel == "email":
                # Requires SMTP config
                result.email_sent = send_email_report(report)
            elif channel == "telegram":
                # Requires bot token
                result.telegram_sent = send_telegram_report(report)
        except Exception as e:
            logger.error(f"Delivery failed for {channel}: {e}")
    
    return result
```

---

## HEALTH STATUS

| Status | Condition |
|--------|-----------|
| HEALTHY | CEO acknowledged last 2 reports |
| DEGRADED | Report saved but no CEO acknowledgment |
| UNHEALTHY | 2+ consecutive reports without delivery confirmation |

---

## TESTS REQUIRED

1. `test_report_generated_not_equal_delivered`
2. `test_dashboard_file_always_accessible`
3. `test_chat_delivery_requires_active_session`
4. `test_delivery_status_tracks_all_channels`
5. `test_two_consecutive_undelivered_reports_unhealthy`
6. `test_ceo_acknowledgment_confirms_delivery`

---

## AUDIT TRAIL

- Creation: 2026-05-20 22:35 CEST
- Evolution Event: EV-20260520-003
- Genes: GENE-004, GENE-005
- Tests: tests/test_reporting_delivery_reliability.py
