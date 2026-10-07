# Contributing to AROS-FraPo / Nexus

This repository is an experimental fork of AROS used to develop and test the Nexus architecture.

The rules in this section apply to Nexus work in this fork. The original upstream AROS contribution guidance is preserved below because Nexus intends to remain compatible with upstream coding and testing practices.

## Where a contribution belongs

### Nexus architectural work

Use this repository when the change is specifically related to:

- Nexus address spaces;
- Legacy Cell containment;
- protected execution;
- privilege virtualization;
- fault isolation;
- capability/IPC work;
- driver-domain work;
- Nexus-specific tests, tooling or documentation.

Target `nexus/main` through a focused feature branch or pull request.

### General AROS fixes

If a change is independently useful to normal AROS and does not depend on Nexus, contributors are encouraged to consider submitting it to the upstream AROS Development Team as well.

Nexus should not maintain a private copy of a generally useful AROS fix without a good reason.

## Before coding

For non-trivial Nexus changes, the mandatory process in `docs/nexus/REVIEW_PROTOCOL.md` applies.


1. read `docs/nexus/VISION.md`;
2. read the relevant architecture documents and ADRs;
3. find or open a GitHub Issue for the concrete task;
4. describe any change to an architectural invariant before implementing it.

Use GitHub Discussions for broad design conversations and Issues for work that can be completed and tested.

## Pull request rules

A Nexus pull request may not be considered ready until three distinct review passes have been documented: correctness/scope, regression/integration, and adversarial red-team.

A Nexus pull request should:

- contain one logical change;
- identify the related issue;
- state the upstream baseline used;
- state the tested target(s);
- state the highest isolation level actually demonstrated, where relevant;
- describe failure/recovery behaviour;
- include a regression test or reproducible verification whenever practical;
- avoid unrelated formatting/refactoring;
- preserve ABI v1 unless the PR explicitly documents a compatibility impact.

For low-level work, include the exact QEMU or hardware test environment when possible.

## Architecture review

Changes to any of the following should normally update or reference an ADR:

- protection boundary;
- trust model;
- ABI contract;
- privilege model;
- address-space ownership;
- scheduler ownership;
- IPC/capability semantics;
- hardware/DMA ownership.

A large implementation is not a substitute for an architectural explanation.

## Merge policy

The upstream AROS rule requiring sign-off from two upstream core developers applies to the upstream AROS project, not automatically to this experimental fork.

For Nexus, changes should be merged only after:

- the relevant tests pass;
- the architectural impact is understood;
- the change is small enough to review;
- known limitations are documented.

As the contributor base grows, this policy should evolve toward independent review rather than relying on a single maintainer.

## Coding style and portability

Nexus inherits the AROS coding conventions unless a Nexus-specific document explicitly says otherwise.

In particular:

- use Unix LF line endings;
- isolate architecture-specific code;
- consider 32/64-bit and LE/BE assumptions;
- do not introduce unnecessary compiler-specific behaviour;
- keep changes upstream-mergeable where practical.

---

# Upstream AROS contribution guidance

The following is preserved from the upstream repository and remains useful for coding style, portability and the process used when contributing changes back to AROS.

## Applying for access

