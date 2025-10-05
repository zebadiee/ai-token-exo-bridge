# 🔍 Holmesian Autocorrection Layer

**"When you have eliminated the impossible, whatever remains, however improbable, must be the truth."**  
— Sherlock Holmes

## Overview

The **Holmesian Autocorrection Layer** is an intelligent filtering and decision-support system that automatically eliminates impossible options and guides users to viable solutions. It provides a **zero dead-end guarantee**: users never see options they can't use, and always get clear guidance when no solutions exist.

---

## 🎯 Core Philosophy

### The Holmesian Principle
1. **Eliminate the Impossible** - Automatically filter out broken, unavailable, or incompatible options
2. **Surface the Viable** - Show only options that will actually work
3. **Guide Through Impossibility** - When no solutions exist, provide clear steps to resolve
4. **Never Show Dead Ends** - Always provide actionable next steps

### Zero Dead-End Guarantee
- Users never see "N/A" or empty lists without explanation
- Impossible options are hidden or clearly marked with resolution steps
- System always suggests next best action
- Auto-selects when only one viable option exists

---

## ✨ Key Features

### 1. **Intelligent Option Filtering**
- Automatically eliminates impossible options based on:
  - API key availability
  - Service health status
  - Free tier requirements
  - Network reachability
  - Rate limits and quotas
  - Authentication status
  - Deprecation status

### 2. **Viability Scoring**
Each option is scored on a 0-100 scale and classified:
- **🏆 Optimal** (85-100): Perfect choice, no compromises
- **✅ Viable** (70-84): Good choice, minor limitations
- **🎲 Improbable** (50-69): Rare/unusual but possible
- **⚠️ Degraded** (30-49): Works but with significant limitations
- **❌ Impossible** (0-29): Cannot work under current constraints

### 3. **Smart Recommendations**
Based on viable solutions, the system provides:
- **Auto-select**: Single viable option → automatically selected
- **Choose from optimal**: Multiple excellent options → user choice
- **Choose with compromises**: Only degraded options → show warnings
- **Guide resolution**: No viable options → step-by-step fix guide
- **Suggest mode change**: Constraints too strict → suggest relaxing

### 4. **Clear Diagnostics**
When options are impossible, the system explains:
- Why it's impossible (specific reason)
- Whether it can be resolved
- Step-by-step resolution instructions
- Alternative suggestions

---

## 💻 Implementation

### Core Components

#### Solution Class
```python
@dataclass
class Solution:
    id: str
    name: str
    viability: SolutionViability  # OPTIMAL, VIABLE, IMPROBABLE, DEGRADED, IMPOSSIBLE
    score: float  # 0-100
    
    is_free: bool
    is_available: bool
    is_healthy: bool
    is_authenticated: bool
    
    reasons: List[str]        # Why it works
    warnings: List[str]       # What to watch out for
    compromises: List[str]    # What you're giving up
    limitations: List[str]    # What doesn't work
```

#### Impossibility Class
```python
@dataclass
class Impossibility:
    reason: ImpossibilityReason
    message: str
    suggestion: Optional[str]
    can_be_resolved: bool
    resolution_steps: List[str]
```

#### Holmesian Solver
```python
solver = HolmesianSolver(
    free_mode=True,        # Only allow free options
    strict_mode=True,      # Reject degraded solutions
    auto_select_single=True  # Auto-select if only one option
)

solutions, impossibilities = solver.solve(possibilities, constraints)
recommendation = solver.get_recommendation(solutions, impossibilities)
```

---

## 🚀 Usage Examples

### Basic Usage
```python
from holmesian_solver import holmesian_autocorrect

possibilities = [
    {
        'id': 'provider1',
        'name': 'Provider 1',
        'available': True,
        'healthy': True,
        'authenticated': True,
        'is_free': True,
        'trust_score': 95.0
    },
    # ... more options
]

solutions, recommendation = holmesian_autocorrect(
    possibilities,
    free_mode=True
)

if recommendation['action'] == 'auto_select':
    selected = recommendation['auto_select']
    print(f"Auto-selected: {selected.name}")
elif recommendation['action'] == 'guide_resolution':
    print(f"No viable options: {recommendation['message']}")
    for step in recommendation['suggestions']:
        print(f"  • {step}")
```

