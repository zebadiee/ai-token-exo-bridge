# 🛡️ ReliaKit Integration Guide

## Overview

This guide explains how the AI Token Manager + Exo Bridge integrates with **ReliaKit-TL15** self-healing patterns for automated health monitoring, failover, and recovery.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Spiral Codex HUD (Streamlit Dashboard)                    │
│  • Live monitoring                                          │
│  • Event visualization                                      │
│  • Manual controls                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  ReliakitSelfHealingManager                                 │
│  ├── HealthChecker (Exo Primary Node)                       │
│  ├── HealthChecker (Exo Node 2)                             │
│  ├── HealthChecker (OpenRouter)                             │
│  └── HealthChecker (HuggingFace)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────▼────────┐    ┌────────▼────────┐
│ Exo Cluster     │    │ Cloud Providers │
│ • Auto-failover │    │ • Backup        │
│ • Auto-recovery │    │ • Always-on     │
└─────────────────┘    └─────────────────┘
```

---

## Components

### 1. **HealthChecker** (`reliakit_integration.py`)

Monitors individual endpoints with:
- Configurable check intervals (default: 10s)
- Failure thresholds (3 failures = offline)
- Recovery thresholds (2 successes = recovered)
- State transitions: healthy → degraded → failing → offline → recovering → healthy
- Callback system for events

**Example:**
```python
from reliakit_integration import HealthChecker

checker = HealthChecker(
    target_name="exo_primary",
    target_url="http://localhost:8000",
    health_endpoint="/health",
    check_interval=10,
    failure_threshold=3
)

# Register callbacks
checker.on_failure(lambda name, error: print(f"{name} failed: {error}"))
checker.on_recovery(lambda name: print(f"{name} recovered!"))

# Run check
result = checker.check()
print(f"Status: {result.status.value}, Latency: {result.latency_ms}ms")
```

### 2. **ReliakitSelfHealingManager** (`reliakit_integration.py`)

Orchestrates health monitoring across all providers:
- Manages multiple HealthChecker instances
- Automatic failover on failures
- Recovery attempt logic
- Event logging for HUD
- Background monitoring thread

**Example:**
```python
from reliakit_integration import ReliakitSelfHealingManager
from bridge_manager import ExoBridgeManager

# Initialize
bridge = ExoBridgeManager()
manager = ReliakitSelfHealingManager(
    bridge_manager=bridge,
    check_interval=10,
    enable_auto_recovery=True
)

# Add targets
manager.add_target("exo_primary", "http://localhost:8000")
manager.add_target("exo_node_2", "http://192.168.1.100:8000")

# Start monitoring
manager.start()

# Get status anytime
status = manager.get_system_status()
print(f"Targets: {status['manager']['targets']}")
print(f"Recent events: {len(status['recent_events'])}")
```

### 3. **Enhanced Spiral Codex HUD** (`spiral_codex_hud.py`)

Integrated monitoring dashboard with:
- Real-time event stream
- Recovery action log
- Health metrics visualization
- Manual control panel
- Auto-refresh with live updates

---

## Features

### Automatic Health Monitoring

The ReliaKit manager continuously monitors all configured targets:

```python
# Runs in background thread every 10 seconds
for target in targets:
    result = target.check()
    if not result.healthy:
        log_event("health_check_failed", {...})
        if consecutive_failures >= threshold:
            trigger_failover()
```

### State Machine

Each target transitions through health states:

```
HEALTHY → DEGRADED → FAILING → OFFLINE
   ↑                              ↓
   └──── RECOVERING ←──────────────┘
```

- **HEALTHY**: All checks passing
- **DEGRADED**: 1 failure detected
- **FAILING**: 2+ failures, not yet offline
- **OFFLINE**: 3+ consecutive failures
- **RECOVERING**: Coming back online (1+ success after offline)

### Automatic Failover

When Exo nodes fail:

1. Health check fails
2. Consecutive failures increment
3. At threshold (3), node marked OFFLINE
4. Failover callback triggered
5. Bridge automatically routes to cloud providers
6. Event logged for HUD display

```python
def _on_target_failure(self, target_name: str, error: str):
    logger.error(f"Target {target_name} failed: {error}")
    
    # Log event
    self._log_event("target_failure", {...})
    
    # Trigger recovery
    if self.enable_auto_recovery:
        self._attempt_recovery(target_name, error)
```

### Auto-Recovery

When offline nodes come back:

1. Health check succeeds
2. State transitions to RECOVERING
3. After 2 consecutive successes, marked HEALTHY
4. Recovery callback triggered
5. Node automatically re-added to pool
6. Event logged

### Event Logging

All significant events are logged:
- Target added/removed
- Health check failures
- State transitions
- Failover actions
- Recovery attempts
- Manager start/stop

Events are stored with timestamps and metadata for HUD display and analysis.

---

## Usage

### Basic Setup

```python
from src.bridge_manager import ExoBridgeManager
from src.reliakit_integration import ReliakitSelfHealingManager

# Initialize bridge
bridge = ExoBridgeManager(
    exo_host="localhost",
    exo_port=8000
)
bridge.start()

# Initialize ReliaKit
reliakit = ReliakitSelfHealingManager(
    bridge_manager=bridge,
    check_interval=10,  # Check every 10 seconds
    enable_auto_recovery=True
)

# Add monitoring targets
reliakit.add_target("exo_primary", "http://localhost:8000")

