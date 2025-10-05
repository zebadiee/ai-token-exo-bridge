#!/usr/bin/env python3
"""
Advanced Self-Healing System with Model Fallback & Permission Management

PhD-level resilience features:
- Cloud endpoint health monitoring with remediation
- Intelligent model fallback on failures
- Permission error detection and guided recovery
- Automatic provider rotation with context preservation
- Event journaling for postmortem analysis
- Proactive healing before user-facing errors
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class FailureReason(Enum):
    """Categorized failure reasons"""
    AUTH_ERROR = "authentication_error"  # 401
    PERMISSION_ERROR = "permission_error"  # 403
    RATE_LIMIT = "rate_limit_exceeded"  # 429
    MODEL_NOT_FOUND = "model_not_found"  # 404
    QUOTA_EXCEEDED = "quota_exceeded"  # 402
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    INVALID_REQUEST = "invalid_request"  # 400
    SERVER_ERROR = "server_error"  # 500+
    UNKNOWN = "unknown"


@dataclass
class HealingAction:
    """Self-healing action taken"""
    action_type: str  # "retry", "fallback_model", "rotate_provider", "notify_user"
    target: str
    reason: FailureReason
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "action_type": self.action_type,
            "target": self.target,
            "reason": self.reason.value,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "details": self.details,
            "error": self.error
        }


@dataclass
class ProviderHealthRecord:
    """Health record for a provider"""
    provider_name: str
    healthy: bool
    last_check: datetime
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failure_reasons: Dict[FailureReason, int] = field(default_factory=dict)
    current_models: List[str] = field(default_factory=list)
    unavailable_models: List[str] = field(default_factory=list)
    permission_issues: List[str] = field(default_factory=list)
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def to_dict(self) -> Dict:
        return {
            "provider_name": self.provider_name,
            "healthy": self.healthy,
            "last_check": self.last_check.isoformat(),
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "success_rate": self.success_rate(),
            "total_requests": self.total_requests,
            "failure_reasons": {k.value: v for k, v in self.failure_reasons.items()},
            "current_models": self.current_models,
            "unavailable_models": self.unavailable_models,
            "permission_issues": self.permission_issues
        }


class AdvancedSelfHealingManager:
    """
    Advanced self-healing manager with intelligent fallback and recovery
    
    Features:
    - Categorized error detection and response
    - Model-level fallback strategies
    - Permission error guidance
    - Provider rotation with state preservation
    - Healing action journaling
    - Proactive health checks
    """
    
    def __init__(
        self,
        model_catalog=None,
        enable_auto_fallback: bool = True,
        enable_permission_guidance: bool = True,
        max_retry_attempts: int = 3
    ):
        """
        Initialize advanced self-healing manager
        
        Args:
            model_catalog: ModelCatalogSync instance
            enable_auto_fallback: Enable automatic model fallback
            enable_permission_guidance: Enable permission error guidance
            max_retry_attempts: Maximum retry attempts per provider
        """
        self.model_catalog = model_catalog
        self.enable_auto_fallback = enable_auto_fallback
        self.enable_permission_guidance = enable_permission_guidance
        self.max_retry_attempts = max_retry_attempts
        
        # Health tracking
        self.provider_health: Dict[str, ProviderHealthRecord] = {}
        
        # Healing journal
        self.healing_journal: List[HealingAction] = []
        self.max_journal_size = 1000
        
        # Threading
        self._running = False
        self._health_check_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_healing_action: List[Callable] = []
        self.on_permission_error: List[Callable] = []
        
        logger.info("Advanced self-healing manager initialized")
    
    def classify_error(
        self,
        status_code: int = None,
        error_message: str = None,
        response_data: Dict = None
    ) -> FailureReason:
        """
        Classify error into actionable category
        
        Args:
            status_code: HTTP status code
            error_message: Error message
            response_data: Response data
            
        Returns:
            FailureReason enum
        """
        # HTTP status code classification
        if status_code:
            if status_code == 401:
                return FailureReason.AUTH_ERROR
            elif status_code == 403:
                return FailureReason.PERMISSION_ERROR
            elif status_code == 404:
                return FailureReason.MODEL_NOT_FOUND
            elif status_code == 429:
                return FailureReason.RATE_LIMIT
            elif status_code == 402:
                return FailureReason.QUOTA_EXCEEDED
            elif status_code >= 500:
                return FailureReason.SERVER_ERROR
            elif status_code == 400:
                return FailureReason.INVALID_REQUEST
        
        # Message-based classification
        if error_message:
            msg_lower = error_message.lower()
            
            if "timeout" in msg_lower:
                return FailureReason.TIMEOUT
            elif "connection" in msg_lower:
                return FailureReason.CONNECTION_ERROR
            elif "permission" in msg_lower or "forbidden" in msg_lower:
                return FailureReason.PERMISSION_ERROR
            elif "rate limit" in msg_lower or "too many requests" in msg_lower:
                return FailureReason.RATE_LIMIT
            elif "quota" in msg_lower or "exceeded" in msg_lower:
                return FailureReason.QUOTA_EXCEEDED
            elif "not found" in msg_lower or "does not exist" in msg_lower:
                return FailureReason.MODEL_NOT_FOUND
            elif "unauthorized" in msg_lower or "invalid" in msg_lower:
                return FailureReason.AUTH_ERROR
        
        return FailureReason.UNKNOWN
    
    def handle_provider_failure(
        self,
        provider_name: str,
        model_id: str,
        failure_reason: FailureReason,
        error_details: str = None
    ) -> Tuple[Optional[str], Optional[str], List[HealingAction]]:
        """
        Handle provider failure with intelligent recovery
        
        Args:
            provider_name: Name of failed provider
            model_id: Model that was attempted
            failure_reason: Categorized failure reason
            error_details: Detailed error message
            
        Returns:
            Tuple of (alternative_provider, alternative_model, healing_actions)
        """
        healing_actions = []
        
        # Update health record
        self._record_failure(provider_name, failure_reason, model_id, error_details)
        
        # Strategy based on failure reason
        if failure_reason == FailureReason.MODEL_NOT_FOUND:
            # Try to find alternative model
            action, alt_provider, alt_model = self._handle_model_not_found(
                provider_name, model_id
            )
            healing_actions.append(action)
            
            if alt_model:
                return alt_provider, alt_model, healing_actions
        
        elif failure_reason == FailureReason.PERMISSION_ERROR:
            # Guide user to fix permissions
            action = self._handle_permission_error(provider_name, error_details)
            healing_actions.append(action)
            
            # Try alternative provider
            alt_provider = self._find_healthy_alternative_provider(provider_name)
            if alt_provider:
                action = HealingAction(
                    action_type="rotate_provider",
                    target=alt_provider,
                    reason=failure_reason,
                    success=True,
                    details={"from": provider_name, "to": alt_provider}
                )
                healing_actions.append(action)
                return alt_provider, model_id, healing_actions
        
        elif failure_reason in [FailureReason.RATE_LIMIT, FailureReason.QUOTA_EXCEEDED]:
            # Rotate to alternative provider immediately
            alt_provider = self._find_healthy_alternative_provider(provider_name)
            if alt_provider:
                action = HealingAction(
                    action_type="rotate_provider",
                    target=alt_provider,
                    reason=failure_reason,
                    success=True,
                    details={
                        "from": provider_name,
                        "to": alt_provider,
                        "reason": f"{failure_reason.value}"
                    }
                )
                healing_actions.append(action)
                return alt_provider, model_id, healing_actions
        
        elif failure_reason in [FailureReason.TIMEOUT, FailureReason.CONNECTION_ERROR]:
            # Retry with backoff, then rotate
            if self.provider_health[provider_name].consecutive_failures < self.max_retry_attempts:
                action = HealingAction(
                    action_type="retry_with_backoff",
                    target=provider_name,
                    reason=failure_reason,
                    details={"retry_count": self.provider_health[provider_name].consecutive_failures}
                )
                healing_actions.append(action)
                return provider_name, model_id, healing_actions
            else:
                # Max retries exceeded, rotate
                alt_provider = self._find_healthy_alternative_provider(provider_name)
                if alt_provider:
                    action = HealingAction(
                        action_type="rotate_provider",
                        target=alt_provider,
                        reason=failure_reason,
                        success=True,
                        details={"from": provider_name, "max_retries_exceeded": True}
                    )
                    healing_actions.append(action)
                    return alt_provider, model_id, healing_actions
        
        elif failure_reason == FailureReason.AUTH_ERROR:
            # Notify user to update API key
            action = HealingAction(
                action_type="notify_user",
                target=provider_name,
                reason=failure_reason,
                details={
                    "message": f"API key for {provider_name} is invalid. Please update in settings.",
                    "actionable": True,
                    "action_url": "/settings/api-keys"
                }
            )
            healing_actions.append(action)
        
        # Log all healing actions
        for action in healing_actions:
            self._journal_action(action)
        
        return None, None, healing_actions
    
    def _handle_model_not_found(
        self,
        provider_name: str,
        model_id: str
    ) -> Tuple[HealingAction, Optional[str], Optional[str]]:
        """Handle model not found error"""
        # Mark model as unavailable for this provider
        if provider_name in self.provider_health:
            if model_id not in self.provider_health[provider_name].unavailable_models:
                self.provider_health[provider_name].unavailable_models.append(model_id)
        
        # Find alternative model
        if self.model_catalog:
            alternatives = self.model_catalog.find_alternative_models(model_id, provider_name)
            
            if alternatives:
                alt_model = alternatives[0]
                action = HealingAction(
                    action_type="fallback_model",
                    target=alt_model.id,
                    reason=FailureReason.MODEL_NOT_FOUND,
                    success=True,
                    details={
                        "original_model": model_id,
                        "alternative_model": alt_model.id,
                        "provider": alt_model.provider,
                        "context_length": alt_model.context_length
                    }
                )
                return action, alt_model.provider, alt_model.id
        
        # No alternative found
        action = HealingAction(
            action_type="fallback_model",
            target=model_id,
            reason=FailureReason.MODEL_NOT_FOUND,
            success=False,
            error="No alternative model found"
        )
        return action, None, None
    
    def _handle_permission_error(
        self,
        provider_name: str,
        error_details: str = None
    ) -> HealingAction:
        """Handle permission error with user guidance"""
        # Parse permission requirements from error
        required_scopes = self._parse_permission_requirements(error_details)
        
        guidance = {
            "provider": provider_name,
            "message": f"Insufficient permissions for {provider_name}",
            "required_scopes": required_scopes,
            "fix_steps": [
                f"1. Go to {provider_name} dashboard",
                "2. Regenerate API token with required permissions",
                "3. Update token in HUD settings",
                "4. Reconnect to apply changes"
            ],
            "actionable": True
        }
        
        # Track permission issue
        if provider_name in self.provider_health:
            issue_str = f"{error_details[:100]}" if error_details else "Unknown permission issue"
            if issue_str not in self.provider_health[provider_name].permission_issues:
                self.provider_health[provider_name].permission_issues.append(issue_str)
        
        action = HealingAction(
            action_type="guide_permission_fix",
            target=provider_name,
            reason=FailureReason.PERMISSION_ERROR,
            details=guidance
        )
        
        # Trigger callback if registered
        for callback in self.on_permission_error:
            try:
                callback(provider_name, guidance)
            except Exception as e:
                logger.error(f"Permission error callback failed: {e}")
        
        return action
    
    def _parse_permission_requirements(self, error_details: str = None) -> List[str]:
        """Parse required permissions from error message"""
        if not error_details:
            return ["inference", "models:read"]
        
        scopes = []
        error_lower = error_details.lower()
        
        # Common permission patterns
        if "inference" in error_lower:
            scopes.append("inference")
        if "chat" in error_lower:
            scopes.append("chat.completions")
        if "model" in error_lower and "read" in error_lower:
            scopes.append("models:read")
        
        return scopes if scopes else ["inference", "models:read"]
    
    def _find_healthy_alternative_provider(
        self,
        current_provider: str
    ) -> Optional[str]:
        """Find a healthy alternative provider"""
        # Sort providers by health
        healthy_providers = [
            (name, record) for name, record in self.provider_health.items()
            if record.healthy and name != current_provider
        ]
        
        # Sort by success rate
        healthy_providers.sort(key=lambda x: x[1].success_rate(), reverse=True)
        
        if healthy_providers:
            return healthy_providers[0][0]
        
        return None
    
    def _record_failure(
        self,
        provider_name: str,
        failure_reason: FailureReason,
        model_id: str = None,
        error_details: str = None
    ):
        """Record provider failure"""
        if provider_name not in self.provider_health:
            self.provider_health[provider_name] = ProviderHealthRecord(
                provider_name=provider_name,
                healthy=True,
                last_check=datetime.now()
            )
        
        record = self.provider_health[provider_name]
        record.last_failure = datetime.now()
        record.last_check = datetime.now()
        record.consecutive_failures += 1
        record.consecutive_successes = 0
        record.total_requests += 1
        
        # Track failure reason
        if failure_reason not in record.failure_reasons:
            record.failure_reasons[failure_reason] = 0
        record.failure_reasons[failure_reason] += 1
        
        # Mark unhealthy if too many failures
        if record.consecutive_failures >= 3:
            record.healthy = False
    
    def record_success(
        self,
        provider_name: str,
        model_id: str = None
    ):
        """Record provider success"""
        if provider_name not in self.provider_health:
            self.provider_health[provider_name] = ProviderHealthRecord(
                provider_name=provider_name,
                healthy=True,
                last_check=datetime.now()
            )
        
        record = self.provider_health[provider_name]
        record.last_success = datetime.now()
        record.last_check = datetime.now()
        record.consecutive_successes += 1
        record.consecutive_failures = 0
        record.successful_requests += 1
        record.total_requests += 1
        record.healthy = True
        
        # Track model availability
        if model_id and model_id not in record.current_models:
            record.current_models.append(model_id)
    
    def _journal_action(self, action: HealingAction):
        """Add action to healing journal"""
        self.healing_journal.append(action)
        
        # Trim journal if too large
        if len(self.healing_journal) > self.max_journal_size:
            self.healing_journal = self.healing_journal[-self.max_journal_size:]
        
        # Trigger callbacks
        for callback in self.on_healing_action:
            try:
                callback(action)
            except Exception as e:
                logger.error(f"Healing action callback failed: {e}")
        
        logger.info(f"Healing action: {action.action_type} on {action.target} for {action.reason.value}")
    
    def get_healing_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of healing actions over time period"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_actions = [
            a for a in self.healing_journal
            if a.timestamp > cutoff
        ]
        
        # Categorize actions
        by_type = {}
        by_reason = {}
        successes = 0
        failures = 0
        
        for action in recent_actions:
            # By type
            if action.action_type not in by_type:
                by_type[action.action_type] = 0
            by_type[action.action_type] += 1
            
            # By reason
            reason_key = action.reason.value
            if reason_key not in by_reason:
                by_reason[reason_key] = 0
            by_reason[reason_key] += 1
            
            # Success/failure
            if action.success:
                successes += 1
            else:
                failures += 1
        
        return {
            "period_hours": hours,
            "total_actions": len(recent_actions),
            "successful_actions": successes,
            "failed_actions": failures,
            "by_action_type": by_type,
            "by_failure_reason": by_reason,
            "provider_health": {
                name: record.to_dict()
                for name, record in self.provider_health.items()
            }
        }
    
    def get_recent_actions(self, limit: int = 10) -> List[Dict]:
        """Get recent healing actions"""
        recent = self.healing_journal[-limit:]
        return [action.to_dict() for action in reversed(recent)]


# Singleton instance
_healing_manager = None

def get_healing_manager(model_catalog=None) -> AdvancedSelfHealingManager:
    """Get or create global healing manager instance"""
    global _healing_manager
    if _healing_manager is None:
        _healing_manager = AdvancedSelfHealingManager(model_catalog=model_catalog)
    return _healing_manager
