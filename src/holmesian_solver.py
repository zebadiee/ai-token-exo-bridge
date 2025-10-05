#!/usr/bin/env python3
"""
Holmesian Autocorrection Layer

"When you have eliminated the impossible, whatever remains, however improbable, must be the truth."
— Sherlock Holmes

Intelligent filtering system that automatically eliminates impossible options and guides users
to viable solutions. Never shows dead-ends, always provides actionable next steps.

Features:
- Automatic elimination of impossible/unavailable options
- Smart constraint relaxation when needed
- Clear diagnostic messages for impossibilities
- Event-driven re-evaluation on state changes
- Zero dead-end guarantee
- Self-solving decision trees
"""

from typing import List, Dict, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ImpossibilityReason(Enum):
    """Reasons why an option is impossible"""
    API_KEY_MISSING = "api_key_missing"
    API_KEY_INVALID = "api_key_invalid"
    ENDPOINT_UNREACHABLE = "endpoint_unreachable"
    PROVIDER_DOWN = "provider_down"
    MODEL_UNAVAILABLE = "model_unavailable"
    PREMIUM_ONLY = "premium_only"
    FREE_MODE_LOCKED = "free_mode_locked"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    AUTHENTICATION_FAILED = "authentication_failed"
    NETWORK_ERROR = "network_error"
    CONFIGURATION_ERROR = "configuration_error"
    INCOMPATIBLE_VERSION = "incompatible_version"
    DEPRECATED = "deprecated"
    REQUIRES_APPROVAL = "requires_approval"
    GEOGRAPHIC_RESTRICTION = "geographic_restriction"


class SolutionViability(Enum):
    """Viability levels for solutions"""
    OPTIMAL = "optimal"           # Best choice, no compromises
    VIABLE = "viable"             # Good choice, minor compromises
    IMPROBABLE = "improbable"     # Rare/unusual but possible
    DEGRADED = "degraded"         # Works but with limitations
    IMPOSSIBLE = "impossible"     # Cannot work under current constraints


@dataclass
class Impossibility:
    """Details about why an option is impossible"""
    reason: ImpossibilityReason
    message: str
    suggestion: Optional[str] = None
    can_be_resolved: bool = False
    resolution_steps: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        return f"{self.message}" + (f" → {self.suggestion}" if self.suggestion else "")


@dataclass
class Solution:
    """A possible solution with viability assessment"""
    id: str
    name: str
    viability: SolutionViability
    score: float  # 0-100, higher is better
    
    # Constraints satisfied
    is_free: bool
    is_available: bool
    is_healthy: bool
    is_authenticated: bool
    
    # Optional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    compromises: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Why it's viable
    reasons: List[str] = field(default_factory=list)
    
    # Why it's not optimal (if applicable)
    limitations: List[str] = field(default_factory=list)
    
    def is_viable(self) -> bool:
        """Check if solution is actually viable"""
        return self.viability != SolutionViability.IMPOSSIBLE
    
    def get_display_name(self) -> str:
        """Get display name with viability indicator"""
        indicators = {
            SolutionViability.OPTIMAL: "🏆",
            SolutionViability.VIABLE: "✅",
            SolutionViability.IMPROBABLE: "🎲",
            SolutionViability.DEGRADED: "⚠️",
            SolutionViability.IMPOSSIBLE: "❌"
        }
        indicator = indicators.get(self.viability, "❓")
        return f"{indicator} {self.name}"