### Streamlit Integration
```python
from holmesian_ui import streamlit_smart_provider_selector

providers = [...]  # List of provider dicts

selected_id = streamlit_smart_provider_selector(
    providers,
    free_mode=True
)

if selected_id:
    print(f"User selected: {selected_id}")
```

### Diagnostic View
```python
from holmesian_ui import streamlit_holmesian_diagnostic

# Show detailed diagnostic of why each option is/isn't viable
streamlit_holmesian_diagnostic(possibilities, free_mode=True)
```

---

## 📊 Evaluation Logic

### Viability Assessment

Each possibility is evaluated against constraints:

1. **Availability** - Is the service/model available?
   - ❌ If unavailable → IMPOSSIBLE

2. **Authentication** - Is API key configured and valid?
   - ❌ If not authenticated → IMPOSSIBLE

3. **Free Tier** - Does it have free tier (if required)?
   - ❌ If paid-only in free mode → IMPOSSIBLE

4. **Health Status** - Is service healthy?
   - ⚠️ If unhealthy → DEGRADED (score -30)

5. **Rate Limits** - Are we rate limited?
   - ⚠️ If rate limited → DEGRADED (score -20)

6. **Quota** - Have we exceeded quota?
   - ❌ If quota exceeded → IMPOSSIBLE

7. **Approval** - Does it require manual approval?
   - ❌ If pending approval → IMPOSSIBLE

8. **Deprecation** - Is it deprecated?
   - ⚠️ If deprecated → DEGRADED (score -40)

9. **Network** - Is it reachable?
   - ❌ If unreachable → IMPOSSIBLE

### Score Calculation
```python
score = 100.0

# Apply penalties
if unhealthy:
    score -= 30
if rate_limited:
    score -= 20
if deprecated:
    score -= 40

# Weight with trust score
final_score = (score * 0.7) + (trust_score * 0.3)
```

---

## 🎨 UI Behavior

### Scenario 1: Single Viable Option
```
✅ Only viable option: 🏆 OpenRouter
ℹ️ This is the only option that works with your current settings
ℹ️ Using OpenRouter automatically

[OpenRouter auto-selected]
```

### Scenario 2: Multiple Optimal Options
```
🏆 2 excellent option(s) available
• Top choice: 🏆 OpenRouter
• All options meet your criteria perfectly

[Dropdown with ranked options]
```

### Scenario 3: No Viable Options (Resolvable)
```
❌ No viable options currently - but you can fix this!

📋 How to Fix This
Primary issue: DeepSeek: No API key configured
Solution: Configure API key in settings

Steps to resolve:
  1. Go to Settings
  2. Add API key for provider
  3. Lock key to save
```

### Scenario 4: No Viable Options (Mode Change Needed)
```
❌ No options match your current criteria

💡 Suggested Actions
All available options are excluded by your filters

Your options:
  • Enable paid models (⚠️ billing risk)
  • Configure additional providers
  • Use local inference instead
  • Adjust your requirements
```

---

## 🔒 Impossibility Reasons

The system tracks specific impossibility reasons:

```python
class ImpossibilityReason(Enum):
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
```

Each reason has:
- Clear user-facing message
- Resolution suggestion
- Step-by-step fix guide (if resolvable)

---

## 🎯 Integration with Existing Systems

### With BYOK Provider Registry
```python
from byok_provider_registry import get_registry
from holmesian_solver import holmesian_autocorrect

registry = get_registry()
providers = registry.get_recommended_providers(free_only=True)

# Convert to possibilities format
possibilities = [
    {
        'id': p.provider_id,
        'name': p.provider_name,
        'available': p.api_stable,
        'healthy': not p.pricing_changed,
        'authenticated': False,  # Check from key manager
        'is_free': p.has_free_tier,
        'trust_score': p.get_trust_score()
    }
    for p in providers
]

solutions, recommendation = holmesian_autocorrect(possibilities)
```

### With Secure Key Manager
```python
from secure_key_manager import get_key_manager
from holmesian_solver import HolmesianSolver

km = get_key_manager()

# Enhance possibilities with auth status
for poss in possibilities:
    poss['authenticated'] = km.has_key(poss['name'])
    poss['api_key_valid'] = True  # Could validate here

solver = HolmesianSolver()
solutions, impossibilities = solver.solve(possibilities)
```

