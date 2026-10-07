# AI and Automation Foundations

> Status: long-term architectural direction
>
> This document does not make AI a Phase 1 dependency.

## 1. Principle

Nexus should be ready for AI/agent workloads without making a language model part of the kernel.

The trusted core must remain:

- deterministic;
- small;
- model-independent;
- usable with no network;
- usable with no AI runtime installed.

An LLM is a service, not a kernel primitive.

## 2. Why prepare now

Some mechanisms useful for a modern protected OS are also ideal foundations for AI:

- asynchronous message passing;
- explicit capabilities;
- shared MemoryObjects;
- service discovery;
- accelerator abstraction;
- restartable processes.

Designing those mechanisms cleanly now avoids adding unsafe global AI privileges later.

## 3. AI service model

A future AROS AI service may expose a conventional AROS-facing interface while using Nexus mechanisms underneath.

Conceptually:

```
application
    |
AROS AI interface
    |
AI broker/service
    |
    +-- local CPU runtime
    +-- GPU/NPU runtime
    +-- remote provider
    +-- specialized model/service
```

Applications should not need to know where the model runs unless they explicitly request a provider class.

## 4. Message-oriented API

Amiga-style asynchronous communication is a natural fit.

A future request flow could conceptually support:

- request message;
- streaming text/token events;
- progress;
- tool invocation request;
- completion;
- error;
- cancellation.

The exact public API is not frozen.

The architectural requirement is that AI does not require a privileged monolithic process with unrestricted system access.

## 5. Capability-scoped agents

An AI agent should receive only the authority required for its task.

Example:

```
agent:
  read  Work:Photos/Incoming
  write Work:Photos/Sorted
  use   ImageService
  no    SYS:
  no    Secrets:
  no    arbitrary shell
```

Nexus capabilities can make this enforceable at the system boundary.

This is more important than whether the model is local or remote.

## 6. Tool calling as services

Tools should ideally be service capabilities rather than arbitrary command execution.

Examples:

- FileService;
- WandererService;
- TextEditorService;
- NetworkService;
- CalendarService;
- AudioService.

This direction has a clear Amiga precedent:

- message ports;
- libraries/devices;
- ARexx-style application interoperability.

## 7. Automation protocol

A future AROS automation protocol may provide structured commands discoverable from applications.

An application could expose actions such as:

```
TextEditor:
  Open
  Save
  Search
  Replace

Wanderer:
  OpenDrawer
  Copy
  Move
  Tag
```

The same protocol could be consumed by:

- scripts;
- human automation tools;
- AI agents.

The goal is not to replace ARexx blindly, but to preserve its strongest idea: applications should be programmable and interoperable.

## 8. Compute acceleration

Do not build an "LLM HIDD".

If a new hardware abstraction is needed, it should be generic enough for:

- GPU compute;
- NPU;
- DSP;
- future accelerators.

Conceptual operations may include:

- query capabilities;
- create compute context;
- import MemoryObject;
- submit graph/kernel;
- wait for fence/completion.

The exact HIDD/service API is intentionally deferred.

## 9. MemoryObjects

Large AI/compute data should avoid unnecessary copies.

MemoryObjects may eventually back:

- tensors;
- embeddings;
- audio;
- images;
- model buffers;
- GPU/NPU shared data.

Mapping rights remain explicit.

## 10. Local and remote providers

The system should not hard-code one provider.

Possible providers include:

- fully local model;
- local network server;
- remote hosted API;
- specialized embedded model.

Provider selection belongs in user/service policy, not in Nexus.

## 11. Privacy and observability

A future AI broker should make visible:

- which provider receives data;
- which capabilities an agent has;
- which services/tools it invoked;
- whether data leaves the machine.

Nexus should provide the enforcement primitives; the AROS runtime provides user-facing policy and UX.

## 12. Failure model

AI failure must not be system failure.

A model/service may:

- time out;
- crash;
- return invalid data;
- become unavailable;
- exceed quota.

The OS must continue functioning normally.

## 13. Non-goals

Nexus will not:

- place inference logic in the kernel;
- require an LLM to boot or administer the machine;
- give AI agents implicit root/global authority;
- couple the system ABI to one model vendor;
- delay core protection work to implement AI features.

## 14. Near-term consequence

The only near-term requirement is architectural hygiene:

- capabilities must be general enough for delegated authority;
- IPC should support asynchronous streams/events;
- MemoryObjects should support large shared data;
- service interfaces should be discoverable/versioned;
- future compute accelerators should fit the HIDD/service model.

No AI code is required in the first Nexus milestones.
