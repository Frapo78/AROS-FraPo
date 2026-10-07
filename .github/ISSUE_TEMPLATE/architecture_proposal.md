---
name: Nexus architecture proposal
about: Propose a change to a Nexus architectural invariant or subsystem boundary
title: '[Architecture] '
labels: ''
assignees: ''
---

## Problem

What concrete architectural problem are you trying to solve?

## Current limitation

Which current Nexus assumption, AROS behaviour or hardware constraint creates the problem?

## Proposed change

Describe the smallest architectural change that solves it.

## Compatibility impact

How does this affect:

- ABI v1:
- protected AROS:
- selective Legacy Cells:
- m68k compatibility:
- upstream mergeability:

## Trust / isolation impact

Which isolation levels are affected?

- L0
- L1
- L2
- L3
- L4
- L5

Does this add code to the Nexus trusted computing base?

## Alternatives considered

List meaningful alternatives and why they are weaker.

## Falsifiable proof

What future experiment or test would demonstrate that the proposal works?

What result would demonstrate that it is wrong?

If no executable test is currently possible, apply **NO TEST, EXPLAIN WHY** and identify the prerequisite needed for a future test.

## Verification gate

- Expected evidence class E0-E7:
- Human gate H0/H1/H2/H3:
- Real hardware required?

## ADR

If accepted, which ADR should be added or superseded?
