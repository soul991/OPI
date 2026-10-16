"""Typed schema definition for OPI research agent and console inputs."""

from datetime import datetime
from typing import Dict, Any, Optional, TypeVar, Generic, Literal, List
from pydantic import BaseModel, Field

T = TypeVar("T")

GroundingStatus = Literal[
    "VERIFIED_IN_SNAPSHOT",
    "NOT_FOUND_IN_SNAPSHOT",
    "FETCH_FAILED",
    "UNVERIFIED"
]


class FieldProposal(BaseModel, Generic[T]):
    """Container for an individual feature extracted or proposed by research agent."""
    value: Optional[T] = None
    source_url: Optional[str] = None
    page_date: Optional[str] = None
    accessed_on: Optional[str] = None
    snapshot_path: Optional[str] = None
    snapshot_hash: Optional[str] = None
    grounding_status: GroundingStatus = "UNVERIFIED"
    confidence: Optional[str] = "medium"  # high, medium, low
    edited_by_user: bool = False
    verbatim_quote: Optional[str] = None

    def get_grounded_value(self) -> Optional[T]:
        """Return value only if verified in snapshot or confirmed/edited by human user."""
        if self.edited_by_user or self.grounding_status == "VERIFIED_IN_SNAPSHOT":
            return self.value
        return None


class IPOCandidateSchema(BaseModel):
    """Complete typed candidate representation for research, review, and scoring."""
    run_id: str = Field(default_factory=lambda: f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    company: str

    # Dates
    open_date: FieldProposal[str] = Field(default_factory=FieldProposal)
    close_date: FieldProposal[str] = Field(default_factory=FieldProposal)
    listing_date: FieldProposal[str] = Field(default_factory=FieldProposal)

    # Issue Structure
    issue_price: FieldProposal[float] = Field(default_factory=FieldProposal)
    issue_size_cr: FieldProposal[float] = Field(default_factory=FieldProposal)
    fresh_issue_pct: FieldProposal[float] = Field(default_factory=FieldProposal)
    ofs_pct: FieldProposal[float] = Field(default_factory=FieldProposal)
    lot_size: FieldProposal[int] = Field(default_factory=FieldProposal)

    # Subscription Demand
    sub_qib: FieldProposal[float] = Field(default_factory=FieldProposal)
    sub_nii: FieldProposal[float] = Field(default_factory=FieldProposal)
    sub_retail: FieldProposal[float] = Field(default_factory=FieldProposal)
    sub_total: FieldProposal[float] = Field(default_factory=FieldProposal)

    # Valuation & Fundamentals
    pe_ratio: FieldProposal[float] = Field(default_factory=FieldProposal)
    peer_median_pe: FieldProposal[float] = Field(default_factory=FieldProposal)
    debt_equity: FieldProposal[float] = Field(default_factory=FieldProposal)

    # Categoricals
    sector: FieldProposal[str] = Field(default_factory=FieldProposal)
    exchange: FieldProposal[str] = Field(default_factory=FieldProposal)

    # Market Signals & Grey Market Premium
    gmp_pct: FieldProposal[float] = Field(default_factory=FieldProposal)
    gmp_as_of_date: FieldProposal[str] = Field(default_factory=FieldProposal)
    nifty_30d_return: FieldProposal[float] = Field(default_factory=FieldProposal)
    india_vix: FieldProposal[float] = Field(default_factory=FieldProposal)
    recent_ipo_avg_gain: FieldProposal[float] = Field(default_factory=FieldProposal)

    notes: Optional[str] = None
    user_confirmed: bool = False

    def to_model_features(self) -> Dict[str, Any]:
        """Export grounded and user-confirmed features into dictionary matching model pipeline."""
        return {
            "company": self.company,
            "open_date": self.open_date.get_grounded_value(),
            "close_date": self.close_date.get_grounded_value(),
            "listing_date": self.listing_date.get_grounded_value(),
            "issue_price": self.issue_price.get_grounded_value(),
            "issue_size_cr": self.issue_size_cr.get_grounded_value(),
            "fresh_issue_pct": self.fresh_issue_pct.get_grounded_value() or 0.0,
            "ofs_pct": self.ofs_pct.get_grounded_value() or 0.0,
            "lot_size": self.lot_size.get_grounded_value(),
            "sub_qib": self.sub_qib.get_grounded_value(),
            "sub_nii": self.sub_nii.get_grounded_value(),
            "sub_retail": self.sub_retail.get_grounded_value(),
            "sub_total": self.sub_total.get_grounded_value(),
            "pe_ratio": self.pe_ratio.get_grounded_value(),
            "peer_median_pe": self.peer_median_pe.get_grounded_value(),
            "debt_equity": self.debt_equity.get_grounded_value(),
            "sector": self.sector.get_grounded_value() or "Industrial & Manufacturing",
            "exchange": self.exchange.get_grounded_value() or "BOTH",
            "gmp_pct": self.gmp_pct.get_grounded_value(),
            "nifty_30d_return": self.nifty_30d_return.get_grounded_value(),
            "india_vix": self.india_vix.get_grounded_value(),
            "recent_ipo_avg_gain": self.recent_ipo_avg_gain.get_grounded_value(),
            "notes": self.notes or "",
        }

    def grounding_metrics(self) -> Dict[str, Any]:
        """Compute verification and grounding summary stats."""
        fields = [
            self.open_date, self.close_date, self.listing_date,
            self.issue_price, self.issue_size_cr, self.fresh_issue_pct,
            self.ofs_pct, self.lot_size, self.sub_qib, self.sub_nii,
            self.sub_retail, self.sub_total, self.pe_ratio,
            self.peer_median_pe, self.debt_equity, self.sector,
            self.exchange, self.gmp_pct
        ]
        non_null = [f for f in fields if f.value is not None]
        verified = [f for f in non_null if f.grounding_status == "VERIFIED_IN_SNAPSHOT" or f.edited_by_user]
        failed = [f for f in non_null if f.grounding_status == "NOT_FOUND_IN_SNAPSHOT"]
        unreachable = [f for f in non_null if f.grounding_status == "FETCH_FAILED"]
        
        rate = (len(verified) / len(non_null) * 100) if non_null else 0.0
        return {
            "total_fields": len(fields),
            "populated_fields": len(non_null),
            "verified_fields": len(verified),
            "failed_grounding": len(failed),
            "fetch_failed": len(unreachable),
            "grounding_rate_pct": round(rate, 1)
        }
