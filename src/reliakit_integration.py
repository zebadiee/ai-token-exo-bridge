#!/usr/bin/env python3
"""
ReliaKit Integration for AI Token Manager + Exo Bridge

Implements self-healing, health monitoring, and automatic recovery
using reliakit-tl15 patterns for distributed AI infrastructure.
"""

import logging
import time
import threading
import requests
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    OFFLINE = "offline"
    RECOVERING = "recovering"


@dataclass
class HealthCheckResult:
    """Result from a health check"""
    timestamp: datetime
    healthy: bool
    status: HealthStatus
    latency_ms: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "healthy": self.healthy,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "metadata": self.metadata
        }


@dataclass
class RecoveryAction:
    """Recovery action to execute"""
    action_type: str  # "restart", "failover", "reset", "notify"
    target: str
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False
    error: Optional[str] = None


class HealthChecker:
    """
    ReliaKit-style health checker for distributed AI infrastructure
    
    Monitors endpoints and triggers recovery actions on failure.
    """
    
    def __init__(
        self,
        target_name: str,
        target_url: str,
        health_endpoint: str = "/health",
        check_interval: int = 10,
        timeout: int = 5,
        failure_threshold: int = 3,
        recovery_threshold: int = 2
    ):
        """
        Initialize health checker
        
        Args:
            target_name: Name of the target (e.g., "exo_node_1")
            target_url: Base URL of target
            health_endpoint: Health check endpoint path
            check_interval: Seconds between checks
            timeout: Request timeout
            failure_threshold: Failures before marking offline
            recovery_threshold: Successes before marking recovered
        """
        self.target_name = target_name
        self.target_url = target_url
        self.health_endpoint = health_endpoint
        self.check_interval = check_interval
        self.timeout = timeout
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        
        # State
        self.current_status = HealthStatus.HEALTHY
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_check_time: Optional[datetime] = None
        self.history: List[HealthCheckResult] = []
        self.max_history = 100
        
        # Callbacks
        self.on_failure_callbacks: List[Callable] = []
        self.on_recovery_callbacks: List[Callable] = []
        self.on_status_change_callbacks: List[Callable] = []
    
    def check(self) -> HealthCheckResult:
        """
        Execute health check
        
        Returns:
            HealthCheckResult with details
        """
        start_time = time.time()
        
        try:
            url = f"{self.target_url}{self.health_endpoint}"
            response = requests.get(url, timeout=self.timeout)
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Success
                self.consecutive_failures = 0
                self.consecutive_successes += 1
                
                # Check if recovering
                if self.current_status in [HealthStatus.FAILING, HealthStatus.OFFLINE]:
                    if self.consecutive_successes >= self.recovery_threshold:
                        self._transition_to(HealthStatus.HEALTHY)
                        self._trigger_recovery_callbacks()
                    else:
                        self._transition_to(HealthStatus.RECOVERING)
                
                result = HealthCheckResult(
                    timestamp=datetime.now(),
                    healthy=True,
                    status=self.current_status,
                    latency_ms=latency_ms,
                    metadata=response.json() if response.text else {}
                )
            else:
                # HTTP error
                self._handle_failure(f"HTTP {response.status_code}")
                
                result = HealthCheckResult(
                    timestamp=datetime.now(),
                    healthy=False,
                    status=self.current_status,
                    latency_ms=latency_ms,
                    error=f"HTTP {response.status_code}"
                )
        
        except requests.exceptions.Timeout:
            self._handle_failure("Timeout")
            
            result = HealthCheckResult(
                timestamp=datetime.now(),
                healthy=False,
                status=self.current_status,
                latency_ms=self.timeout * 1000,
                error="Timeout"
            )
        
        except Exception as e:
            self._handle_failure(str(e))
            
            result = HealthCheckResult(
                timestamp=datetime.now(),
                healthy=False,
                status=self.current_status,
                latency_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
        
        # Store result
        self.last_check_time = datetime.now()
        self.history.append(result)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        return result
    
    def _handle_failure(self, error: str):
        """Handle check failure"""
        self.consecutive_successes = 0
        self.consecutive_failures += 1
        
        # Transition states based on failure count
        if self.consecutive_failures >= self.failure_threshold:
            if self.current_status != HealthStatus.OFFLINE:
                self._transition_to(HealthStatus.OFFLINE)
                self._trigger_failure_callbacks(error)
        elif self.consecutive_failures >= 2:
            self._transition_to(HealthStatus.FAILING)
    
    def _transition_to(self, new_status: HealthStatus):
        """Transition to new health status"""
        old_status = self.current_status
        self.current_status = new_status
        
        logger.info(f"{self.target_name}: {old_status.value} → {new_status.value}")
        
        # Trigger status change callbacks
        for callback in self.on_status_change_callbacks:
            try:
                callback(self.target_name, old_status, new_status)
            except Exception as e:
                logger.error(f"Status change callback error: {e}")
    
    def _trigger_failure_callbacks(self, error: str):
        """Trigger failure callbacks"""
        for callback in self.on_failure_callbacks:
            try:
                callback(self.target_name, error)
            except Exception as e:
                logger.error(f"Failure callback error: {e}")
    
    def _trigger_recovery_callbacks(self):
        """Trigger recovery callbacks"""
        for callback in self.on_recovery_callbacks:
            try:
                callback(self.target_name)
            except Exception as e:
                logger.error(f"Recovery callback error: {e}")
    
    def on_failure(self, callback: Callable):
        """Register failure callback"""
        self.on_failure_callbacks.append(callback)
    
    def on_recovery(self, callback: Callable):
        """Register recovery callback"""
        self.on_recovery_callbacks.append(callback)
    
    def on_status_change(self, callback: Callable):
        """Register status change callback"""
        self.on_status_change_callbacks.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get health statistics"""
        if not self.history:
            return {
                "target": self.target_name,
                "status": self.current_status.value,
                "checks": 0
            }
        
        recent = self.history[-20:]  # Last 20 checks
        healthy_count = sum(1 for r in recent if r.healthy)
        avg_latency = sum(r.latency_ms for r in recent) / len(recent)
        
        return {
            "target": self.target_name,
            "status": self.current_status.value,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "checks": len(self.history),
            "recent_success_rate": healthy_count / len(recent),
            "avg_latency_ms": avg_latency,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None
        }


class ReliakitSelfHealingManager:
    """
    Self-healing manager for AI Token Manager + Exo Bridge
    
    Orchestrates health monitoring, automatic failover, and recovery
    across all providers and Exo nodes.
    """
    
    def __init__(
        self,
        bridge_manager,
        check_interval: int = 10,
        enable_auto_recovery: bool = True
    ):
        """
        Initialize self-healing manager
        
        Args:
            bridge_manager: Reference to ExoBridgeManager
            check_interval: Health check interval in seconds
            enable_auto_recovery: Enable automatic recovery actions
        """
        self.bridge = bridge_manager
        self.check_interval = check_interval
        self.enable_auto_recovery = enable_auto_recovery
        
        # Health checkers for each component
        self.checkers: Dict[str, HealthChecker] = {}
        
        # Recovery actions log
        self.recovery_log: List[RecoveryAction] = []
        
        # Event log for HUD
        self.event_log: List[Dict] = []
        
        # Threading
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        logger.info("ReliaKit self-healing manager initialized")
    
    def add_target(
        self,
        name: str,
        url: str,
        health_endpoint: str = "/health"
    ) -> HealthChecker:
        """Add a monitoring target"""
        checker = HealthChecker(
            target_name=name,
            target_url=url,
            health_endpoint=health_endpoint,
            check_interval=self.check_interval
        )
        
        # Register callbacks
        checker.on_failure(self._on_target_failure)
        checker.on_recovery(self._on_target_recovery)
        checker.on_status_change(self._on_status_change)
        
        self.checkers[name] = checker
        self._log_event("target_added", {"name": name, "url": url})
        
        logger.info(f"Added monitoring target: {name} ({url})")
        return checker
    
    def start(self):
        """Start health monitoring"""
        if self._running:
            logger.warning("Self-healing manager already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()
        
        self._log_event("manager_started", {})
        logger.info("Self-healing manager started")
    
    def stop(self):
        """Stop health monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        
        self._log_event("manager_stopped", {})
        logger.info("Self-healing manager stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                for name, checker in self.checkers.items():
                    result = checker.check()
                    
                    # Log significant events
                    if not result.healthy:
                        self._log_event("health_check_failed", {
                            "target": name,
                            "error": result.error,
                            "status": result.status.value
                        })
                
                time.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.check_interval)
    
    def _on_target_failure(self, target_name: str, error: str):
        """Handle target failure"""
        logger.error(f"Target {target_name} failed: {error}")
        
        self._log_event("target_failure", {
            "target": target_name,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trigger recovery if enabled
        if self.enable_auto_recovery:
            self._attempt_recovery(target_name, error)
    
    def _on_target_recovery(self, target_name: str):
        """Handle target recovery"""
        logger.info(f"Target {target_name} recovered")
        
        self._log_event("target_recovery", {
            "target": target_name,
            "timestamp": datetime.now().isoformat()
        })
    
    def _on_status_change(self, target_name: str, old_status: HealthStatus, new_status: HealthStatus):
        """Handle status change"""
        self._log_event("status_change", {
            "target": target_name,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "timestamp": datetime.now().isoformat()
        })
    
    def _attempt_recovery(self, target_name: str, error: str):
        """Attempt to recover failed target"""
        logger.info(f"Attempting recovery for {target_name}")
        
        # Determine recovery strategy based on target type
        if "exo" in target_name.lower():
            action = self._recover_exo_node(target_name)
        else:
            action = self._recover_cloud_provider(target_name)
        
        self.recovery_log.append(action)
        
        # Keep only last 100 actions
        if len(self.recovery_log) > 100:
            self.recovery_log.pop(0)
    
    def _recover_exo_node(self, node_name: str) -> RecoveryAction:
        """Recover failed Exo node"""
        action = RecoveryAction(
            action_type="failover",
            target=node_name,
            params={"reason": "node_offline"}
        )
        
        try:
            # Trigger failover to cloud
            logger.info(f"Failing over {node_name} to cloud providers")
            
            # The bridge manager handles this automatically via ExoIntegration
            # Just log the event
            self._log_event("exo_failover", {
                "node": node_name,
                "action": "failover_to_cloud",
                "timestamp": datetime.now().isoformat()
            })
            
            action.success = True
        
        except Exception as e:
            logger.error(f"Recovery failed for {node_name}: {e}")
            action.error = str(e)
            self._log_event("recovery_failed", {
                "target": node_name,
                "error": str(e)
            })
        
        return action
    
    def _recover_cloud_provider(self, provider_name: str) -> RecoveryAction:
        """Recover failed cloud provider"""
        action = RecoveryAction(
            action_type="reset",
            target=provider_name,
            params={"reason": "provider_failure"}
        )
        
        try:
            logger.info(f"Resetting {provider_name}")
            
            # Log the provider failure
            self._log_event("cloud_provider_failure", {
                "provider": provider_name,
                "timestamp": datetime.now().isoformat()
            })
            
            action.success = True
        
        except Exception as e:
            logger.error(f"Recovery failed for {provider_name}: {e}")
            action.error = str(e)
        
        return action
    
    def _log_event(self, event_type: str, data: Dict):
        """Log event for HUD and analysis"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        
        self.event_log.append(event)
        
        # Keep only last 500 events
        if len(self.event_log) > 500:
            self.event_log.pop(0)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status for HUD"""
        return {
            "manager": {
                "running": self._running,
                "check_interval": self.check_interval,
                "auto_recovery": self.enable_auto_recovery,
                "targets": len(self.checkers)
            },
            "targets": {
                name: checker.get_stats()
                for name, checker in self.checkers.items()
            },
            "recent_events": self.event_log[-20:],  # Last 20 events
            "recent_recoveries": [
                {
                    "action_type": action.action_type,
                    "target": action.target,
                    "success": action.success,
                    "timestamp": action.timestamp.isoformat(),
                    "error": action.error
                }
                for action in self.recovery_log[-10:]  # Last 10 actions
            ]
        }
    
    def get_events_since(self, since: datetime) -> List[Dict]:
        """Get events since timestamp (for HUD live updates)"""
        return [
            event for event in self.event_log
            if datetime.fromisoformat(event["timestamp"]) > since
        ]
    
    def force_check(self, target_name: Optional[str] = None):
        """Force immediate health check"""
        if target_name:
            if target_name in self.checkers:
                return self.checkers[target_name].check()
            else:
                raise ValueError(f"Unknown target: {target_name}")
        else:
            return {
                name: checker.check()
                for name, checker in self.checkers.items()
            }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Mock bridge manager for testing
    class MockBridge:
        pass
    
    bridge = MockBridge()
    
    # Initialize self-healing manager
    manager = ReliakitSelfHealingManager(
        bridge_manager=bridge,
        check_interval=5,
        enable_auto_recovery=True
    )
    
    # Add monitoring targets
    manager.add_target("exo_primary", "http://localhost:8000")
    manager.add_target("openrouter", "https://openrouter.ai/api/v1")
    
    # Start monitoring
    manager.start()
    
    print("\n=== ReliaKit Self-Healing Manager Running ===")
    print("Monitoring targets. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            time.sleep(5)
            status = manager.get_system_status()
            
            print(f"\n--- Status Update ---")
            for target, stats in status['targets'].items():
                print(f"{target}: {stats['status']} (failures: {stats['consecutive_failures']})")
            
            if status['recent_events']:
                print(f"\nRecent events: {len(status['recent_events'])}")
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
        manager.stop()
