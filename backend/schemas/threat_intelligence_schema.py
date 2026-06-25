"""
Threat Intelligence Schemas for Frontend
"""

from pydantic import BaseModel
from typing import List, Optional, Dict


class IOCLookupResult(BaseModel):
    """IOC lookup result from threat feeds"""
    indicator: str  # IP, domain, hash, URL
    indicator_type: str  # IP, DOMAIN, HASH, URL
    virustotal_detections: Optional[int] = None
    virustotal_ratio: Optional[str] = None  # "detection_count/total_sources"
    virustotal_category: Optional[str] = None
    virustotal_country: Optional[str] = None
    virustotal_isp: Optional[str] = None
    abuseipdb_score: Optional[int] = None  # 0-100 reputation score
    abuseipdb_reports: Optional[int] = None
    confidence: Optional[float] = None
    last_updated: Optional[str] = None


class MITRETechnique(BaseModel):
    """MITRE ATT&CK technique"""
    technique_id: str  # e.g., "T1040"
    technique_name: str
    tactic: str  # Reconnaissance, Execution, etc.
    hit_count: int
    severity: str  # Color-coded severity
    description: Optional[str] = None


class ThreatIntelligenceResponse(BaseModel):
    """Threat intelligence data"""
    ioc_lookup: Optional[IOCLookupResult] = None
    mitre_techniques: List[MITRETechnique] = []
    threat_feeds: List[Dict[str, str]] = []
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


class IOCSearchRequest(BaseModel):
    """Search request for IOC"""
    indicator: str
    lookup_sources: Optional[List[str]] = None  # virustotal, abuseipdb, etc.


class ThreatFeedItem(BaseModel):
    """Item from threat feed"""
    indicator: str
    threat_type: str
    source: str
    confidence: int  # 0-100
    updated_at: str
