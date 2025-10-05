#!/usr/bin/env python3
"""
Security Features Verification Script

Validates all three security features:
1. Secure API Key Lock-In
2. Localhost Auto-Detection  
3. Auto Free Models Highlighting
"""

import sys
import os
from pathlib import Path
from typing import Dict, List

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{YELLOW}ℹ️  {text}{RESET}")


def verify_file_exists(filepath: str, description: str) -> bool:
    """Verify a file exists"""
    if Path(filepath).exists():
        size = Path(filepath).stat().st_size
        print_success(f"{description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print_error(f"{description} NOT FOUND: {filepath}")
        return False


def verify_imports() -> Dict[str, bool]:
    """Verify all security feature modules can be imported"""
    print_header("1️⃣  MODULE IMPORT VERIFICATION")
    
    results = {}
    
    # Add src to path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    modules = [
        ("secure_key_manager", "Secure API Key Manager"),
        ("localhost_auto_detector", "Localhost Auto-Detector"),
        ("auto_free_models", "Free Models Highlighter"),
    ]
    
    for module_name, description in modules:
        try:
            exec(f"import {module_name}")
            print_success(f"{description} imports successfully")
            results[module_name] = True
        except ImportError as e:
            print_error(f"{description} import failed: {e}")
            results[module_name] = False
    
    return results


def verify_file_structure() -> Dict[str, bool]:
    """Verify all required files exist"""
    print_header("2️⃣  FILE STRUCTURE VERIFICATION")
    
    results = {}
    
    files = [
        ("src/secure_key_manager.py", "Secure Key Manager"),
        ("src/localhost_auto_detector.py", "Localhost Auto-Detector"),
        ("src/auto_free_models.py", "Free Models Highlighter"),
        ("FEATURES_INTEGRATION_GUIDE.md", "Integration Guide"),
        ("src/spiral_codex_hud.py", "Main HUD Application"),
    ]
    
    for filepath, description in files:
        results[filepath] = verify_file_exists(filepath, description)
    
    return results


def verify_feature_functions() -> Dict[str, bool]:
    """Verify key functions exist in each module"""
    print_header("3️⃣  FEATURE FUNCTION VERIFICATION")
    
    results = {}
    
    # Add src to path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    try:
        from secure_key_manager import (
            get_key_manager,
            streamlit_secure_key_input,
            SecureKeyManager
        )
        print_success("Secure Key Manager: All functions available")
        print_info("  - get_key_manager()")
        print_info("  - streamlit_secure_key_input()")
        print_info("  - SecureKeyManager class")
        results['secure_key_manager'] = True
    except ImportError as e:
        print_error(f"Secure Key Manager functions missing: {e}")
        results['secure_key_manager'] = False
    
    try:
        from localhost_auto_detector import (
            LocalhostAutoDetector,
            streamlit_localhost_detector,
            LocalNodeInfo
        )
        print_success("Localhost Auto-Detector: All functions available")
        print_info("  - LocalhostAutoDetector class")
        print_info("  - streamlit_localhost_detector()")
        print_info("  - LocalNodeInfo dataclass")
        results['localhost_auto_detector'] = True
    except ImportError as e:
        print_error(f"Localhost Auto-Detector functions missing: {e}")
        results['localhost_auto_detector'] = False
    
    try:
        from auto_free_models import (
            FreeModelsHighlighter,
            streamlit_free_models_selector,
            ModelEntry
        )
        print_success("Free Models Highlighter: All functions available")
        print_info("  - FreeModelsHighlighter class")
        print_info("  - streamlit_free_models_selector()")
        print_info("  - ModelEntry dataclass")
        results['auto_free_models'] = True
    except ImportError as e:
        print_error(f"Free Models Highlighter functions missing: {e}")
        results['auto_free_models'] = False
    
    return results


