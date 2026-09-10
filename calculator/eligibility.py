"""
ADU Eligibility Calculation Engine.

Provides deterministic, testable evaluation of questionnaire answers
to determine whether a property is Potentially Eligible, Needs Further Review,
or is Currently Unlikely to Qualify for an Accessory Dwelling Unit (ADU).

NOTE: This is a demonstration prototype and does not constitute formal legal,
zoning, or architectural advice.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


STATUS_ELIGIBLE = "Potentially Eligible"
STATUS_REVIEW = "Needs Further Review"
STATUS_UNLIKELY = "Currently Unlikely to Qualify"

CODE_ELIGIBLE = "eligible"
CODE_REVIEW = "review"
CODE_UNLIKELY = "unlikely"

DISCLAIMER_TEXT = (
    "This calculator is a demonstration prototype designed for preliminary informational "
    "screening only. It does not constitute legal, zoning, architectural, or structural advice. "
    "Actual permitting requirements vary by local jurisdiction, municipal ordinances, utility "
    "capacity, and specific parcel characteristics."
)

QUESTIONS = [
    {
        "id": "owns_property",
        "text": "Do you own the property?",
        "help_text": "Permitting and building an ADU requires legal ownership or formal owner authorization.",
    },
    {
        "id": "located_in_california",
        "text": "Is the property located in California?",
        "help_text": "This prototype applies California state ADU statutory guidelines (e.g., California Government Code Section 65852.2).",
    },
    {
        "id": "is_residential",
        "text": "Is the property a residential property?",
        "help_text": "ADU state statutes apply to residential or mixed-use zoned properties.",
    },
    {
        "id": "is_single_family",
        "text": "Is it a single-family property?",
        "help_text": "Both single-family and multi-family properties can qualify in California, but single-family lots follow streamlined detached/attached rules.",
    },
    {
        "id": "has_sufficient_space",
        "text": "Does the property have sufficient space for an ADU?",
        "help_text": "Typically at least 4-foot rear/side setbacks and adequate yard area for a standalone detached structure.",
    },
    {
        "id": "has_existing_structure",
        "text": "Is there an existing garage, basement, or other structure suitable for conversion?",
        "help_text": "Existing accessory structures or attached spaces can often be converted even if yard footprint is limited.",
    },
    {
        "id": "has_restrictions",
        "text": "Are there any known restrictions that may prevent construction?",
        "help_text": "Examples: utility easements, extreme hillside topography, coastal commission overlay, or strict historic district covenants.",
    },
]

QUESTION_MAP = {q["id"]: q for q in QUESTIONS}


def normalize_bool(val: Any) -> bool:
    """Normalize various truthy/falsy representations to a boolean."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("yes", "true", "1", "y")
    if isinstance(val, (int, float)):
        return bool(val)
    return False


@dataclass
class EligibilityResult:
    status: str
    status_code: str
    summary: str
    key_factors: List[str] = field(default_factory=list)
    disclaimer: str = DISCLAIMER_TEXT
    answers: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "status_code": self.status_code,
            "summary": self.summary,
            "key_factors": self.key_factors,
            "disclaimer": self.disclaimer,
            "answers": self.answers,
        }


def calculate_eligibility(raw_answers: Dict[str, Any]) -> EligibilityResult:
    """
    Deterministically evaluates eligibility based on the 7 standard questionnaire answers.
    
    Evaluation Rules:
    1. Unlikely to Qualify:
       - Does not own property (owner authorization required).
       - Non-residential property (ADU statutes target residential parcels).
       - Neither sufficient yard space nor an existing structure for conversion.
    
    2. Needs Further Review:
       - Outside California (statutory criteria vary widely by state/country).
       - Has known severe site/legal restrictions (easements, overlays, steep slope).
       - Multi-family property (eligible under CA law, but requires unit density & conversion analysis).
       - No yard space, but has an existing structure (feasible conversion, but needs structural/parking review).
    
    3. Potentially Eligible:
       - Meets all primary ownership, residential, California, and site feasibility criteria without major restrictions.
    """
    answers = {q["id"]: normalize_bool(raw_answers.get(q["id"])) for q in QUESTIONS}

    owns = answers["owns_property"]
    california = answers["located_in_california"]
    residential = answers["is_residential"]
    single_family = answers["is_single_family"]
    space = answers["has_sufficient_space"]
    structure = answers["has_existing_structure"]
    restrictions = answers["has_restrictions"]

    factors: List[str] = []

    # Priority 1: Check for outright disqualifiers
    if not owns:
        factors.append("Property ownership is required to apply for permits and construct an ADU.")
        return EligibilityResult(
            status=STATUS_UNLIKELY,
            status_code=CODE_UNLIKELY,
            summary="Based on your responses, an ADU application cannot proceed without registered property ownership.",
            key_factors=factors,
            answers=answers,
        )

    if not residential:
        factors.append("State and municipal ADU regulations specifically apply to parcels with residential zoning.")
        return EligibilityResult(
            status=STATUS_UNLIKELY,
            status_code=CODE_UNLIKELY,
            summary="Non-residential parcels are generally ineligible for residential ADU permits.",
            key_factors=factors,
            answers=answers,
        )

    if not space and not structure:
        factors.append("Neither open yard space for new ground-up construction nor an existing structure for conversion is available.")
        return EligibilityResult(
            status=STATUS_UNLIKELY,
            status_code=CODE_UNLIKELY,
            summary="Without sufficient yard area or an existing structure to convert, construction is physically constrained.",
            key_factors=factors,
            answers=answers,
        )

    # Priority 2: Check for Review Triggers
    needs_review = False

    if not california:
        needs_review = True
        factors.append("The property is outside California. ADU statutes, setbacks, and utility mandates differ by state.")

    if restrictions:
        needs_review = True
        factors.append("Known site or legal restrictions (e.g., utility easements, HOA covenants, steep slope, or coastal zones) require local planning department review.")

    if not single_family:
        needs_review = True
        factors.append("Multi-family properties can qualify in California (up to two detached ADUs plus conversion spaces), but require custom density and floor-area calculations.")

    if not space and structure:
        needs_review = True
        factors.append("Yard space is limited for ground-up construction, but your existing garage/basement structure offers potential for an interior or garage conversion ADU.")

    if needs_review:
        return EligibilityResult(
            status=STATUS_REVIEW,
            status_code=CODE_REVIEW,
            summary="Your property shows promise, but specific factors require deeper review by a planning or building specialist.",
            key_factors=factors,
            answers=answers,
        )

    # Priority 3: Potentially Eligible
    factors.append("Verified property ownership and residential zoning.")
    factors.append("Located within California with statewide streamlined permitting protections.")
    if single_family:
        factors.append("Single-family parcel eligible for ministerial review under state statute.")
    if space:
        factors.append("Adequate yard space available for detached or attached construction.")
    if structure:
        factors.append("Existing structure provides versatile options for attached conversion or hybrid design.")
    factors.append("No self-reported severe easements or prohibitive site restrictions.")

    return EligibilityResult(
        status=STATUS_ELIGIBLE,
        status_code=CODE_ELIGIBLE,
        summary="Your property meets the foundational baseline criteria for adding an Accessory Dwelling Unit under California standards.",
        key_factors=factors,
        answers=answers,
    )
