# Shadow Ecology governance-boundary register

**Version:** 1.0  
**Date:** 2026-09-24  
**Applies to:** Lower Walker River-Walker Lake terminal-basin study area

## Purpose

This register distinguishes public desktop analysis from activities that need
consultation, agreement, or authorization. It is a project operating policy,
not a legal determination of jurisdiction, data ownership, or consultation
obligations. It does not substitute for a data-sharing agreement, research
agreement, or a Tribe's own governance requirements.

## Governance entities in scope

| Entity or program | Relationship to the selected study area | Project status | Required treatment |
|---|---|---|---|
| **Walker River Paiute Tribe** | Primary counterpart. The selected corridor includes the Walker River Paiute Reservation and waters connected to the Walker River, Weber Reservoir, and the Walker Lake confluence. | **Primary consultation counterpart** | Invite early consultation before interpreting or disseminating place-specific findings on Reservation lands or waters. Obtain written agreement before requesting, receiving, using, or retaining Tribe-supplied data, contextual knowledge, site locations, or review input. |
| **Walker River Environmental Department/Water-resource and public-utilities programs** | Public sources document established environmental and water-management programs; their current priorities and data holdings must not be inferred from public material. | **Primary program-level contact pathway** | Ask the Tribe which office or designated representative should receive the project description. Do not assume a public agency page, historic staff listing, or federal contact is authorization to engage or share data. |
| **Yerington Paiute Tribe** | Relevant upstream/contributory context near the Wabuska-Mason Valley transition. Public documentation describes water-quality and groundwater concerns in its area. | **Secondary consultation counterpart** | Begin with public data only. Consult before producing place-specific findings that concern Yerington Paiute lands, using Tribe-supplied information, or extending the final study boundary upstream to its lands or waters. |
| **USGS Nevada Water Science Center; Nevada Division of Water Resources; EPA Region 9; Bureau of Indian Affairs; Bureau of Reclamation** | Public-data stewards, monitoring partners, and/or water-management agencies relevant to the system. | **Public-source/coordination entities** | Cite and document public datasets and metadata. Agency data do not substitute for Tribal data or authority; agency staff cannot grant permission to use Tribal-sourced data. |

## Data and information categories

| Category | Examples | May enter public repository or publication? | Conditions |
|---|---|---|---|
| **P1: Public, general-use data** | Sentinel-2 and Landsat imagery; NLCD; USGS/NWIS observations; public agency reports; public monitoring metadata; public boundaries used only as desktop context | Yes, subject to source licenses and metadata | Cite source, date, access method, processing, and known limitations. A public boundary is not treated as a definitive statement of sovereignty or jurisdiction. |
| **P2: Public data with place-specific sensitivity** | Public well coordinates, public monitoring records, or project-derived residual clusters located on or immediately adjacent to Tribal lands/waters | Not automatically | Maintain source terms. Before external release of maps that rank, flag, or characterize areas on or immediately adjacent to Tribal lands/waters, offer the relevant Tribe an opportunity to review the intended interpretation and map scale. |
| **R1: Partner-shared restricted data or context** | Non-public monitoring data; site locations; local observations; program priorities; review comments; interpretation supplied by a Tribal partner | No, unless written terms explicitly allow it | Use only under written terms specifying purpose, access, security, retention, attribution, derivative products, review, and withdrawal/disposition provisions. Store outside public Git and restrict access. |
| **R2: Sensitive information** | Cultural resources; sacred or restricted locations; personally identifying information; sensitive infrastructure; information designated confidential by a partner | No | Do not solicit or collect unless there is a separately approved need and explicit written governance pathway. Do not attempt inference from imagery or public proxies. |

## Permitted work before consultation

The following may proceed using P1 data only:

- Build a reproducible imagery and public-hydrography data pipeline.
- Train and spatially validate land-cover models under the frozen protocol.
- Calculate residual fields, spatial statistics, and null-model results.
- Map public monitoring coverage as an **agency/public-record coverage layer**.
- State only that public records have specified spatial/temporal coverage; do
  not describe that coverage as total monitoring capacity or local knowledge.

The following are not permitted before consultation or written agreement:

- Requesting or collecting non-public monitoring data, site locations, or local
  ecological/hydrologic knowledge.
- Representing a result as a Tribal monitoring gap, Tribal priority, or Tribal
  interpretation without consultation.
- Publishing a map or ranked intervention/field-validation list that singles
  out locations on or immediately adjacent to Tribal lands/waters without first
  offering contextual review to the relevant Tribe.
- Conducting field work, installing sensors, sampling, or using drone imagery
  on Tribal lands or waters without the applicable written permission.

## Consultation and release workflow

1. **Early project notice:** Send a short, nontechnical project description,
   focal-area map, public-data inventory, and statement that no Tribal data are
   being requested at this stage. Ask whether the Tribe wishes to engage and
   which office/designated representative is appropriate.
2. **Scoping conversation, if welcomed:** Ask about priorities, concerns,
   appropriate map scales, whether any public-data interpretation should be
   avoided, and whether the project could be useful. Record only what the
   partner agrees may be retained.
3. **Written terms before R1/R2 information:** Agree on purpose, data fields,
   users, security, retention/deletion, derivative products, review period,
   attribution, publication, and withdrawal terms.
4. **Interpretation review:** Before external dissemination of place-specific
   results affecting Tribal lands/waters, provide a plain-language summary,
   methods, proposed maps, uncertainty/confounder analysis, and reasonable
   review time. Incorporate agreed corrections; document any unresolved
   interpretive difference rather than presenting it as consensus.
5. **Release decision:** Publish only material permitted by data terms and
   review arrangements. Aggregate, mask, defer, or omit sensitive products as
   required.

Consultation does not obligate a Tribe to participate, share information, endorse the project, 
or accept the project's interpretations.

## Evidence and source notes

- EPA documents that the Walker River Paiute Tribe received Clean Water Act
  Treatment as a State authority and describes the Walker River Environmental
  Department and the Tribe's waters in this system: [EPA, 2016](https://www.epa.gov/archive/epa/newsreleases/walker-river-paiutes-develop-tribal-water-quality-standards.html).
- EPA's 2025 Tribal Clean Water Act workshop includes a Walker River Paiute
  Tribe nonpoint-source-program presentation: [EPA workshop page](https://www.epa.gov/tribal-pacific-sw/2025-tribal-clean-water-act-cwa-workshop).
- EPA documents the Yerington Paiute Tribe's water-quality monitoring program
  and the sensitivity of its groundwater context: [EPA accomplishments report](https://www.epa.gov/sites/default/files/2015-08/documents/tribal-water-quality-accomplishments.pdf).
- USGS identifies a Walker River monitoring location operated in cooperation
  with the Walker River Paiute Tribe: [USGS monitoring location](https://waterdata.usgs.gov/monitoring-location/USGS-10302025/).

## Review and amendment log

| Version | Date | Change | Status |
|---|---|---|---|
| 1.0 | 2026-09-24 | Initial entity, data-classification, and engagement boundaries | Internal draft; review before outreach |
