# CrisisWeave case studies

These case studies exist to make CrisisWeave's practical behaviour inspectable without pretending the prototype has already been deployed in a live emergency. Every scenario uses synthetic data and is executed by the locked end-to-end release path.

## Fragmented flood reporting

Two reports describe the same synthetic flood: one official CAP-style report and one field report. They disagree on severity and arrive twenty minutes apart. CrisisWeave should merge them into one incident while retaining two independent provenance entries, both original source identifiers, the observation window and the severity range. The combined confidence remains explicitly labelled as a ranking signal rather than a probability of truth.

This demonstrates the core editorial problem behind CrisisWeave: aggregation should reduce duplication without erasing where claims came from or making disagreement disappear.

## Stale wildfire information

Two synthetic wildfire reports both exceed the severity and confidence thresholds for an alert. One is four hours old and the other is thirty minutes old. The rule sets max_age_hours to two and evaluates both at a fixed time. Only the recent report is allowed to trigger the alert.

This is deliberately deterministic. The release artifact records the rule, both inputs, the evaluation time and the resulting alert so the safeguard can be checked rather than merely described.

## Recovery coordination

The recovery case uses explicit synthetic worksites, not inferred jobs. A hazard report never becomes a cleanup task simply because it is nearby. The operational worksite is assigned atomically to a synthetic team, while the public projection removes the assigned team, coordinator instructions and free-form description.

This demonstrates the separation between crisis information and operational recovery work, and the separation between internal coordination data and information safe enough for a public or volunteer-facing surface.

## Reproduce the results

Run bash demo.sh or ./demo.ps1. The locked E2E writes machine-readable inputs and outputs to artifact/case-studies/, including index.json and RESULTS.md.

These scenarios are suitable for explaining and testing the prototype. They are not field validations, outcome studies or evidence that CrisisWeave is currently used by an emergency service or humanitarian organisation.