### With Free Models System
```python
from auto_free_models import FreeModelsHighlighter
from holmesian_solver import holmesian_autocorrect

highlighter = FreeModelsHighlighter()
free_models, paid_models = highlighter.fetch_and_categorize_models(...)

model_possibilities = [
    {
        'id': model.id,
        'name': model.name,
        'available': True,
        'healthy': True,
        'authenticated': True,
        'is_free': model.is_free,
        'trust_score': 80.0
    }
    for model in free_models
]

solutions, recommendation = holmesian_autocorrect(model_possibilities)
```

---

## 🧪 Testing

### Run Tests
```bash
# Test solver logic
python src/holmesian_solver.py

# Test UI components
streamlit run src/holmesian_ui.py
```

### Test Scenarios
1. **All options viable** - Should present ranked list
2. **Single option viable** - Should auto-select
3. **No options viable (resolvable)** - Should show fix steps
4. **No options viable (unresolvable)** - Should suggest mode change
5. **Mixed viability** - Should rank and show warnings

---

## 📈 Benefits

### For Users
- 🎯 **Never confused** - Only see options that work
- 🎯 **Never stuck** - Always get next steps
- 🎯 **Faster decisions** - Auto-select when obvious
- 🎯 **Clear understanding** - Know why options are/aren't available
- 🎯 **No dead ends** - Always have a path forward

### For Developers
- 🛠️ **Cleaner code** - Centralized filtering logic
- 🛠️ **Easier debugging** - Clear diagnostic views
- 🛠️ **Better UX** - Consistent user experience
- 🛠️ **Flexible constraints** - Easy to add new rules
- 🛠️ **Testable** - Clear inputs/outputs

### For System Reliability
- ⚡ **Self-healing** - Auto-excludes broken options
- ⚡ **Proactive** - Prevents errors before they happen
- ⚡ **Adaptive** - Responds to changing conditions
- ⚡ **Resilient** - Gracefully handles failures

---

## 🎓 Design Patterns

### The Rubik's Cube Principle
Like solving a Rubik's Cube, every state transition leaves only solvable configurations:
- No dead-end states
- Every move leads to solution or alternative
- Impossible states are prevented, not encountered

### Event-Driven Re-evaluation
When system state changes:
1. Re-filter possibilities
2. Re-calculate viability
3. Update UI automatically
4. Preserve user context

### Constraint Relaxation
If all constraints can't be satisfied:
1. Identify which constraints are strictest
2. Suggest relaxing least critical ones
3. Show trade-offs clearly
4. Let user decide

---

## 🚀 Future Enhancements

### Phase 1 (Current)
- ✅ Core solver logic
- ✅ Viability scoring
- ✅ Streamlit UI components
- ✅ Diagnostic views

### Phase 2 (Next)
- ML-powered viability prediction
- Historical success rate tracking
- User preference learning
- Context-aware suggestions

### Phase 3 (Future)
- Multi-criteria optimization
- Cost-benefit analysis
- Temporal viability (time-based constraints)
- Group decision support

---

## 📚 API Reference

### `holmesian_autocorrect(possibilities, free_mode, strict_mode)`
Convenience function for quick filtering.

**Returns:** `(solutions, recommendation)`

### `HolmesianSolver.solve(possibilities, constraints)`
Main solver method.

**Returns:** `(solutions, impossibilities)`

### `HolmesianSolver.get_recommendation(solutions, impossibilities)`
Generate user-facing recommendation.

**Returns:** `dict` with action, message, auto_select, suggestions

### `streamlit_holmesian_selector(...)`
Streamlit UI component for option selection.

**Returns:** Selected option ID or None

### `streamlit_holmesian_diagnostic(...)`
Diagnostic view showing full evaluation details.

---

## ✅ Summary

The Holmesian Autocorrection Layer provides:

✅ **Zero Dead-End Guarantee** - Never shows impossible options  
✅ **Intelligent Filtering** - Auto-eliminates broken/unavailable choices  
✅ **Smart Recommendations** - Guides users to best solutions  
✅ **Clear Diagnostics** - Explains why options are impossible  
✅ **Resolution Guidance** - Step-by-step fix instructions  
✅ **Auto-Selection** - Chooses obvious single solutions  
✅ **Graceful Degradation** - Handles "no solution" elegantly  

**"Elementary, my dear Watson." - Your users will always find a way forward.** 🔍✨