# Start self-healing
reliakit.start()

# Get status
status = reliakit.get_system_status()
```

### With Spiral Codex HUD

```bash
# Launch HUD with ReliaKit enabled
./launch.sh

# Or manually
streamlit run src/spiral_codex_hud.py
```

In the HUD:
1. Connect to Exo cluster
2. Enable "ReliaKit Self-Healing" checkbox
3. View live events in the "ReliaKit Self-Healing Events" section
4. See automatic failover/recovery in real-time

### Custom Callbacks

```python
# Create custom failure handler
def on_node_failure(target_name, error):
    print(f"🔴 {target_name} failed: {error}")
    # Send alert, log to external system, etc.

def on_node_recovery(target_name):
    print(f"🟢 {target_name} recovered!")
    # Clear alerts, update dashboards, etc.

# Register callbacks
checker.on_failure(on_node_failure)
checker.on_recovery(on_node_recovery)
```

### Force Health Check

```python
# Force immediate check of all targets
results = reliakit.force_check()

# Or specific target
result = reliakit.force_check("exo_primary")
```

---

## HUD Features

### Live Event Stream

Shows real-time events with color coding:
- 🔴 Failures (red background)
- 🟢 Recoveries (green background)
- 🟡 Status changes (yellow background)
- 🔵 Info events (blue background)

### Recovery Actions Log

Table view of all recovery attempts:
- Timestamp
- Action type (failover, reset, notify)
- Target name
- Success/failure status
- Error details

### Health Metrics

Per-target metrics:
- Current status
- Success rate (last 20 checks)
- Average latency
- Consecutive failures/successes
- Total checks performed
- Last check timestamp

---

## Configuration

### Health Check Intervals

```python
# Fast monitoring (5 second intervals)
manager = ReliakitSelfHealingManager(
    bridge_manager=bridge,
    check_interval=5
)

# Slow monitoring (60 second intervals)
manager = ReliakitSelfHealingManager(
    bridge_manager=bridge,
    check_interval=60
)
```

### Failure Thresholds

```python
checker = HealthChecker(
    target_name="exo",
    target_url="http://localhost:8000",
    failure_threshold=5,  # 5 failures before offline
    recovery_threshold=3  # 3 successes to recover
)
```

### Disable Auto-Recovery

```python
# Manual control only
manager = ReliakitSelfHealingManager(
    bridge_manager=bridge,
    enable_auto_recovery=False  # No automatic actions
)
```

---

## Integration with Token Manager

The ReliaKit integration works seamlessly with your existing token manager:

1. **Exo as Priority 0**: ReliaKit monitors Exo nodes
2. **Automatic Failover**: On failure, routes to cloud providers
3. **Automatic Recovery**: When Exo recovers, resumes local inference
4. **Zero Code Changes**: Works with existing token manager setup

---

## Monitoring Best Practices

### 1. Set Appropriate Intervals

- **Production**: 10-30 second intervals
- **Development**: 5-10 second intervals
- **Resource-constrained**: 60+ second intervals

### 2. Configure Thresholds

- **Sensitive**: failure_threshold=2 (quick failover)
- **Balanced**: failure_threshold=3 (default)
- **Conservative**: failure_threshold=5 (avoid false positives)

### 3. Watch Event Log

Monitor for patterns:
- Frequent failures = unstable node
- Long recovery times = network issues
- Regular state transitions = threshold too sensitive

### 4. Use Manual Controls

- Force health checks before maintenance
- Disable auto-recovery for testing
- Clear event history periodically

---

## Troubleshooting

### High Failure Rate

```python
# Check recent stats
status = reliakit.get_system_status()
for target, stats in status['targets'].items():
    if stats['recent_success_rate'] < 0.8:  # < 80%
        print(f"⚠️ {target} is unstable")
```

### False Positives

If nodes are marked offline incorrectly:
- Increase `failure_threshold`
- Increase `timeout` in HealthChecker
- Check network latency

### Recovery Not Working

```python
# Check recovery threshold
# May need to decrease for faster recovery
checker = HealthChecker(
    ...,
    recovery_threshold=1  # Recover after 1 success
)
```

---

## Advanced

### Multiple Exo Nodes

```python
# Monitor entire cluster
manager.add_target("exo_node_1", "http://192.168.1.10:8000")
manager.add_target("exo_node_2", "http://192.168.1.11:8000")
manager.add_target("exo_node_3", "http://192.168.1.12:8000")

# Each node monitored independently
# Automatic load balancing across healthy nodes
```

### Custom Recovery Logic

```python
def custom_recovery(target_name, error):
    if "exo" in target_name:
        # Try restarting local process
        os.system("systemctl restart exo-node")
    else:
        # Reset cloud provider connection
        reset_provider(target_name)

manager._on_target_failure = custom_recovery
```

### Export Metrics

```python
# Get all events for external logging
events = manager.event_log

# Send to monitoring system
for event in events:
    send_to_prometheus(event)
    send_to_datadog(event)
```

---

## Summary

ReliaKit integration provides:
- ✅ Automatic health monitoring
- ✅ Intelligent failover
- ✅ Auto-recovery on node return
- ✅ Live event tracking
- ✅ Visual HUD dashboard
- ✅ Zero-modification to parent repos
- ✅ Production-ready reliability

**Result**: Self-healing AI infrastructure that automatically handles failures and recoveries without manual intervention.
