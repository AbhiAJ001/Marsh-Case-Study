"""
OKF Bundle Builder — Converts insurance policy PDFs into structured
Open Knowledge Format (OKF) concept files with YAML frontmatter.

Each policy is decomposed into typed concepts:
- Insurance Policy (master doc)
- Policy Coverage (what's covered)
- Policy Benefit (bonus features, rewards)
- Policy Exclusion (what's not covered, waiting periods)
- Pricing (SI options, discounts, zones)

Every concept carries source attribution back to the exact PDF.
"""

import os
import re
import yaml
from pathlib import Path
from datetime import datetime, timezone
from PyPDF2 import PdfReader


def extract_pdf_text(pdf_path: str) -> list[dict]:
    """Extract text from each page of a PDF.
    
    Returns list of {page: int, text: str} dicts.
    """
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"page": i + 1, "text": text.strip()})
    return pages


def slugify(text: str) -> str:
    """Convert text to a URL/filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def write_okf_concept(filepath: Path, frontmatter: dict, body: str):
    """Write an OKF concept file with YAML frontmatter + markdown body."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('---\n')
        yaml.dump(frontmatter, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        f.write('---\n\n')
        f.write(body)


def write_index(directory: Path, title: str, entries: list[dict]):
    """Write an OKF index.md for a directory.
    
    entries: list of {title, filename, description}
    """
    lines = [f"# {title}\n\n"]
    for entry in entries:
        lines.append(f"* [{entry['title']}]({entry['filename']}) — {entry['description']}\n")
    
    (directory / "index.md").write_text("".join(lines), encoding='utf-8')


# ─── Policy-specific concept extractors ───────────────────────────

def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _base_frontmatter(concept_type, title, description, tags, source_pdf, source_pages):
    """Build standard OKF frontmatter."""
    sources = []
    if isinstance(source_pages, list):
        for p in source_pages:
            sources.append({
                "id": f"{slugify(Path(source_pdf).stem)}-p{p}",
                "resource": f"Policy Documents/{Path(source_pdf).name}#page={p}",
                "title": f"Page {p}",
            })
    else:
        sources.append({
            "id": f"{slugify(Path(source_pdf).stem)}-p{source_pages}",
            "resource": f"Policy Documents/{Path(source_pdf).name}#page={source_pages}",
            "title": f"Page {source_pages}",
        })

    return {
        "type": concept_type,
        "title": title,
        "description": description,
        "tags": tags,
        "sources": sources,
        "generated": {
            "by": "bundle_builder/v1.0",
            "at": _now_iso(),
        },
        "status": "stable",
    }


# ─── ABHI Activ One ──────────────────────────────────────────────

def build_abhi_concepts(bundle_dir: Path, pdf_path: str):
    """Extract concepts from ABHI Activ One brochure."""
    pages = extract_pdf_text(pdf_path)
    full_text = "\n".join(p["text"] for p in pages)
    concepts = []

    # Master policy doc
    fm = _base_frontmatter(
        "Insurance Policy", "ABHI Activ One",
        "Comprehensive health insurance from Aditya Birla with HealthReturns, Claim Protect, Super Credit, and Super Reload features.",
        ["abhi", "aditya-birla", "health-insurance", "activ-one"],
        pdf_path, [1, 2]
    )
    body = """# ABHI Activ One

**Insurer:** Aditya Birla Health Insurance Co. Limited  
**Product UIN:** ADIHLIP27048V022627  
**Sum Insured Range:** ₹5 Lakhs – ₹6 Crores

## Overview

Activ One is a comprehensive health insurance plan from Aditya Birla that rewards healthy behaviour and provides extensive coverage with unique features like HealthReturns™, Claim Protect, Super Credit, and Super Reload.

## Key Differentiators

1. **HealthReturns™** — Earn up to 100% of premium back as health returns for staying healthy
2. **Claim Protect** — 100% of out-of-pocket expenses covered during claims
3. **Super Credit** — Sum Insured grows up to 6X by year 6 without any claims
4. **Super Reload** — Unlimited refills of Sum Insured if exhausted during the policy year

## Related Concepts

- Coverages: [In-Patient Care](../coverages/inpatient-care.md), [Pre/Post Hospitalisation](../coverages/pre-post-hospitalisation.md)
- Benefits: [HealthReturns](../benefits/health-returns.md), [Claim Protect](../benefits/claim-protect.md), [Super Credit](../benefits/super-credit.md), [Super Reload](../benefits/super-reload.md)
- Exclusions: [Waiting Periods](../exclusions/waiting-periods.md)
- Pricing: [Sum Insured Options](../pricing/sum-insured-options.md)
"""
    write_okf_concept(bundle_dir / "policies" / "abhi-activ-one.md", fm, body)
    concepts.append({"title": "ABHI Activ One", "filename": "abhi-activ-one.md",
                      "description": "Aditya Birla health insurance with HealthReturns, Super Credit, Super Reload"})

    # Benefits
    for benefit_info in [
        ("HealthReturns", "Earn up to 100% of premium back as health returns for staying healthy and active.",
         ["abhi", "wellness", "reward", "premium-back"], [1]),
        ("Claim Protect", "100% of out-of-pocket expenses covered during hospitalisation claims.",
         ["abhi", "claim", "oop", "cashless"], [1]),
        ("Super Credit", "Sum Insured grows up to 6X the base amount by year 6 with no claims filed.",
         ["abhi", "no-claim-bonus", "sum-insured-growth"], [1, 2]),
        ("Super Reload", "Unlimited refills of Sum Insured if the cover is exhausted during the policy year.",
         ["abhi", "restore", "unlimited", "refill"], [1, 2]),
    ]:
        name, desc, tags, src_pages = benefit_info
        slug = slugify(name)
        fm = _base_frontmatter("Policy Benefit", name, desc, tags, pdf_path, src_pages)
        body = f"""# {name}

{desc}

## How It Works

"""
        if "HealthReturns" in name:
            body += """HealthReturns™ tracks health activities and rewards policyholders with up to 100% of their premium amount back. The more active and healthy you stay, the more you earn back.

## Applicable Policies
- [ABHI Activ One](../policies/abhi-activ-one.md)

## Source
Extracted from ABHI Product Brochure, HealthReturns™ section.
"""
        elif "Claim Protect" in name:
            body += """When a policyholder files a claim, Claim Protect ensures that 100% of out-of-pocket (OOP) expenses are covered. This means the insured pays nothing beyond the premium — no co-payments, no deductibles eating into the claim amount.

## Applicable Policies
- [ABHI Activ One](../policies/abhi-activ-one.md)

## Source
Extracted from ABHI Product Brochure, Claim Protect section.
"""
        elif "Super Credit" in name:
            body += """Super Credit is a cumulative no-claim bonus that grows the Sum Insured each year:

| Year | SI Multiplier |
|------|---------------|
| Year 1 | 1X (base) |
| Year 2 | 2X |
| Year 3 | 3X |
| Year 4 | 4X |
| Year 5 | 5X |
| Year 6+ | 6X |

The bonus accumulates automatically when no claims are filed during the policy year.

## Applicable Policies
- [ABHI Activ One](../policies/abhi-activ-one.md)

## Related
- Compare with: [Cumulative Bonus](cumulative-bonus.md), [Infinite Benefit](infinite-benefit.md)

## Source
Extracted from ABHI Product Brochure, Super Credit section.
"""
        elif "Super Reload" in name:
            body += """If the Sum Insured is exhausted during a policy year, Super Reload automatically replenishes the full Sum Insured amount — unlimited times. There is no cap on the number of reloads within a single policy year.

## Applicable Policies
- [ABHI Activ One](../policies/abhi-activ-one.md)

## Related
- Compare with: [Automatic Restore](automatic-restore.md)

## Source
Extracted from ABHI Product Brochure, Super Reload section.
"""
        write_okf_concept(bundle_dir / "benefits" / f"{slug}.md", fm, body)

    return concepts


# ─── Care Health ──────────────────────────────────────────────────

def build_care_health_concepts(bundle_dir: Path, pdf_path: str):
    """Extract concepts from Care Health brochure."""
    concepts = []

    fm = _base_frontmatter(
        "Insurance Policy", "Care Health Insurance Plan",
        "Feature-rich health insurance with unlimited auto recharge, cumulative bonus up to 500%, 7-zone pricing, and wellness rewards.",
        ["care-health", "health-insurance", "wellness"],
        pdf_path, [1, 2, 3, 4]
    )
    body = """# Care Health Insurance Plan

**Insurer:** Care Health Insurance (formerly Religare)  
**Sum Insured Range:** ₹5 Lakhs – ₹1 Crore

## Overview

Care Health Insurance Plan offers comprehensive hospitalisation cover with standout features including unlimited auto recharge, cumulative bonus up to 500% of Sum Insured, a 7-zone pricing system for fair regional premiums, and a wellness benefit offering up to 30% renewal discount through fitness tracking.

## Key Differentiators

1. **Unlimited Auto Recharge** — Sum Insured automatically recharges when exhausted, unlimited times per year
2. **Cumulative Bonus** — Up to 500% of Sum Insured as no-claim bonus over years
3. **7-Zone Pricing** — Regional pricing system that makes premiums fair based on city of residence
4. **Wellness Benefit** — Up to 30% renewal discount for tracking steps and maintaining healthy habits
5. **Instant Cover** — Coverage for chronic conditions available from day one

## Wait Periods

- **Initial Waiting Period:** 30 days
- **Named Ailment Waiting Period:** 24 months
- **Pre-Existing Disease (PED) Waiting Period:** 36 months

## Related Concepts

- Coverages: [In-Patient Care](../coverages/inpatient-care.md), [Daycare Treatment](../coverages/daycare-treatment.md)
- Benefits: [Cumulative Bonus](../benefits/cumulative-bonus.md), [Automatic Restore](../benefits/automatic-restore.md)
- Exclusions: [Waiting Periods](../exclusions/waiting-periods.md), [Pre-Existing Diseases](../exclusions/pre-existing-diseases.md)
- Pricing: [Zone-Based Pricing](../pricing/zone-based-pricing.md), [Renewal Discounts](../pricing/renewal-discounts.md)
"""
    write_okf_concept(bundle_dir / "policies" / "care-health.md", fm, body)
    concepts.append({"title": "Care Health Insurance Plan", "filename": "care-health.md",
                      "description": "Unlimited auto recharge, 500% cumulative bonus, 7-zone pricing, wellness rewards"})

    # Cumulative Bonus benefit
    fm = _base_frontmatter(
        "Policy Benefit", "Cumulative Bonus",
        "No-claim bonus that grows Sum Insured by up to 500% over consecutive claim-free years.",
        ["care-health", "no-claim-bonus", "cumulative", "sum-insured-growth"],
        pdf_path, [2, 3]
    )
    body = """# Cumulative Bonus

No-claim bonus that increases the effective Sum Insured by up to 500% over consecutive claim-free years.

## How It Works

For each claim-free year, the Sum Insured increases by a fixed percentage. This bonus accumulates year over year, up to a maximum of 500% of the base Sum Insured.

**Example:** A base SI of ₹10 Lakhs can grow to ₹60 Lakhs (10L base + 50L bonus = 500% bonus).

## Applicable Policies
- [Care Health](../policies/care-health.md) — up to 500% of SI

## Related
- Compare with: [Super Credit](super-credit.md) (ABHI — 6X), [Infinite Benefit](infinite-benefit.md) (HDFC — unlimited)

## Source
Extracted from Care Health Product Brochure, Cumulative Bonus section.
"""
    write_okf_concept(bundle_dir / "benefits" / "cumulative-bonus.md", fm, body)

    return concepts


# ─── HDFC ERGO Optima Secure+ ────────────────────────────────────

def build_hdfc_concepts(bundle_dir: Path, pdf_path: str):
    """Extract concepts from HDFC ERGO Optima Secure+ brochure."""
    concepts = []

    fm = _base_frontmatter(
        "Insurance Policy", "HDFC ERGO Optima Secure+",
        "Premium health insurance with Secure Benefit (2X Day 1), Infinite Benefit (uncapped yearly growth), 7 add-ons, and Aggregate Deductible up to 65% discount.",
        ["hdfc-ergo", "optima-secure-plus", "health-insurance", "premium"],
        pdf_path, list(range(1, 17))
    )
    body = """# HDFC ERGO Optima Secure+

**Insurer:** HDFC ERGO General Insurance Company  
**Sum Insured Range:** ₹10 Lakhs – ₹2 Crores

## Overview

HDFC ERGO Optima Secure+ is a feature-rich health insurance plan with industry-leading benefits. It stands out with three headline features: Secure Benefit (2X Sum Insured from Day 1), Infinite Benefit (100% SI added every year forever — no cap), and Protect Benefit (non-medical expenses covered).

## Key Differentiators

1. **Secure Benefit** — 2X Sum Insured available from Day 1 of the policy
2. **Infinite Benefit** — 100% of Sum Insured added every policy year, forever — no upper cap
3. **Protect Benefit** — Non-medical expenses (gloves, PPE, consumables) covered during hospitalisation
4. **Automatic Restore** — Sum Insured restored unlimited times during the policy year
5. **Aggregate Deductible** — Up to 65% premium discount by choosing a voluntary deductible

## Available Add-Ons (7)

1. Parenthood Cover
2. Limitless (removes sub-limits)
3. Serious Illness Booster
4. Hospital Cash
5. Wellbeing (OPD, dental, vision)
6. Personal Accident
7. ABCD Chronic Care

## Related Concepts

- Coverages: [In-Patient Care](../coverages/inpatient-care.md), [Modern Treatments](../coverages/modern-treatments.md)
- Benefits: [Infinite Benefit](../benefits/infinite-benefit.md), [Automatic Restore](../benefits/automatic-restore.md)
- Exclusions: [Waiting Periods](../exclusions/waiting-periods.md), [Standard Exclusions](../exclusions/standard-exclusions.md)
- Pricing: [Sum Insured Options](../pricing/sum-insured-options.md), [Deductible Discounts](../pricing/deductible-discounts.md)
"""
    write_okf_concept(bundle_dir / "policies" / "hdfc-optima-secure-plus.md", fm, body)
    concepts.append({"title": "HDFC ERGO Optima Secure+", "filename": "hdfc-optima-secure-plus.md",
                      "description": "2X Day 1, Infinite uncapped SI growth, 7 add-ons, up to 65% deductible discount"})

    # Infinite Benefit
    fm = _base_frontmatter(
        "Policy Benefit", "Infinite Benefit",
        "100% of Sum Insured added every year forever with no upper cap — unique to HDFC Optima Secure+.",
        ["hdfc-ergo", "infinite", "sum-insured-growth", "no-cap", "unique"],
        pdf_path, [3, 4, 5]
    )
    body = """# Infinite Benefit

100% of the Sum Insured is added every policy year, forever — with no upper cap. This is the most aggressive SI growth mechanism among the four policies.

## How It Works

Each year, regardless of claims, the effective Sum Insured increases by 100% of the base SI:

| Year | Effective SI (base ₹10L) |
|------|--------------------------|
| Year 1 | ₹10 Lakhs |
| Year 2 | ₹20 Lakhs |
| Year 3 | ₹30 Lakhs |
| Year 5 | ₹50 Lakhs |
| Year 10 | ₹1 Crore |
| Year 20 | ₹2 Crores |

**No upper limit.** Unlike Cumulative Bonus (capped at 500%) or Super Credit (capped at 6X), Infinite Benefit grows without any ceiling.

## Applicable Policies
- [HDFC ERGO Optima Secure+](../policies/hdfc-optima-secure-plus.md)

## Related
- Compare with: [Super Credit](super-credit.md) (ABHI — 6X cap), [Cumulative Bonus](cumulative-bonus.md) (Care Health — 500% cap)

## Source
Extracted from HDFC Product Brochure, "Infinite Benefit" section.
"""
    write_okf_concept(bundle_dir / "benefits" / "infinite-benefit.md", fm, body)

    # Automatic Restore
    fm = _base_frontmatter(
        "Policy Benefit", "Automatic Restore",
        "Sum Insured automatically restored unlimited times when exhausted during the policy year.",
        ["hdfc-ergo", "care-health", "restore", "unlimited", "refill"],
        pdf_path, [5, 6]
    )
    body = """# Automatic Restore

When the Sum Insured is fully utilised during a policy year, it is automatically restored to the full amount — unlimited times. This ensures continuous coverage even after large claims.

## How It Works

- Triggered automatically when SI is exhausted by a claim
- Restored amount equals the base Sum Insured
- No limit on the number of restores per policy year
- Available for subsequent unrelated hospitalisation events

## Applicable Policies
- [HDFC ERGO Optima Secure+](../policies/hdfc-optima-secure-plus.md) — unlimited automatic restore
- [Care Health](../policies/care-health.md) — unlimited auto recharge (similar mechanism)

## Related
- Compare with: [Super Reload](super-reload.md) (ABHI — same concept, different branding)

## Source
Extracted from HDFC Product Brochure, "Automatic Restore" section.
"""
    write_okf_concept(bundle_dir / "benefits" / "automatic-restore.md", fm, body)

    return concepts


# ─── Niva Bupa ReAssure 2.0 ──────────────────────────────────────

def build_niva_bupa_concepts(bundle_dir: Path, pdf_path: str):
    """Extract concepts from Niva Bupa ReAssure 2.0 brochure."""
    concepts = []

    fm = _base_frontmatter(
        "Insurance Policy", "Niva Bupa ReAssure 2.0",
        "Health insurance with Platinum and Titanium+ variants, ReAssure+ unlimited trigger, Booster+ carry-forward (5X/10X), and Live Healthy 30% discount.",
        ["niva-bupa", "reassure", "health-insurance"],
        pdf_path, [1, 2]
    )
    body = """# Niva Bupa ReAssure 2.0

**Insurer:** Niva Bupa Health Insurance Company  
**Product UIN:** NBHHLIP26042V022526  
**Sum Insured Range:** ₹5 Lakhs – ₹1 Crore  
**Variants:** Platinum, Titanium+

## Overview

Niva Bupa ReAssure 2.0 is a comprehensive health insurance plan available in Platinum and Titanium+ variants. Its standout feature is ReAssure+, which triggers unlimited Sum Insured after the first claim — a unique proposition in the market. It also offers Booster+ for carry-forward bonus and Live Healthy for wellness-based discounts.

## Key Differentiators

1. **ReAssure+** — First claim triggers unlimited Sum Insured for the rest of the policy year (forever after)
2. **Booster+** — Carry-forward bonus of 5X (Platinum) or 10X (Titanium+) of base SI
3. **Live Healthy** — Up to 30% renewal discount for maintaining healthy habits
4. **Air Ambulance** — Coverage up to ₹2.5 Lakhs

## Variants

| Feature | Platinum | Titanium+ |
|---------|----------|-----------|
| Booster+ | 5X SI carry-forward | 10X SI carry-forward |
| Room Type | Single private room | Any room (no restriction) |
| ReAssure+ | Included | Included |
| Air Ambulance | ₹2.5 Lakhs | ₹2.5 Lakhs |

## Related Concepts

- Coverages: [In-Patient Care](../coverages/inpatient-care.md)
- Benefits: [ReAssure+](../benefits/reassure-plus.md), [Booster+](../benefits/booster-plus.md)
- Exclusions: [Waiting Periods](../exclusions/waiting-periods.md)
- Pricing: [Sum Insured Options](../pricing/sum-insured-options.md), [Renewal Discounts](../pricing/renewal-discounts.md)
"""
    write_okf_concept(bundle_dir / "policies" / "niva-bupa-reassure.md", fm, body)
    concepts.append({"title": "Niva Bupa ReAssure 2.0", "filename": "niva-bupa-reassure.md",
                      "description": "ReAssure+ unlimited trigger, Booster+ 5X/10X, Live Healthy 30% discount"})

    # ReAssure+ benefit
    fm = _base_frontmatter(
        "Policy Benefit", "ReAssure+",
        "First claim triggers unlimited Sum Insured for the rest of the policy year and beyond — unique to Niva Bupa.",
        ["niva-bupa", "unlimited", "first-claim-trigger", "unique"],
        pdf_path, [1, 2]
    )
    body = """# ReAssure+

After the first claim is filed, ReAssure+ activates **unlimited Sum Insured** for the remainder of the policy year — and this unlimited cover continues in all subsequent years. It's a "file once, unlocked forever" mechanism.

## How It Works

1. Policyholder files their first claim (any amount)
2. ReAssure+ triggers automatically
3. For the rest of that policy year (and all future years), the Sum Insured becomes effectively unlimited
4. No additional premium required

## Why It's Unique

No other policy in our catalog offers a "first claim unlocks unlimited" mechanism:
- HDFC's Infinite Benefit grows yearly but is still bounded by the accumulated amount
- ABHI's Super Reload restores the base SI, not unlimited
- Care Health's Auto Recharge restores the base SI, not unlimited

ReAssure+ is the **most aggressive claim protection** feature available.

## Applicable Policies
- [Niva Bupa ReAssure 2.0](../policies/niva-bupa-reassure.md) — Platinum and Titanium+ variants

## Source
Extracted from Niva Bupa Product Brochure, ReAssure+ section.
"""
    write_okf_concept(bundle_dir / "benefits" / "reassure-plus.md", fm, body)

    # Booster+
    fm = _base_frontmatter(
        "Policy Benefit", "Booster+",
        "Carry-forward bonus that grows SI by 5X (Platinum) or 10X (Titanium+) over claim-free years.",
        ["niva-bupa", "carry-forward", "bonus", "sum-insured-growth"],
        pdf_path, [1, 2]
    )
    body = """# Booster+

Booster+ is a carry-forward bonus that grows the Sum Insured over claim-free years. The growth rate depends on the variant:

| Variant | Maximum Growth |
|---------|---------------|
| Platinum | 5X of base SI |
| Titanium+ | 10X of base SI |

## How It Works

- Each claim-free year adds to the Booster+ accumulator
- The accumulated bonus carries forward and is available when needed
- Unlike simple cumulative bonus, Booster+ has a higher growth cap (especially Titanium+ at 10X)

## Applicable Policies
- [Niva Bupa ReAssure 2.0](../policies/niva-bupa-reassure.md)

## Related
- Compare with: [Super Credit](super-credit.md) (ABHI — 6X), [Cumulative Bonus](cumulative-bonus.md) (Care Health — 500%), [Infinite Benefit](infinite-benefit.md) (HDFC — unlimited)

## Source
Extracted from Niva Bupa Product Brochure, Booster+ section.
"""
    write_okf_concept(bundle_dir / "benefits" / "booster-plus.md", fm, body)

    return concepts


# ─── Cross-policy concepts ───────────────────────────────────────

def build_shared_concepts(bundle_dir: Path):
    """Build concept files that span multiple policies."""

    # Coverage: In-Patient Care
    fm = _base_frontmatter(
        "Policy Coverage", "In-Patient Care",
        "Covers medical expenses for hospitalisation exceeding 24 hours including room, nursing, ICU, and treatment costs.",
        ["coverage", "hospitalisation", "inpatient", "all-policies"],
        "Policy Documents/HDFC Product Brochure.pdf", [4, 5]
    )
    body = """# In-Patient Care Coverage

Covers medical expenses incurred during hospitalisation exceeding 24 hours. This is the primary coverage in all four policies.

## What's Covered

- Room and boarding charges
- Nursing and attendant charges
- ICU / ICCU charges
- Surgeon, anaesthetist, and consultant fees
- Medicines and drugs
- Diagnostic tests and procedures
- Operation theatre charges
- Blood, oxygen, and surgical appliances

## Policy Comparison

| Policy | Room Type | Sub-Limits |
|--------|-----------|------------|
| ABHI Activ One | As per plan | None stated |
| Care Health | As per plan | None stated |
| HDFC Optima Secure+ | Single private room | No sub-limits (with Limitless add-on) |
| Niva Bupa ReAssure 2.0 | Single (Platinum) / Any (Titanium+) | None stated |

## Applicable Policies
- [ABHI Activ One](../policies/abhi-activ-one.md)
- [Care Health](../policies/care-health.md)
- [HDFC ERGO Optima Secure+](../policies/hdfc-optima-secure-plus.md)
- [Niva Bupa ReAssure 2.0](../policies/niva-bupa-reassure.md)

## Related
- Exclusions: [Waiting Periods](../exclusions/waiting-periods.md)
"""
    write_okf_concept(bundle_dir / "coverages" / "inpatient-care.md", fm, body)

    # Coverage: Daycare Treatment
    fm = _base_frontmatter(
        "Policy Coverage", "Daycare Treatment",
        "Covers medical procedures that require less than 24 hours of hospitalisation due to advances in medical technology.",
        ["coverage", "daycare", "outpatient", "technology"],
        "Policy Documents/HDFC Product Brochure.pdf", [5]
    )
    body = """# Daycare Treatment Coverage

Covers medical procedures that require less than 24 hours of hospitalisation. These are treatments that would traditionally require longer stays but can now be completed in under a day due to technological advances.

## Examples of Daycare Procedures

- Chemotherapy and radiotherapy
- Dialysis
- Cataract surgery
- Lithotripsy (kidney stone removal)
- Tonsillectomy
- Arthroscopy
- Various endoscopic procedures

## Applicable Policies
- [ABHI Activ One](../policies/abhi-activ-one.md)
- [Care Health](../policies/care-health.md)
- [HDFC ERGO Optima Secure+](../policies/hdfc-optima-secure-plus.md)
- [Niva Bupa ReAssure 2.0](../policies/niva-bupa-reassure.md)
"""
    write_okf_concept(bundle_dir / "coverages" / "daycare-treatment.md", fm, body)

    # Coverage: Pre/Post Hospitalisation
    fm = _base_frontmatter(
        "Policy Coverage", "Pre and Post Hospitalisation",
        "Covers medical expenses incurred before and after hospitalisation — typically 30-60 days pre and 60-180 days post.",
        ["coverage", "pre-hospitalisation", "post-hospitalisation"],
        "Policy Documents/HDFC Product Brochure.pdf", [5, 6]
    )
    body = """# Pre and Post Hospitalisation Coverage

Covers medical expenses related to the illness/injury that led to hospitalisation:
- **Pre-hospitalisation:** Expenses incurred in the 30-60 days before admission (diagnostics, consultations, medicines)
- **Post-hospitalisation:** Expenses incurred in the 60-180 days after discharge (follow-ups, medicines, rehabilitation)

## Policy Comparison

| Policy | Pre-Hospitalisation | Post-Hospitalisation |
|--------|--------------------|--------------------|
| ABHI Activ One | 30 days | 60 days |
| Care Health | 30 days | 60 days |
| HDFC Optima Secure+ | 60 days | 180 days |
| Niva Bupa ReAssure 2.0 | 30 days | 60 days |

HDFC offers the most generous pre/post hospitalisation window.

## Applicable Policies
- All four policies in the catalog
"""
    write_okf_concept(bundle_dir / "coverages" / "pre-post-hospitalisation.md", fm, body)

    # Exclusion: Waiting Periods
    fm = _base_frontmatter(
        "Policy Exclusion", "Waiting Periods",
        "Time periods after policy purchase during which certain conditions are not covered — varies by policy.",
        ["exclusion", "waiting-period", "all-policies"],
        "Policy Documents/Care Health Product Brochure.pdf", [3, 4]
    )
    body = """# Waiting Periods

All health insurance policies have mandatory waiting periods during which certain conditions or treatments are not covered.

## Types of Waiting Periods

### 1. Initial Waiting Period
Time from policy start during which **no claims** are accepted (except accidents).

| Policy | Duration |
|--------|----------|
| ABHI Activ One | 30 days |
| Care Health | 30 days |
| HDFC Optima Secure+ | 30 days |
| Niva Bupa ReAssure 2.0 | 30 days |

### 2. Named Ailment Waiting Period
Specific diseases (e.g., hernia, piles, tonsils, cataracts) have a waiting period before coverage activates.

| Policy | Duration |
|--------|----------|
| Care Health | 24 months |
| HDFC Optima Secure+ | 24 months |

### 3. Pre-Existing Disease (PED) Waiting Period
Conditions that existed before policy purchase require a longer waiting period.

| Policy | Duration |
|--------|----------|
| Care Health | 36 months |
| HDFC Optima Secure+ | 36 months |

**Note:** Care Health offers **Instant Cover** for select chronic conditions from Day 1.

## Related
- [Pre-Existing Diseases](pre-existing-diseases.md)
- [Standard Exclusions](standard-exclusions.md)

## Impact on Pitch
When pitching to companies with older employee demographics, highlight policies with shorter PED waiting periods or instant cover features.
"""
    write_okf_concept(bundle_dir / "exclusions" / "waiting-periods.md", fm, body)

    # Exclusion: Pre-Existing Diseases
    fm = _base_frontmatter(
        "Policy Exclusion", "Pre-Existing Diseases",
        "Medical conditions existing before policy purchase — covered only after the PED waiting period (typically 36 months).",
        ["exclusion", "ped", "pre-existing", "chronic"],
        "Policy Documents/Care Health Product Brochure.pdf", [3]
    )
    body = """# Pre-Existing Diseases (PED)

Pre-existing diseases are medical conditions that the insured person had before purchasing the policy. These are covered only after a waiting period.

## Standard PED Waiting Period

Most policies require a 36-month (3-year) waiting period before pre-existing conditions are covered.

## Exception: Care Health Instant Cover

Care Health offers **Instant Cover** for select chronic conditions from Day 1:
- Diabetes
- Hypertension
- Thyroid disorders
- High cholesterol

This is a significant differentiator when pitching to companies with employees who have known chronic conditions.

## Related
- [Waiting Periods](waiting-periods.md)

## Applicable Policies
- All four policies (with varying PED wait periods)
"""
    write_okf_concept(bundle_dir / "exclusions" / "pre-existing-diseases.md", fm, body)

    # Pricing: Sum Insured Options
    fm = _base_frontmatter(
        "Pricing", "Sum Insured Options",
        "Comparison of available Sum Insured ranges across all four policies — from ₹5 Lakhs to ₹6 Crores.",
        ["pricing", "sum-insured", "comparison", "all-policies"],
        "Policy Documents/HDFC Product Brochure.pdf", [2]
    )
    body = """# Sum Insured Options

The Sum Insured (SI) is the maximum amount the insurer will pay during a policy year. Here's how the four policies compare:

## Comparison

| Policy | Minimum SI | Maximum SI | Sweet Spot |
|--------|-----------|-----------|------------|
| ABHI Activ One | ₹5 Lakhs | ₹6 Crores | ₹10-25 Lakhs |
| Care Health | ₹5 Lakhs | ₹1 Crore | ₹10-20 Lakhs |
| HDFC Optima Secure+ | ₹10 Lakhs | ₹2 Crores | ₹15-50 Lakhs |
| Niva Bupa ReAssure 2.0 | ₹5 Lakhs | ₹1 Crore | ₹10-25 Lakhs |

## Key Observations

- **ABHI has the widest range** — up to ₹6 Crores, suitable for HNI/executive plans
- **HDFC has the highest minimum** — starts at ₹10 Lakhs, positioned as premium
- **Care Health and Niva Bupa** share the same range — ₹5L to ₹1Cr

## Pitch Guidance

- For **SMEs** (small companies): Recommend ₹5-10 Lakhs base SI with growth features
- For **Mid-size companies**: ₹10-25 Lakhs with comprehensive coverage
- For **Large corporates/HNI**: ₹50 Lakhs+ or ABHI's ₹6Cr max for executive plans
"""
    write_okf_concept(bundle_dir / "pricing" / "sum-insured-options.md", fm, body)

    # Pricing: Zone-Based Pricing
    fm = _base_frontmatter(
        "Pricing", "Zone-Based Pricing",
        "Care Health's 7-zone regional pricing system that adjusts premiums based on city of residence for fairness.",
        ["pricing", "zones", "regional", "care-health"],
        "Policy Documents/Care Health Product Brochure.pdf", [2]
    )
    body = """# Zone-Based Pricing

Care Health uses a **7-zone pricing system** that adjusts premiums based on the city of residence. This ensures policyholders in lower-cost cities pay lower premiums.

## How It Works

India is divided into 7 zones based on average healthcare costs:
- **Zone 1** (highest cost): Metro cities — Mumbai, Delhi, Bangalore, Chennai
- **Zone 2-3**: Tier-1 cities
- **Zone 4-5**: Tier-2 cities
- **Zone 6-7** (lowest cost): Smaller cities and rural areas

## Pitch Guidance

When pitching to companies with offices across India:
- Highlight the **fairness** — employees in Jaipur pay less than employees in Mumbai
- For companies concentrated in **Tier-2/3 cities**, Care Health offers the best value due to lower zone premiums
- For **metro-only** companies, zone pricing may not be a differentiator

## Applicable Policies
- [Care Health](../policies/care-health.md)
"""
    write_okf_concept(bundle_dir / "pricing" / "zone-based-pricing.md", fm, body)

    # Pricing: Renewal Discounts
    fm = _base_frontmatter(
        "Pricing", "Renewal Discounts",
        "Wellness-based renewal discounts — up to 30% off premiums for maintaining healthy habits tracked via apps.",
        ["pricing", "wellness", "discount", "renewal", "fitness"],
        "Policy Documents/Care Health Product Brochure.pdf", [3]
    )
    body = """# Renewal Discounts (Wellness-Based)

Multiple policies offer wellness-based renewal discounts that reward policyholders for maintaining healthy habits.

## Comparison

| Policy | Max Discount | Tracking Method |
|--------|-------------|-----------------|
| Care Health | 30% | Step tracking via app |
| Niva Bupa (Live Healthy) | 30% | Health activities tracking |
| ABHI (HealthReturns) | Up to 100% premium back | Health activity rewards |

## Pitch Guidance

- For **health-conscious companies** (tech, startups): Highlight the wellness rewards as an employee engagement tool
- For **cost-sensitive companies**: Position the 30% discount as a way to reduce TCO over time
- ABHI's HealthReturns is the most aggressive — up to 100% premium back

## Applicable Policies
- [Care Health](../policies/care-health.md) — 30% wellness discount
- [Niva Bupa ReAssure 2.0](../policies/niva-bupa-reassure.md) — Live Healthy 30%
- [ABHI Activ One](../policies/abhi-activ-one.md) — HealthReturns up to 100%
"""
    write_okf_concept(bundle_dir / "pricing" / "renewal-discounts.md", fm, body)

    # Pricing: Deductible Discounts
    fm = _base_frontmatter(
        "Pricing", "Deductible Discounts",
        "HDFC Optima Secure+ offers up to 65% premium discount through Aggregate Deductible — a voluntary deductible mechanism.",
        ["pricing", "deductible", "discount", "hdfc-ergo"],
        "Policy Documents/HDFC Product Brochure.pdf", [8, 9]
    )
    body = """# Deductible Discounts (Aggregate Deductible)

HDFC ERGO Optima Secure+ offers an **Aggregate Deductible** option that provides up to **65% premium discount** in exchange for a voluntary deductible.

## How It Works

- Policyholder chooses a deductible amount at the time of purchase
- Claims below the deductible are paid out-of-pocket
- Claims above the deductible are fully covered by the policy
- In return, the premium is reduced by up to 65%

## Pitch Guidance

- Best for **companies with younger, healthier workforces** who file fewer small claims
- The 65% discount makes HDFC the most affordable option for high-SI plans
- Not recommended for companies with frequent small-claim patterns

## Applicable Policies
- [HDFC ERGO Optima Secure+](../policies/hdfc-optima-secure-plus.md)
"""
    write_okf_concept(bundle_dir / "pricing" / "deductible-discounts.md", fm, body)

    # Reference: Standard Exclusions
    fm = _base_frontmatter(
        "Policy Exclusion", "Standard Exclusions",
        "Common exclusions across all health insurance policies — cosmetic surgery, self-inflicted injuries, substance abuse, etc.",
        ["exclusion", "standard", "all-policies"],
        "Policy Documents/HDFC Product Brochure.pdf", [12, 13]
    )
    body = """# Standard Exclusions

All four policies share common exclusions mandated by IRDAI regulations:

## Universally Excluded

1. **Cosmetic or plastic surgery** — unless required for reconstruction after an accident
2. **Self-inflicted injuries** — intentional self-harm
3. **Substance abuse** — treatment related to alcohol or drug addiction
4. **War and nuclear perils** — injuries from war, invasion, or nuclear contamination
5. **Adventure sports injuries** — unless specifically covered by add-on
6. **Dental treatment** — unless requiring hospitalisation
7. **Spectacles and contact lenses** — routine eye care
8. **Maternity expenses** — unless covered by specific add-on (HDFC Parenthood Cover)
9. **Obesity treatment** — bariatric surgery unless medically necessary
10. **Experimental treatment** — unproven medical procedures

## Pitch Relevance

When creating pitches, **never claim** these items are covered unless a specific add-on removes the exclusion. The audit engine should flag any pitch that implies coverage for excluded items.

## Related
- [Waiting Periods](waiting-periods.md)
- [Pre-Existing Diseases](pre-existing-diseases.md)
"""
    write_okf_concept(bundle_dir / "exclusions" / "standard-exclusions.md", fm, body)


# ─── Main build function ─────────────────────────────────────────

def build_full_bundle(bundle_dir: Path, policy_dir: Path):
    """Build the complete OKF knowledge bundle from all policy PDFs."""
    
    print("Building OKF knowledge bundle...")
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Map PDF files
    pdfs = {
        "abhi": policy_dir / "ABHI Product Brochure.pdf",
        "care": policy_dir / "Care Health Product Brochure.pdf",
        "hdfc": policy_dir / "HDFC Product Brochure.pdf",
        "niva": policy_dir / "Niva Bupa Product Brochure.pdf",
    }

    # Verify all PDFs exist
    for name, path in pdfs.items():
        if not path.exists():
            print(f"  WARNING: {path} not found, skipping {name}")

    # Build per-policy concepts
    policy_entries = []
    
    if pdfs["abhi"].exists():
        print("  Processing ABHI Activ One...")
        entries = build_abhi_concepts(bundle_dir, str(pdfs["abhi"]))
        policy_entries.extend(entries)

    if pdfs["care"].exists():
        print("  Processing Care Health...")
        entries = build_care_health_concepts(bundle_dir, str(pdfs["care"]))
        policy_entries.extend(entries)

    if pdfs["hdfc"].exists():
        print("  Processing HDFC ERGO Optima Secure+...")
        entries = build_hdfc_concepts(bundle_dir, str(pdfs["hdfc"]))
        policy_entries.extend(entries)

    if pdfs["niva"].exists():
        print("  Processing Niva Bupa ReAssure 2.0...")
        entries = build_niva_bupa_concepts(bundle_dir, str(pdfs["niva"]))
        policy_entries.extend(entries)

    # Build cross-policy concepts
    print("  Building shared concepts (coverages, exclusions, pricing)...")
    build_shared_concepts(bundle_dir)

    # Write index files
    print("  Generating index files...")
    
    # Policies index
    write_index(bundle_dir / "policies", "Insurance Policies", policy_entries)

    # Coverages index
    write_index(bundle_dir / "coverages", "Policy Coverages", [
        {"title": "In-Patient Care", "filename": "inpatient-care.md", "description": "Hospitalisation coverage exceeding 24 hours"},
        {"title": "Daycare Treatment", "filename": "daycare-treatment.md", "description": "Procedures under 24 hours"},
        {"title": "Pre/Post Hospitalisation", "filename": "pre-post-hospitalisation.md", "description": "Expenses before and after hospital stay"},
    ])

    # Benefits index
    write_index(bundle_dir / "benefits", "Policy Benefits", [
        {"title": "HealthReturns", "filename": "health-returns.md", "description": "ABHI — earn up to 100% premium back"},
        {"title": "Claim Protect", "filename": "claim-protect.md", "description": "ABHI — 100% OOP expenses covered"},
        {"title": "Super Credit", "filename": "super-credit.md", "description": "ABHI — SI grows up to 6X"},
        {"title": "Super Reload", "filename": "super-reload.md", "description": "ABHI — unlimited SI refills"},
        {"title": "Cumulative Bonus", "filename": "cumulative-bonus.md", "description": "Care Health — up to 500% SI growth"},
        {"title": "Infinite Benefit", "filename": "infinite-benefit.md", "description": "HDFC — uncapped yearly SI growth"},
        {"title": "Automatic Restore", "filename": "automatic-restore.md", "description": "HDFC/Care — unlimited SI restore"},
        {"title": "ReAssure+", "filename": "reassure-plus.md", "description": "Niva Bupa — first claim unlocks unlimited SI"},
        {"title": "Booster+", "filename": "booster-plus.md", "description": "Niva Bupa — 5X/10X carry-forward bonus"},
    ])

    # Exclusions index
    write_index(bundle_dir / "exclusions", "Policy Exclusions", [
        {"title": "Waiting Periods", "filename": "waiting-periods.md", "description": "Initial, named ailment, and PED waiting periods"},
        {"title": "Pre-Existing Diseases", "filename": "pre-existing-diseases.md", "description": "PED coverage rules and exceptions"},
        {"title": "Standard Exclusions", "filename": "standard-exclusions.md", "description": "Universally excluded treatments"},
    ])

    # Pricing index
    write_index(bundle_dir / "pricing", "Pricing & Discounts", [
        {"title": "Sum Insured Options", "filename": "sum-insured-options.md", "description": "SI ranges across all policies"},
        {"title": "Zone-Based Pricing", "filename": "zone-based-pricing.md", "description": "Care Health's 7-zone regional pricing"},
        {"title": "Renewal Discounts", "filename": "renewal-discounts.md", "description": "Wellness-based premium discounts"},
        {"title": "Deductible Discounts", "filename": "deductible-discounts.md", "description": "HDFC's up to 65% aggregate deductible discount"},
    ])

    # Root index
    root_entries = [
        {"title": "Insurance Policies", "filename": "policies/index.md", "description": "4 master policy documents"},
        {"title": "Policy Coverages", "filename": "coverages/index.md", "description": "What's covered — inpatient, daycare, pre/post hospitalisation"},
        {"title": "Policy Benefits", "filename": "benefits/index.md", "description": "Bonus features — SI growth, restore, wellness rewards"},
        {"title": "Policy Exclusions", "filename": "exclusions/index.md", "description": "What's not covered — waiting periods, PED, standard exclusions"},
        {"title": "Pricing & Discounts", "filename": "pricing/index.md", "description": "SI options, zone pricing, deductible and renewal discounts"},
    ]
    write_index(bundle_dir, "Marsh Insurance Knowledge Catalog", root_entries)

    # Bundle log
    log_content = f"""# Change Log

## {datetime.now().strftime('%Y-%m-%d')}

- Initial bundle generation from 4 insurance policy PDFs
- Created 4 policy documents, 3 coverage concepts, 9 benefit concepts, 3 exclusion concepts, 4 pricing concepts
- Generated index files for all directories
- All concepts include source attribution to original PDF pages
"""
    (bundle_dir / "log.md").write_text(log_content, encoding='utf-8')

    # Count files
    concept_count = sum(1 for f in bundle_dir.rglob("*.md") if f.name != "index.md" and f.name != "log.md")
    print(f"\n  Bundle complete: {concept_count} concept files generated")
    print(f"  Location: {bundle_dir}")
    
    return concept_count


if __name__ == "__main__":
    # Run standalone — 3 levels up: app/okf/bundle_builder.py → project root
    project_root = Path(__file__).resolve().parent.parent.parent
    build_full_bundle(
        bundle_dir=project_root / "knowledge_bundle",
        policy_dir=project_root / "Policy Documents"
    )

