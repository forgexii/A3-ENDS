"""
Threat Intelligence Routes - Frontend Integration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.schemas.threat_intelligence_schema import (
    IOCLookupResult,
    MITRETechnique,
    ThreatIntelligenceResponse,
    IOCSearchRequest,
)
from typing import List
import re

router = APIRouter(
    prefix="/threat-intelligence",
    tags=["Threat Intelligence"]
)


def identify_indicator_type(indicator: str) -> str:
    """Identify IOC type"""
    # Check if IP
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ip_pattern, indicator):
        return "IP"
    
    # Check if domain
    domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if re.match(domain_pattern, indicator):
        return "DOMAIN"
    
    # Check if hash (SHA256, MD5, SHA1)
    if len(indicator) == 64 or len(indicator) == 32 or len(indicator) == 40:
        if all(c in '0123456789abcdefABCDEF' for c in indicator):
            return "HASH"
    
    # Check if URL
    if indicator.startswith(('http://', 'https://')):
        return "URL"
    
    return "UNKNOWN"


@router.post("/ioc-lookup")
def lookup_ioc(
    request: IOCSearchRequest,
    db: Session = Depends(get_db)
):
    """Lookup IOC across threat feeds"""
    
    indicator_type = identify_indicator_type(request.indicator)
    
    if indicator_type == "UNKNOWN":
        raise HTTPException(status_code=400, detail="Invalid indicator format")
    
    # Mock threat feed data
    mock_lookups = {
        "185.220.101.45": {
            "virustotal_detections": 42,
            "virustotal_ratio": "42/89",
            "virustotal_category": "Malware",
            "virustotal_country": "NL",
            "virustotal_isp": "Leaseweb",
            "abuseipdb_score": 98,
            "abuseipdb_reports": 1248,
            "confidence": 0.99,
        },
        "10.0.1.50": {
            "virustotal_detections": 0,
            "virustotal_ratio": "0/89",
            "virustotal_category": "Clean",
            "virustotal_country": "US",
            "virustotal_isp": "Internal",
            "abuseipdb_score": 0,
            "abuseipdb_reports": 0,
            "confidence": 0.95,
        },
    }
    
    result = mock_lookups.get(
        request.indicator,
        {
            "virustotal_detections": 0,
            "virustotal_ratio": "0/89",
            "virustotal_category": "Unknown",
            "abuseipdb_score": 0,
            "abuseipdb_reports": 0,
            "confidence": 0.5,
        }
    )
    
    return IOCLookupResult(
        indicator=request.indicator,
        indicator_type=indicator_type,
        **result,
        last_updated="2025-06-12T10:30:00Z"
    )


@router.get("/mitre-techniques")
def get_mitre_techniques(
    attack_type: str = None,
    db: Session = Depends(get_db)
):
    """Get MITRE ATT&CK techniques for detected attacks"""
    
    # Mock MITRE data
    mitre_techniques = [
        MITRETechnique(
            technique_id="T1040",
            technique_name="Traffic Duplication",
            tactic="Reconnaissance",
            hit_count=12,
            severity="MEDIUM",
            description="Adversary captures network traffic to gather intelligence"
        ),
        MITRETechnique(
            technique_id="T1589",
            technique_name="Gather Victim Identity Information",
            tactic="Reconnaissance",
            hit_count=8,
            severity="MEDIUM",
            description="Adversary gathers identifying information about targets"
        ),
        MITRETechnique(
            technique_id="T1090",
            technique_name="Proxy",
            tactic="Command and Control",
            hit_count=24,
            severity="HIGH",
            description="Adversary routes traffic through intermediate proxies"
        ),
        MITRETechnique(
            technique_id="T1190",
            technique_name="Exploit Public-Facing Application",
            tactic="Initial Access",
            hit_count=15,
            severity="CRITICAL",
            description="Adversary exploits vulnerabilities in public applications"
        ),
        MITRETechnique(
            technique_id="T1595",
            technique_name="Active Scanning",
            tactic="Reconnaissance",
            hit_count=31,
            severity="HIGH",
            description="Adversary performs active scanning to identify targets"
        ),
        MITRETechnique(
            technique_id="T1498",
            technique_name="Network Denial of Service",
            tactic="Impact",
            hit_count=47,
            severity="CRITICAL",
            description="Adversary performs DDoS/DoS attacks"
        ),
        MITRETechnique(
            technique_id="T1046",
            technique_name="Network Service Scanning",
            tactic="Discovery",
            hit_count=19,
            severity="HIGH",
            description="Adversary scans for exposed network services"
        ),
        MITRETechnique(
            technique_id="T1021",
            technique_name="Remote Services",
            tactic="Lateral Movement",
            hit_count=6,
            severity="HIGH",
            description="Adversary uses remote services for lateral movement"
        ),
        MITRETechnique(
            technique_id="T1210",
            technique_name="Exploitation of Remote Services",
            tactic="Lateral Movement",
            hit_count=9,
            severity="CRITICAL",
            description="Adversary exploits remote service vulnerabilities"
        ),
        MITRETechnique(
            technique_id="T1559",
            technique_name="Inter-Process Communication",
            tactic="Command and Control",
            hit_count=4,
            severity="MEDIUM",
            description="Adversary uses IPC for command execution"
        ),
        MITRETechnique(
            technique_id="T1571",
            technique_name="Non-Standard Port",
            tactic="Command and Control",
            hit_count=22,
            severity="HIGH",
            description="Adversary uses non-standard ports for communication"
        ),
        MITRETechnique(
            technique_id="T1041",
            technique_name="Exfiltration Over C2 Channel",
            tactic="Exfiltration",
            hit_count=3,
            severity="CRITICAL",
            description="Adversary exfiltrates data over command and control channels"
        ),
    ]
    
    return {"techniques": mitre_techniques}


@router.get("/threat-level/{indicator}")
def assess_threat_level(
    indicator: str,
    db: Session = Depends(get_db)
):
    """Assess overall threat level for an indicator"""
    
    # Get IOC lookup
    lookup_result = lookup_ioc(
        IOCSearchRequest(indicator=indicator),
        db
    )
    
    # Calculate threat level
    threat_score = 0
    
    if lookup_result.abuseipdb_score:
        threat_score += lookup_result.abuseipdb_score / 100 * 40
    
    if lookup_result.virustotal_detections:
        threat_score += min(lookup_result.virustotal_detections / 89 * 40, 40)
    
    threat_score += lookup_result.confidence * 20
    
    if threat_score >= 80:
        risk_level = "CRITICAL"
    elif threat_score >= 60:
        risk_level = "HIGH"
    elif threat_score >= 40:
        risk_level = "MEDIUM"
    elif threat_score >= 20:
        risk_level = "LOW"
    else:
        risk_level = "INFO"
    
    return ThreatIntelligenceResponse(
        ioc_lookup=lookup_result,
        mitre_techniques=[],
        threat_feeds=[],
        risk_level=risk_level
    )


@router.get("/feeds")
def get_threat_feeds(
    db: Session = Depends(get_db)
):
    """Get available threat feeds"""
    return {
        "feeds": [
            {
                "name": "VirusTotal",
                "status": "connected",
                "last_update": "2025-06-12T10:30:00Z",
                "indicators_count": 50000000
            },
            {
                "name": "AbuseIPDB",
                "status": "connected",
                "last_update": "2025-06-12T10:25:00Z",
                "indicators_count": 500000
            },
            {
                "name": "AlienVault OTX",
                "status": "connected",
                "last_update": "2025-06-12T09:15:00Z",
                "indicators_count": 100000
            },
            {
                "name": "Shodan",
                "status": "connected",
                "last_update": "2025-06-12T08:00:00Z",
                "indicators_count": 10000000
            },
        ]
    }
