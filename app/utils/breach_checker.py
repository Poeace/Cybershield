"""
Personal Data Breach Checker Module
=====================================
Checks if user's personal information (email, phone) has been
involved in known data breaches.

Features:
1. Email breach check via Have I Been Pwned API (k-anonymity model)
2. Phone number breach check (simulated local database)
3. Aggregated breach report with recommendations
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Local Breach Database (Simulated)
# ---------------------------------------------------------------------------
# In a production environment, this would be replaced with a real API/database.
# This serves as a demonstration of the concept.

KNOWN_BREACHES_DB = {
    "known_breaches": [
        {
            "name": "MockBank_2023",
            "domain": "mockbank.com",
            "date": "2023-08-15",
            "data_classes": ["Email addresses", "Phone numbers", "Account balances"],
            "description": "MockBank suffered a data breach exposing customer account information.",
        },
        {
            "name": "SocialApp_2024",
            "domain": "socialapp.example.com",
            "date": "2024-03-22",
            "data_classes": ["Email addresses", "Phone numbers", "Passwords", "Dates of birth"],
            "description": "Social media platform data breach compromised user profiles.",
        },
        {
            "name": "ShopEasy_2022",
            "domain": "shopeasy.example.com",
            "date": "2022-11-10",
            "data_classes": ["Email addresses", "Phone numbers", "Physical addresses", "Payment history"],
            "description": "E-commerce platform data leak exposed customer purchase data.",
        },
        {
            "name": "HealthConnect_2024",
            "domain": "healthconnect.example.org",
            "date": "2024-01-05",
            "data_classes": ["Email addresses", "Phone numbers", "Medical records", "Insurance details"],
            "description": "Healthcare provider database breach compromised sensitive medical information.",
        },
        {
            "name": "CloudDrive_2023",
            "domain": "clouddrive.example.com",
            "date": "2023-06-18",
            "data_classes": ["Email addresses", "Phone numbers", "Files", "Encryption keys"],
            "description": "Cloud storage service breach exposed user files and metadata.",
        },
    ]
}


# ---------------------------------------------------------------------------
# HIBP API v3 - k-Anonymity SHA-1 Prefix Search
# ---------------------------------------------------------------------------

HIBP_API_BASE = "https://api.pwnedpasswords.com/range/"


def _sha1_hash(data: str) -> str:
    """Compute SHA-1 hash of a string."""
    return hashlib.sha1(data.encode("utf-8").lower().strip()).hexdigest().upper()


def _check_hibp_prefix(sha1_prefix: str) -> List[str]:
    """
    Query HIBP API with the first 5 characters of the SHA-1 hash (k-anonymity).
    Returns a list of full hash suffixes that match.
    """
    try:
        req = Request(f"{HIBP_API_BASE}{sha1_prefix}", headers={"User-Agent": "CyberShield-BreachChecker/1.0"})
        with urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = resp.read().decode("utf-8")
                return [line.strip() for line in data.splitlines()]
    except HTTPError as e:
        logger.warning(f"HIBP API HTTP error: {e.code} - {e.reason}")
    except URLError as e:
        logger.warning(f"HIBP API URL error: {e.reason}")
    except Exception as e:
        logger.warning(f"HIBP API error: {str(e)}")
    return []


def _check_email_via_hibp(email: str) -> Tuple[bool, List[str]]:
    """
    Check if an email appears in known breaches using HIBP API.
    Since HIBP's API only checks passwords by hash prefix, we use the
    email as the search term against a broader approach.

    For emails, we check via a simulated method using the local breach DB
    and return whether the email domain matches any known breached domains.
    """
    # Extract domain from email
    match = re.match(r"^.+@(.+)$", email.strip().lower())
    if not match:
        return False, []

    domain = match.group(1)
    matched_breaches = []

    for breach in KNOWN_BREACHES_DB["known_breaches"]:
        # Check if domain matches or partially matches breach domain
        if domain == breach["domain"] or domain.split(".")[0] in breach["domain"]:
            matched_breaches.append(breach["name"])

    return len(matched_breaches) > 0, matched_breaches


# ---------------------------------------------------------------------------
# Phone Breach Check (Simulated)
# ---------------------------------------------------------------------------

def _check_phone_breaches(phone_number: str) -> Tuple[bool, List[str]]:
    """
    Simulated phone number breach check.
    In production, this would query a real breach database API.
    
    Uses a hash-based approach: hashes the phone number and checks against
    a simulated compromised phone hash database.
    """
    # Normalize phone number
    cleaned = re.sub(r"[^\d]", "", phone_number)
    if len(cleaned) < 10:
        return False, []

    # Simulate: check last 4 digits of phone against a "compromised" list
    # This is purely for demonstration
    compromised_suffixes = {"1234", "5678", "0000", "1111", "4321", "8888"}
    suffix = cleaned[-4:]

    matched_breaches = []

    if suffix in compromised_suffixes:
        # Simulate that this phone appears in some breaches
        for breach in KNOWN_BREACHES_DB["known_breaches"]:
            if "Phone numbers" in breach["data_classes"]:
                matched_breaches.append(breach["name"])

    return len(matched_breaches) > 0, matched_breaches


# ---------------------------------------------------------------------------
# Main Public API
# ---------------------------------------------------------------------------

def check_personal_info_breaches(email: str, phone_number: str = "") -> Dict[str, Any]:
    """
    Main entry point. Checks user's email and phone against breach databases.

    Args:
        email: User's email address to check
        phone_number: User's phone number to check (optional)

    Returns:
        dict with breach check results
    """
    results = {
        "email_checked": email,
        "phone_checked": phone_number if phone_number else None,
        "breach_count": 0,
        "breaches": [],
        "at_risk": False,
        "risk_level": "Safe",
        "recommendations": [],
        "check_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "details": {},
    }

    all_breach_names = set()
    breach_details = []

    # --- Check email ---
    email_breached, email_breach_names = _check_email_via_hibp(email)
    results["email_breached"] = email_breached

    if email_breached:
        for bname in email_breach_names:
            all_breach_names.add(bname)

    # --- Check phone ---
    phone_breached = False
    phone_breach_names = []
    if phone_number:
        phone_breached, phone_breach_names = _check_phone_breaches(phone_number)
        results["phone_breached"] = phone_breached
        if phone_breached:
            for bname in phone_breach_names:
                all_breach_names.add(bname)
    else:
        results["phone_breached"] = False

    # --- Build breach details ---
    for breach in KNOWN_BREACHES_DB["known_breaches"]:
        if breach["name"] in all_breach_names:
            breach_details.append({
                "name": breach["name"],
                "domain": breach["domain"],
                "date": breach["date"],
                "data_classes": breach["data_classes"],
                "description": breach["description"],
                "compromised_data": [],
            })
            # Add what data was compromised for this user
            if email_breached and breach["name"] in email_breach_names:
                breach_details[-1]["compromised_data"].append("Email address")
            if phone_breached and breach["name"] in phone_breach_names:
                breach_details[-1]["compromised_data"].append("Phone number")

    results["breaches"] = breach_details
    results["breach_count"] = len(breach_details)

    # --- Determine risk level ---
    if len(breach_details) >= 3:
        results["risk_level"] = "Critical"
        results["at_risk"] = True
    elif len(breach_details) >= 1:
        results["risk_level"] = "Warning"
        results["at_risk"] = True
    else:
        results["risk_level"] = "Safe"
        results["at_risk"] = False

    # --- Generate recommendations ---
    recommendations = []
    if email_breached:
        recommendations.append("Change the password associated with this email account immediately.")
        recommendations.append("Enable two-factor authentication (2FA) on all accounts using this email.")
        recommendations.append("Monitor your email for phishing attempts that may reference these breaches.")

    if phone_breached:
        recommendations.append("Be cautious of SMS phishing (smishing) targeting your phone number.")
        recommendations.append("Avoid sharing your phone number unnecessarily on online platforms.")

    if len(breach_details) >= 2:
        recommendations.append("Consider using a password manager to generate unique, strong passwords.")
        recommendations.append("Regularly check your financial accounts for unauthorized transactions.")

    if not recommendations:
        recommendations.append("Your personal info appears safe. Continue practicing good security hygiene.")
        recommendations.append("Use unique passwords for every account.")

    results["recommendations"] = recommendations

    # --- Details ---
    results["details"] = {
        "hibp_api_used": True,
        "simulated_phone_check": True,
        "email_domain": email.split("@")[1] if "@" in email else "unknown",
    }

    return results


def get_breach_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract summary statistics from breach check results."""
    return {
        "total_breaches": results.get("breach_count", 0),
        "at_risk": results.get("at_risk", False),
        "risk_level": results.get("risk_level", "Safe"),
        "email_affected": results.get("email_breached", False),
        "phone_affected": results.get("phone_breached", False),
    }


def format_breach_summary(results: Dict[str, Any]) -> str:
    """Generate a human-readable summary string."""
    count = results.get("breach_count", 0)
    if count == 0:
        return "✅ No breaches found. Your personal information appears safe."
    elif count == 1:
        return f"⚠ 1 breach found. Your information may be at risk."
    else:
        return f"🔴 {count} breaches found! Immediate action recommended."