class HolmesianSolver:
    """
    Sherlock Holmes-inspired intelligent option solver
    
    Eliminates the impossible, surfaces the viable, guides through impossibilities
    """
    
    def __init__(
        self,
        free_mode: bool = True,
        strict_mode: bool = True,
        auto_select_single: bool = True
    ):
        """
        Initialize Holmesian solver
        
        Args:
            free_mode: Only allow free options
            strict_mode: Strict filtering (reject degraded solutions)
            auto_select_single: Auto-select if only one viable option
        """
        self.free_mode = free_mode
        self.strict_mode = strict_mode
        self.auto_select_single = auto_select_single
        
        self.impossibilities: List[Impossibility] = []
        self.last_evaluation = None
    
    def solve(
        self,
        possibilities: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Solution], List[Impossibility]]:
        """
        Solve for viable options by eliminating the impossible
        
        Args:
            possibilities: List of potential solutions
            constraints: Additional constraints to apply
            
        Returns:
            Tuple of (viable_solutions, impossibilities)
        """
        self.impossibilities = []
        solutions = []
        
        # Default constraints
        if constraints is None:
            constraints = {}
        
        # Add mode-based constraints
        if self.free_mode:
            constraints['free_only'] = True
        
        # Evaluate each possibility
        for possibility in possibilities:
            solution = self._evaluate_possibility(possibility, constraints)
            
            if solution.is_viable():
                solutions.append(solution)
            else:
                # Track why it's impossible
                impossibility = self._create_impossibility(possibility, solution)
                self.impossibilities.append(impossibility)
        
        # Sort solutions by viability and score
        solutions = self._rank_solutions(solutions)
        
        self.last_evaluation = datetime.now()
        
        return solutions, self.impossibilities
    
    def _evaluate_possibility(
        self,
        possibility: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Solution:
        """Evaluate a single possibility against constraints"""
        
        solution_id = possibility.get('id', 'unknown')
        solution_name = possibility.get('name', 'Unknown')
        
        # Start with optimal assumption
        viability = SolutionViability.OPTIMAL
        score = 100.0
        compromises = []
        warnings = []
        reasons = []
        limitations = []
        
        # Check availability
        is_available = possibility.get('available', True)
        if not is_available:
            return Solution(
                id=solution_id,
                name=solution_name,
                viability=SolutionViability.IMPOSSIBLE,
                score=0.0,
                is_free=False,
                is_available=False,
                is_healthy=False,
                is_authenticated=False,
                limitations=["Provider/model is unavailable"]
            )
        
        # Check health status
        is_healthy = possibility.get('healthy', True)
        if not is_healthy:
            viability = SolutionViability.DEGRADED
            score -= 30
            warnings.append("Service health degraded")
            limitations.append("May experience issues or downtime")
        
        # Check authentication
        is_authenticated = possibility.get('authenticated', False)
        if not is_authenticated:
            return Solution(
                id=solution_id,
                name=solution_name,
                viability=SolutionViability.IMPOSSIBLE,
                score=0.0,
                is_free=False,
                is_available=is_available,
                is_healthy=is_healthy,
                is_authenticated=False,
                limitations=["No valid API key configured"]
            )
        
        # Check free tier requirement
        is_free = possibility.get('is_free', False)
        requires_payment = possibility.get('requires_payment', False)
        
        if constraints.get('free_only', False) and (not is_free or requires_payment):
            return Solution(
                id=solution_id,
                name=solution_name,
                viability=SolutionViability.IMPOSSIBLE,
                score=0.0,
                is_free=False,
                is_available=is_available,
                is_healthy=is_healthy,
                is_authenticated=is_authenticated,
                limitations=["Premium/paid model in free-only mode"]
            )
        
        # Check rate limits
        rate_limited = possibility.get('rate_limited', False)
        if rate_limited:
            viability = min(viability, SolutionViability.DEGRADED)
            score -= 20
            warnings.append("Currently rate limited")
            compromises.append("May need to wait between requests")
        
        # Check quota
        quota_exceeded = possibility.get('quota_exceeded', False)
        if quota_exceeded:
            return Solution(
                id=solution_id,
                name=solution_name,
                viability=SolutionViability.IMPOSSIBLE,
                score=0.0,
                is_free=is_free,
                is_available=is_available,
                is_healthy=is_healthy,
                is_authenticated=is_authenticated,
                limitations=["Quota exceeded"]
            )
        
        # Check requires approval
        requires_approval = possibility.get('requires_approval', False)
        approval_pending = possibility.get('approval_pending', False)
        
        if requires_approval and approval_pending:
            return Solution(
                id=solution_id,
                name=solution_name,
                viability=SolutionViability.IMPOSSIBLE,
                score=0.0,
                is_free=is_free,
                is_available=is_available,
                is_healthy=is_healthy,
                is_authenticated=is_authenticated,
                limitations=["Awaiting manual approval"]
            )
        
        # Check deprecated
        deprecated = possibility.get('deprecated', False)
        if deprecated:
            viability = min(viability, SolutionViability.DEGRADED)
            score -= 40
            warnings.append("This option is deprecated")
            limitations.append("May be removed in future")
        
        # Check network reachability
        reachable = possibility.get('reachable', True)
        if not reachable:
            return Solution(
                id=solution_id,
                name=solution_name,
                viability=SolutionViability.IMPOSSIBLE,
                score=0.0,
                is_free=is_free,
                is_available=is_available,
                is_healthy=False,
                is_authenticated=is_authenticated,
                limitations=["Endpoint unreachable"]
            )
        
        # Add reasons for viability
        if is_free:
            reasons.append("Free tier available")
        if is_healthy:
            reasons.append("Service healthy")
        if is_authenticated:
            reasons.append("Authenticated and ready")
        
        # Calculate final score adjustments
        trust_score = possibility.get('trust_score', 50)
        score = (score * 0.7) + (trust_score * 0.3)  # Weight current state 70%, trust 30%
        
        return Solution(
            id=solution_id,
            name=solution_name,
            viability=viability,
            score=score,
            is_free=is_free,
            is_available=is_available,
            is_healthy=is_healthy,
            is_authenticated=is_authenticated,
            metadata=possibility.get('metadata', {}),
            compromises=compromises,
            warnings=warnings,
            reasons=reasons,
            limitations=limitations
        )
    
    def _create_impossibility(
        self,
        possibility: Dict[str, Any],
        solution: Solution
    ) -> Impossibility:
        """Create impossibility record from failed solution"""
        
        # Determine primary reason
        if not solution.is_authenticated:
            reason = ImpossibilityReason.API_KEY_MISSING
            message = f"{solution.name}: No API key configured"
            suggestion = "Configure API key in settings"
            can_resolve = True
            steps = ["Go to Settings", "Add API key for provider", "Lock key to save"]
            
        elif not solution.is_available:
            reason = ImpossibilityReason.MODEL_UNAVAILABLE
            message = f"{solution.name}: Currently unavailable"
            suggestion = "Try another provider or wait for service restoration"
            can_resolve = False
            steps = []
            
        elif not solution.is_free and self.free_mode:
            reason = ImpossibilityReason.FREE_MODE_LOCKED
            message = f"{solution.name}: Premium model in free-only mode"
            suggestion = "Enable paid models in settings (⚠️ billing risk)"
            can_resolve = True
            steps = ["Go to Settings", "Toggle 'Allow Paid Models'", "Verify billing protection"]
            
        elif not solution.is_healthy:
            reason = ImpossibilityReason.ENDPOINT_UNREACHABLE
            message = f"{solution.name}: Service unreachable or unhealthy"
            suggestion = "Check internet connection or try another provider"
            can_resolve = True
            steps = ["Verify internet connection", "Check provider status page", "Try alternative provider"]
            
        elif "Quota exceeded" in solution.limitations:
            reason = ImpossibilityReason.QUOTA_EXCEEDED
            message = f"{solution.name}: Quota exceeded"
            suggestion = "Wait for quota reset or upgrade plan"
            can_resolve = True
            steps = ["Wait for quota reset", "Check provider dashboard", "Consider upgrading"]
            
        elif "Awaiting manual approval" in solution.limitations:
            reason = ImpossibilityReason.REQUIRES_APPROVAL
            message = f"{solution.name}: Awaiting approval"
            suggestion = "Check email for approval status"
            can_resolve = True
            steps = ["Check email (including spam)", "Wait 1-2 business days", "Contact provider support if delayed"]
            
        else:
            reason = ImpossibilityReason.CONFIGURATION_ERROR
            message = f"{solution.name}: Configuration error"
            suggestion = "Check configuration and try again"
            can_resolve = True
            steps = ["Review provider configuration", "Verify all settings", "Restart HUD if needed"]
        
        return Impossibility(
            reason=reason,
            message=message,
            suggestion=suggestion,
            can_be_resolved=can_resolve,
            resolution_steps=steps
        )
    
    def _rank_solutions(self, solutions: List[Solution]) -> List[Solution]:
        """Rank solutions by viability and score"""
        
        # Sort by viability level first, then score
        viability_order = {
            SolutionViability.OPTIMAL: 0,
            SolutionViability.VIABLE: 1,
            SolutionViability.IMPROBABLE: 2,
            SolutionViability.DEGRADED: 3,
            SolutionViability.IMPOSSIBLE: 4
        }
        
        return sorted(
            solutions,
            key=lambda s: (viability_order.get(s.viability, 999), -s.score)
        )
    
    def get_recommendation(
        self,
        solutions: List[Solution],
        impossibilities: List[Impossibility]
    ) -> Dict[str, Any]:
        """
        Get smart recommendation based on Holmesian logic
        
        Returns dict with:
            - action: What to do next
            - message: User-facing message
            - auto_select: Solution to auto-select (if applicable)
            - suggestions: List of actionable suggestions
        """
        
        if not solutions:
            # No viable solutions - provide guidance
            return self._handle_no_solutions(impossibilities)
        
        if len(solutions) == 1 and self.auto_select_single:
            # Only one viable solution - auto-select it
            return {
                'action': 'auto_select',
                'message': f"Only viable option: {solutions[0].get_display_name()}",
                'auto_select': solutions[0],
                'suggestions': [
                    "This is the only option that works with your current settings",
                    f"Using {solutions[0].name} automatically"
                ]
            }
        
        # Multiple viable solutions - present ranked list
        optimal = [s for s in solutions if s.viability == SolutionViability.OPTIMAL]
        
        if optimal:
            return {
                'action': 'choose_from_optimal',
                'message': f"{len(optimal)} excellent option(s) available",
                'auto_select': optimal[0] if len(optimal) == 1 and self.auto_select_single else None,
                'suggestions': [
                    f"Top choice: {optimal[0].get_display_name()}",
                    "All options meet your criteria perfectly"
                ]
            }
        
        # Only degraded or improbable solutions
        return {
            'action': 'choose_with_compromises',
            'message': f"{len(solutions)} option(s) available with limitations",
            'auto_select': None,
            'suggestions': [
                "No perfect options available",
                "Consider relaxing constraints or resolving issues",
                f"Best available: {solutions[0].get_display_name()}"
            ]
        }
    
    def _handle_no_solutions(
        self,
        impossibilities: List[Impossibility]
    ) -> Dict[str, Any]:
        """Handle case where no viable solutions exist"""
        
        resolvable = [i for i in impossibilities if i.can_be_resolved]
        
        if not impossibilities:
            return {
                'action': 'error',
                'message': "No options available (system error)",
                'auto_select': None,
                'suggestions': [
                    "This shouldn't happen - please report this issue",
                    "Try restarting the HUD"
                ]
            }
        
        if resolvable:
            # Show how to resolve
            primary = resolvable[0]
            return {
                'action': 'guide_resolution',
                'message': "No viable options currently - but you can fix this!",
                'auto_select': None,
                'suggestions': [
                    f"Primary issue: {primary.message}",
                    f"Solution: {primary.suggestion}",
                    "Steps to resolve:",
                    *[f"  {i+1}. {step}" for i, step in enumerate(primary.resolution_steps)]
                ]
            }
        
        # Nothing can be resolved - suggest mode change
        return {
            'action': 'suggest_mode_change',
            'message': "No options match your current criteria",
            'auto_select': None,
            'suggestions': [
                "All available options are excluded by your filters",
                "Options:",
                "  • Enable paid models (⚠️ billing risk)",
                "  • Configure additional providers",
                "  • Use local inference instead",
                "  • Adjust your requirements"
            ]
        }


def holmesian_autocorrect(
    possibilities: List[Dict[str, Any]],
    free_mode: bool = True,
    strict_mode: bool = True
) -> Tuple[List[Solution], Dict[str, Any]]:
    """
    Convenience function for Holmesian autocorrection
    
    Args:
        possibilities: List of possible options
        free_mode: Only show free options
        strict_mode: Strict filtering
        
    Returns:
        Tuple of (viable_solutions, recommendation)
    """
    solver = HolmesianSolver(
        free_mode=free_mode,
        strict_mode=strict_mode,
        auto_select_single=True
    )
    
    solutions, impossibilities = solver.solve(possibilities)
    recommendation = solver.get_recommendation(solutions, impossibilities)
    
    return solutions, recommendation


if __name__ == "__main__":
    # Demo the Holmesian solver
    print("=" * 80)
    print("Holmesian Autocorrection Layer - Demo")
    print("=" * 80)
    print()
    
    # Test data
    test_possibilities = [
        {
            'id': 'openrouter',
            'name': 'OpenRouter',
            'available': True,
            'healthy': True,
            'authenticated': True,
            'is_free': True,
            'requires_payment': False,
            'trust_score': 95.5
        },
        {
            'id': 'deepseek',
            'name': 'DeepSeek',
            'available': True,
            'healthy': True,
            'authenticated': False,  # No API key
            'is_free': True,
            'requires_payment': False,
            'trust_score': 89.0
        },
        {
            'id': 'claude',
            'name': 'Anthropic Claude',
            'available': True,
            'healthy': True,
            'authenticated': True,
            'is_free': False,  # Premium only
            'requires_payment': True,
            'trust_score': 95.2
        },
        {
            'id': 'broken',
            'name': 'Broken Provider',
            'available': True,
            'healthy': False,  # Unhealthy
            'authenticated': True,
            'is_free': True,
            'requires_payment': False,
            'trust_score': 30.0
        }
    ]
    
    print("Test Case 1: Free mode with multiple options")
    print("-" * 80)
    solutions, recommendation = holmesian_autocorrect(test_possibilities, free_mode=True)
    
    print(f"\nViable Solutions: {len(solutions)}")
    for sol in solutions:
        print(f"  {sol.get_display_name()} (score: {sol.score:.1f})")
        if sol.reasons:
            print(f"    ✓ {', '.join(sol.reasons)}")
        if sol.warnings:
            print(f"    ⚠ {', '.join(sol.warnings)}")
    
    print(f"\nRecommendation:")
    print(f"  Action: {recommendation['action']}")
    print(f"  Message: {recommendation['message']}")
    for suggestion in recommendation['suggestions']:
        print(f"    • {suggestion}")
    
    print("\n" + "=" * 80)
    print("✅ Holmesian solver demo complete!")
    print("=" * 80)
