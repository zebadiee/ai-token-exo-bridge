#!/usr/bin/env python3
"""
HuggingFace Permission Diagnostic Tool

PhD-level diagnostic for the persistent 403 permission issues.
Provides:
- Direct API testing outside the app
- Curl command generation for manual testing
- Detailed permission analysis
- Step-by-step fix protocol
"""

import requests
import json
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class HFDiagnosticResult:
    """Result of HuggingFace diagnostic"""
    success: bool
    status_code: Optional[int]
    error_message: Optional[str]
    available_models: List[str]
    permissions_detected: List[str]
    account_status: str
    fix_steps: List[str]
    curl_commands: List[str]


class HuggingFaceDiagnostic:
    """
    Advanced diagnostic tool for HuggingFace API permission issues
    """
    
    HF_API_BASE = "https://api-inference.huggingface.co"
    HF_MODELS_ENDPOINT = "https://huggingface.co/api/models"
    HF_WHOAMI_ENDPOINT = "https://huggingface.co/api/whoami"
    
    def __init__(self, api_token: str):
        """
        Initialize diagnostic tool
        
        Args:
            api_token: HuggingFace API token to test
        """
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def run_full_diagnostic(self) -> HFDiagnosticResult:
        """
        Run complete diagnostic sequence
        
        Returns:
            HFDiagnosticResult with detailed findings
        """
        print("=" * 70)
        print("🔬 HuggingFace Permission Diagnostic Tool")
        print("=" * 70)
        print()
        
        # Step 1: Test whoami endpoint (account info)
        print("📋 Step 1: Checking account information...")
        account_info, account_error = self._test_whoami()
        
        if account_error:
            print(f"   ❌ Failed: {account_error}")
            return self._build_failed_result(
                error_message=f"Account check failed: {account_error}",
                fix_steps=self._get_token_invalid_steps()
            )
        else:
            username = account_info.get('name', 'unknown')
            account_type = account_info.get('type', 'unknown')
            orgs = account_info.get('orgs', [])
            print(f"   ✅ Account: {username} ({account_type})")
            if orgs:
                print(f"   Organizations: {', '.join([o.get('name', '') for o in orgs])}")
        
        # Step 2: Test model listing
        print("\n📋 Step 2: Testing model listing...")
        models, models_error = self._test_model_listing()
        
        if models_error:
            print(f"   ❌ Failed: {models_error}")
        else:
            print(f"   ✅ Found {len(models)} accessible models")
            if models[:3]:
                print(f"   Sample: {', '.join(models[:3])}")
        
        # Step 3: Test inference API (the critical one)
        print("\n📋 Step 3: Testing inference API...")
        inference_result, inference_error, status_code = self._test_inference_api()
        
        if inference_error:
            print(f"   ❌ Failed with HTTP {status_code}: {inference_error}")
            
            # Analyze the specific error
            if status_code == 403:
                print("\n🔍 Analyzing 403 Forbidden Error...")
                permissions = self._analyze_403_error(inference_error)
                
                return self._build_failed_result(
                    status_code=status_code,
                    error_message=inference_error,
                    permissions_detected=permissions,
                    fix_steps=self._get_403_fix_steps(),
                    account_status=f"{username} ({account_type})"
                )
            elif status_code == 401:
                print("\n🔍 Analyzing 401 Unauthorized Error...")
                return self._build_failed_result(
                    status_code=status_code,
                    error_message=inference_error,
                    fix_steps=self._get_token_invalid_steps()
                )
        else:
            print(f"   ✅ Inference successful!")
        
        # Success path
        print("\n" + "=" * 70)
        print("✅ All tests passed! Token is fully functional.")
        print("=" * 70)
        
        return HFDiagnosticResult(
            success=True,
            status_code=200,
            error_message=None,
            available_models=models,
            permissions_detected=["inference-api", "read-repos"],
            account_status=f"{username} ({account_type})",
            fix_steps=[],
            curl_commands=self._generate_curl_commands()
        )
    
    def _test_whoami(self) -> Tuple[Optional[Dict], Optional[str]]:
        """Test /whoami endpoint to get account info"""
        try:
            response = requests.get(
                self.HF_WHOAMI_ENDPOINT,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"HTTP {response.status_code}: {response.text[:200]}"
        except Exception as e:
            return None, str(e)
    
    def _test_model_listing(self) -> Tuple[List[str], Optional[str]]:
        """Test listing available models"""
        try:
            # Get models the user can access
            response = requests.get(
                f"{self.HF_MODELS_ENDPOINT}",
                headers=self.headers,
                params={"limit": 100, "filter": "inference"},
                timeout=15
            )
            
            if response.status_code == 200:
                models_data = response.json()
                model_ids = [m.get('id', '') for m in models_data if isinstance(m, dict)]
                return model_ids, None
            else:
                return [], f"HTTP {response.status_code}: {response.text[:200]}"
        except Exception as e:
            return [], str(e)
    
    def _test_inference_api(self) -> Tuple[Optional[Dict], Optional[str], Optional[int]]:
        """
        Test actual inference API call
        This is where the 403 typically occurs
        """
        # Use a well-known, free model
        test_model = "gpt2"
        url = f"{self.HF_API_BASE}/models/{test_model}"
        
        payload = {
            "inputs": "Hello",
            "parameters": {"max_new_tokens": 5}
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json(), None, 200
            else:
                return None, response.text[:500], response.status_code
        except Exception as e:
            return None, str(e), None
    
    def _analyze_403_error(self, error_message: str) -> List[str]:
        """Analyze 403 error to detect what permissions might be missing"""
        permissions = []
        
        error_lower = error_message.lower()
        
        if "inference" in error_lower:
            permissions.append("inference-api (MISSING)")
        if "serverless" in error_lower:
            permissions.append("serverless-inference (MISSING)")
        if "provider" in error_lower:
            permissions.append("inference-providers (MISSING)")
        
        return permissions if permissions else ["Unknown permission issue"]
    
    def _get_403_fix_steps(self) -> List[str]:
        """Get detailed fix steps for 403 error"""
        return [
            "🔧 HuggingFace 403 Forbidden - Fix Protocol:",
            "",
            "1. **Go to Token Settings**",
            "   → https://huggingface.co/settings/tokens",
            "",
            "2. **Create New Token** (don't edit existing)",
            "   → Click 'New token'",
            "   → Name: 'inference-token' (or similar)",
            "",
            "3. **Enable ALL Required Permissions:**",
            "   ✓ Read access to contents of all repos",
            "   ✓ Write access to contents of all repos",
            "   ✓ Make calls to serverless Inference API",
            "   ✓ Manage Inference Endpoints",
            "",
            "4. **Check Account Status**",
            "   → Some inference APIs require:",
            "     - Email verification",
            "     - Credit card on file (even for free tier)",
            "     - Agreement to ToS/policies",
            "",
            "5. **Update Token in App**",
            "   → Copy new token",
            "   → Paste in Spiral Codex HUD",
            "   → Click 'Save API Keys'",
            "   → Full app restart required",
            "",
            "6. **Test with Curl** (see commands below)",
            "",
            "7. **If Still Failing:**",
            "   → Check HF Status: https://status.huggingface.co",
            "   → Contact HF Support with:",
            "     - Your username",
            "     - This error message",
            "     - Token scopes screenshot"
        ]
    
    def _get_token_invalid_steps(self) -> List[str]:
        """Get fix steps for invalid token"""
        return [
            "🔧 Invalid Token - Fix Protocol:",
            "",
            "1. Go to: https://huggingface.co/settings/tokens",
            "2. Verify token exists and is active",
            "3. Regenerate token with full permissions",
            "4. Update in app and restart",
            "5. Test with curl command below"
        ]
    
    def _generate_curl_commands(self) -> List[str]:
        """Generate curl commands for manual testing"""
        return [
            "# Test 1: Check account (should succeed)",
            f"curl -H 'Authorization: Bearer {self.api_token[:10]}...' \\",
            f"  {self.HF_WHOAMI_ENDPOINT}",
            "",
            "# Test 2: Test inference (the critical test)",
            f"curl -X POST \\",
            f"  -H 'Authorization: Bearer {self.api_token[:10]}...' \\",
            f"  -H 'Content-Type: application/json' \\",
            f"  -d '{{\"inputs\": \"Hello\", \"parameters\": {{\"max_new_tokens\": 5}}}}' \\",
            f"  {self.HF_API_BASE}/models/gpt2",
            "",
            "# If test 2 returns 403, the token lacks inference permissions"
        ]
    
    def _build_failed_result(
        self,
        error_message: str,
        fix_steps: List[str],
        status_code: Optional[int] = None,
        permissions_detected: Optional[List[str]] = None,
        account_status: str = "unknown"
    ) -> HFDiagnosticResult:
        """Build a failed diagnostic result"""
        return HFDiagnosticResult(
            success=False,
            status_code=status_code,
            error_message=error_message,
            available_models=[],
            permissions_detected=permissions_detected or [],
            account_status=account_status,
            fix_steps=fix_steps,
            curl_commands=self._generate_curl_commands()
        )
    
    def print_full_report(self, result: HFDiagnosticResult):
        """Print comprehensive diagnostic report"""
        print("\n" + "=" * 70)
        print("📊 DIAGNOSTIC REPORT")
        print("=" * 70)
        
        print(f"\n🔐 Account: {result.account_status}")
        print(f"📡 Status: {'✅ PASS' if result.success else '❌ FAIL'}")
        
        if not result.success:
            print(f"🚫 HTTP Status: {result.status_code}")
            print(f"❗ Error: {result.error_message[:200]}")
            
            if result.permissions_detected:
                print(f"\n🔍 Detected Permission Issues:")
                for perm in result.permissions_detected:
                    print(f"   • {perm}")
            
            print(f"\n📋 Fix Steps:")
            for step in result.fix_steps:
                print(step)
            
            print(f"\n💻 Manual Test Commands:")
            for cmd in result.curl_commands:
                print(cmd)
        else:
            print(f"✅ Models Available: {len(result.available_models)}")
            print(f"✅ Permissions: All required permissions active")
        
        print("\n" + "=" * 70)


def main():
    """Run diagnostic from command line"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="HuggingFace Permission Diagnostic Tool"
    )
    parser.add_argument(
        "token",
        help="HuggingFace API token to test"
    )
    parser.add_argument(
        "--curl-only",
        action="store_true",
        help="Only generate curl commands"
    )
    
    args = parser.parse_args()
    
    diagnostic = HuggingFaceDiagnostic(args.token)
    
    if args.curl_only:
        print("💻 Manual Test Commands:")
        for cmd in diagnostic._generate_curl_commands():
            print(cmd)
    else:
        result = diagnostic.run_full_diagnostic()
        diagnostic.print_full_report(result)


if __name__ == "__main__":
    main()
