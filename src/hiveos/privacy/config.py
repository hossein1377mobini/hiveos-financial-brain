"""
Privacy Configuration — Controls data egress policies.

Enforces ADR-0017: All customer data stays on customer infrastructure.
No data leaves unless explicitly configured.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set


class EgressPolicy(Enum):
    """Policy for outbound data transfers."""
    BLOCK_ALL = "block_all"           # No data leaves (default)
    ALLOW_REGISTRY = "allow_registry" # Allow domain pack registry only
    ALLOW_AI = "allow_ai"            # Allow AI provider calls
    ALLOW_ALL = "allow_all"          # Allow all (requires explicit opt-in)


class DataClassification(Enum):
    """Classification of data types."""
    CUSTOMER_DATA = "customer_data"   # User files, documents
    ORG_KNOWLEDGE = "org_knowledge"   # Organization knowledge base
    SKILL_OUTPUT = "skill_output"     # Skill execution results
    AUDIT_LOG = "audit_log"           # System audit logs
    METADATA = "metadata"            # Non-sensitive metadata
    ANONYMIZED = "anonymized"        # De-identified data


@dataclass
class EndpointConfig:
    """Configuration for an external endpoint."""
    url: str
    purpose: str
    data_types: List[DataClassification]
    enabled: bool = False
    requires_explicit_consent: bool = True


@dataclass
class PrivacyConfig:
    """
    Privacy configuration for HiveOS.
    
    Default: BLOCK_ALL — no data leaves the infrastructure.
    Must explicitly enable external endpoints.
    """
    # Global policy
    egress_policy: EgressPolicy = EgressPolicy.BLOCK_ALL
    
    # Allowed endpoints (only enabled ones are allowed)
    allowed_endpoints: Dict[str, EndpointConfig] = field(default_factory=dict)
    
    # Data classification rules
    never_leave: Set[DataClassification] = field(default_factory=lambda: {
        DataClassification.CUSTOMER_DATA,
        DataClassification.ORG_KNOWLEDGE,
    })
    
    # Audit settings
    audit_all_egress: bool = True
    audit_log_retention_days: int = 90
    
    # Network settings
    allowed_domains: Set[str] = field(default_factory=set)
    blocked_domains: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Initialize default allowed endpoints based on policy."""
        if not self.allowed_endpoints:
            self._init_default_endpoints()
    
    def _init_default_endpoints(self):
        """Set up default external endpoints (all disabled by default)."""
        self.allowed_endpoints = {
            "registry": EndpointConfig(
                url="https://registry.hiveos.dev",
                purpose="Domain Pack Registry",
                data_types=[DataClassification.METADATA],
                enabled=False,
            ),
            "ai_provider": EndpointConfig(
                url="https://api.openai.com",  # Placeholder
                purpose="AI Model Provider",
                data_types=[DataClassification.ORG_KNOWLEDGE],
                enabled=False,
            ),
            "updates": EndpointConfig(
                url="https://api.github.com",
                purpose="Update Checker",
                data_types=[DataClassification.METADATA],
                enabled=False,
            ),
        }
    
    def is_egress_allowed(self, endpoint_id: str, data_types: List[DataClassification]) -> bool:
        """
        Check if data egress is allowed for given endpoint and data types.
        
        Returns False if any data type is in never_leave set.
        """
        # Check if any data type is forbidden
        for dt in data_types:
            if dt in self.never_leave:
                return False
        
        # Check endpoint
        endpoint = self.allowed_endpoints.get(endpoint_id)
        if not endpoint or not endpoint.enabled:
            return False
        
        # Check policy
        if self.egress_policy == EgressPolicy.BLOCK_ALL:
            return False
        
        return True
    
    def enable_endpoint(self, endpoint_id: str) -> bool:
        """Enable an external endpoint."""
        if endpoint_id in self.allowed_endpoints:
            self.allowed_endpoints[endpoint_id].enabled = True
            return True
        return False
    
    def disable_endpoint(self, endpoint_id: str) -> bool:
        """Disable an external endpoint."""
        if endpoint_id in self.allowed_endpoints:
            self.allowed_endpoints[endpoint_id].enabled = False
            return True
        return False
    
    def add_endpoint(self, endpoint_id: str, endpoint: EndpointConfig) -> None:
        """Add a new external endpoint (disabled by default)."""
        endpoint.enabled = False
        self.allowed_endpoints[endpoint_id] = endpoint
    
    def set_policy(self, policy: EgressPolicy) -> None:
        """Set global egress policy."""
        self.egress_policy = policy
    
    def can_use_ai_provider(self) -> bool:
        """Check if AI provider calls are allowed."""
        return self.is_egress_allowed("ai_provider", [DataClassification.ORG_KNOWLEDGE])
    
    def can_access_registry(self) -> bool:
        """Check if domain pack registry access is allowed."""
        return self.is_egress_allowed("registry", [DataClassification.METADATA])
    
    def can_check_updates(self) -> bool:
        """Check if update checks are allowed."""
        return self.is_egress_allowed("updates", [DataClassification.METADATA])
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "egress_policy": self.egress_policy.value,
            "allowed_endpoints": {
                k: {
                    "url": v.url,
                    "purpose": v.purpose,
                    "data_types": [dt.value for dt in v.data_types],
                    "enabled": v.enabled,
                    "requires_explicit_consent": v.requires_explicit_consent,
                }
                for k, v in self.allowed_endpoints.items()
            },
            "never_leave": [dt.value for dt in self.never_leave],
            "audit_all_egress": self.audit_all_egress,
            "audit_log_retention_days": self.audit_log_retention_days,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PrivacyConfig":
        """Deserialize from dictionary."""
        return cls(
            egress_policy=EgressPolicy(data.get("egress_policy", "block_all")),
            allowed_endpoints={
                k: EndpointConfig(
                    url=v["url"],
                    purpose=v["purpose"],
                    data_types=[DataClassification(dt) for dt in v["data_types"]],
                    enabled=v.get("enabled", False),
                    requires_explicit_consent=v.get("requires_explicit_consent", True),
                )
                for k, v in data.get("allowed_endpoints", {}).items()
            },
            never_leave={DataClassification(dt) for dt in data.get("never_leave", [])},
            audit_all_egress=data.get("audit_all_egress", True),
            audit_log_retention_days=data.get("audit_log_retention_days", 90),
        )
    
    def save(self, path: Path) -> None:
        """Save configuration to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
    
    @classmethod
    def load(cls, path: Path) -> "PrivacyConfig":
        """Load configuration from file."""
        if not path.exists():
            return cls()  # Return defaults
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)