In the first instance you should show interest in the project by forking and providing pull requests
for patches to improve AROS. You should also join the [slack channel](https://arosdevteam.slack.com) or developer mailing list, and request to officially
join the GitHub organization if you are interested in being directly involved in the project, or would
like to collaborate.

## Contributions

When contributing to this repository, please first discuss the change you wish to make on the 
developer mailing list in the first instance, and via issue, email, or any other method with
the core developer team of this repository before making a change. For small fixes and straightforward
changes, prior discussion may not be necessary, but contributors are encouraged to ask if they are
unsure about the appropriate approach.

Please keep contributions focused on a single logical change where possible, and avoid including
unrelated formatting, refactoring, or other changes in the same pull request.

Please note we have a code of conduct, please follow it in all your interactions with the project.

### Pull Request Process

1. Ensure any code that is not derived from an external source follows the [AROS coding conventions](http://developers.aros.org/documentation/styleguide.html).
   C and header source files should use Unix (LF) line endings, consistent with those conventions
   and the repository's `.astyle` configuration.
   Take special care when tidying MUI UI source layouts: the `.astyle` configuration can mangle
   these layouts, so verify that they have not been malformed.

2. Update the AROS copyright notice year in any modified source files where a copyright notice is
   present. Do not modify copyright notices in files derived from external sources unless required
   by their applicable licensing terms.

3. Make sure to bump the version numbers in any modules where required and update the appropriate
   README or other documentation if applicable.

4. Build the affected components and run any relevant tests before submitting the pull request.
   Bug fixes should, where practical, include a regression test or provide details of how the
   problem was reproduced and how the fix was verified.

5. Test changes on different AROS targets where practical. In particular, changes should be tested
   on different combinations of 32-bit and 64-bit, and big-endian (BE) and little-endian (LE)
   targets where the affected code supports them.

   At a minimum, contributors should consider the following target combinations:

   * 32-bit little-endian (LE)
   * 64-bit little-endian (LE)
   * 32-bit big-endian (BE)
   * 64-bit big-endian (BE)

   It is understood that contributors may not have access to every target. If a change cannot be
   tested on all relevant targets, please state which targets were tested and which could not be
   tested in the pull request.

   Take particular care with code that may be affected by architecture differences, including
   pointer sizes, integer sizes, structure layout and alignment, ABI details, and byte order.
   Do not assume that all AROS targets have the same pointer size, alignment requirements,
   structure layout, or endianness.

6. Check that the change does not introduce unnecessary compiler-specific behaviour or assumptions
   about the underlying architecture. Architecture-specific code should be clearly identified
   and isolated where practical.

7. Update documentation, examples, or other supporting files where a change affects user-visible
   behaviour, interfaces, configuration, or developer usage.

8. Ensure that the pull request description clearly explains what the change does, why it is
   required, and how it was tested. Where relevant, include the AROS targets on which the change
   was tested and identify any known limitations or untested targets.

9. You may merge the Pull Request in once you have the sign-off of two core developers, or if you 
   do not have permission to do that, you may request a core developer review and merge it for you.

### Code of Conduct

#### Our Pledge

In the interest of fostering an open and welcoming environment, we as
contributors and maintainers pledge to making participation in our project and
our community a harassment-free experience for everyone, regardless of age, body
size, disability, ethnicity, gender identity and expression, level of experience,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

#### Our Standards

Examples of behavior that contributes to a positive environment include:

*   Using welcoming and inclusive language

*   Being respectful of differing viewpoints and experiences

*   Gracefully accepting constructive criticism

*   Focusing on what is best for the community

*   Showing empathy towards other community members

Examples of unacceptable behavior by participants include:

*   The use of sexualized language or imagery and unwelcome sexual attention
    or advances

*   Trolling, insulting/derogatory comments, and personal or political attacks

*   Public or private harassment

*   Publishing others' private information, such as a physical or electronic
    address, without explicit permission

*   Other conduct which could reasonably be considered inappropriate in a
    professional setting

#### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable
behavior and are expected to take appropriate and fair corrective action in
response to any instances of unacceptable behavior.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct, or to ban temporarily or
permanently any contributor for other behaviors that they deem inappropriate,
threatening, offensive, or harmful.

#### Scope

This Code of Conduct applies both within project spaces and in public spaces when
an individual is representing the project or its community. Examples of
representing a project or community include using an official project e-mail
address, posting via an official social media account, or acting as an appointed
representative at an online or offline event. Representation of a project may
be further defined and clarified by project maintainers.

#### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by contacting the project team (contact information can be found [here][contact]). All
complaints will be reviewed and investigated and will result in a response that
is deemed necessary and appropriate to the circumstances. The project team is
obligated to maintain confidentiality with regard to the reporter of an incident.
Further details of specific enforcement policies may be posted separately.

Project maintainers who do not follow or enforce the Code of Conduct in good
faith may face temporary or permanent repercussions as determined by other
members of the project's leadership.

#### Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage], version 1.4,
available at [http://contributor-covenant.org/version/1/4][version]

[contact]: http://www.aros.org/contact.html
[homepage]: http://contributor-covenant.org
[version]: http://contributor-covenant.org/version/1/4/