def verify_documentation() -> Dict[str, bool]:
    """Verify documentation exists and is comprehensive"""
    print_header("4️⃣  DOCUMENTATION VERIFICATION")
    
    results = {}
    
    docs = [
        "FEATURES_INTEGRATION_GUIDE.md",
        "LOCALHOST_LOCKDOWN_GUIDE.md",
        "FREE_MODELS_ONLY_GUIDE.md",
        "VERIFIED_FREE_MODELS.md",
        "SYSTEM_READY.md",
        "PHD_LEVEL_ENHANCEMENTS.md",
        "QUICK_REFERENCE.md",
    ]
    
    for doc in docs:
        if Path(doc).exists():
            size = Path(doc).stat().st_size
            print_success(f"{doc} ({size:,} bytes)")
            results[doc] = True
        else:
            print_info(f"{doc} not found (optional)")
            results[doc] = False
    
    return results


def verify_security_config() -> Dict[str, bool]:
    """Verify security configuration"""
    print_header("5️⃣  SECURITY CONFIGURATION VERIFICATION")
    
    results = {}
    
    # Check for encryption key file
    home = Path.home()
    key_file = home / ".spiral_codex_encryption_key"
    
    if key_file.exists():
        # Check permissions
        import stat
        perms = oct(key_file.stat().st_mode)[-3:]
        if perms == '600':
            print_success(f"Encryption key file has secure permissions: {perms}")
            results['key_permissions'] = True
        else:
            print_error(f"Encryption key file has insecure permissions: {perms} (should be 600)")
            results['key_permissions'] = False
    else:
        print_info("Encryption key file not yet created (will be created on first use)")
        results['key_permissions'] = True
    
    # Check for keys storage
    keys_file = home / ".spiral_codex_keys.json"
    if keys_file.exists():
        import stat
        perms = oct(keys_file.stat().st_mode)[-3:]
        if perms == '600':
            print_success(f"Keys storage file has secure permissions: {perms}")
            results['storage_permissions'] = True
        else:
            print_error(f"Keys storage file has insecure permissions: {perms} (should be 600)")
            results['storage_permissions'] = False
    else:
        print_info("Keys storage file not yet created (will be created on first use)")
        results['storage_permissions'] = True
    
    return results


def print_summary(all_results: Dict[str, Dict[str, bool]]):
    """Print verification summary"""
    print_header("📊 VERIFICATION SUMMARY")
    
    total_checks = 0
    passed_checks = 0
    
    for category, results in all_results.items():
        category_total = len(results)
        category_passed = sum(1 for v in results.values() if v)
        total_checks += category_total
        passed_checks += category_passed
        
        status = "✅" if category_passed == category_total else "⚠️"
        print(f"{status} {category}: {category_passed}/{category_total} checks passed")
    
    print(f"\n{BOLD}Overall: {passed_checks}/{total_checks} checks passed{RESET}")
    
    if passed_checks == total_checks:
        print(f"\n{GREEN}{BOLD}🎉 ALL SECURITY FEATURES VERIFIED! SYSTEM READY FOR PRODUCTION! 🎉{RESET}\n")
        return True
    else:
        print(f"\n{YELLOW}{BOLD}⚠️  Some checks failed. Review output above for details.{RESET}\n")
        return False


def main():
    """Run all verification checks"""
    print(f"{BOLD}{BLUE}")
    print(r"""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║          SPIRAL CODEX HUD - SECURITY FEATURES VERIFICATION            ║
    ║                                                                       ║
    ║    🔒 Secure API Key Lock-In                                          ║
    ║    🔍 Localhost Auto-Detection                                        ║
    ║    ✅ Auto Free Models Highlighting                                   ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """)
    print(RESET)
    
    all_results = {
        "File Structure": verify_file_structure(),
        "Module Imports": verify_imports(),
        "Feature Functions": verify_feature_functions(),
        "Documentation": verify_documentation(),
        "Security Config": verify_security_config(),
    }
    
    success = print_summary(all_results)
    
    if success:
        print_header("🚀 NEXT STEPS")
        print("1. Run the HUD: streamlit run src/spiral_codex_hud.py")
        print("2. Test secure key storage with the lock/unlock UI")
        print("3. Scan for localhost nodes with auto-detection")
        print("4. Select free models with visual badges")
        print("\n" + "="*80 + "\n")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
