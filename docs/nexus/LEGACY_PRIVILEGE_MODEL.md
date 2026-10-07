# Legacy Privilege Model

> Status: architectural baseline
>
> Purpose: preserve ABI v1 semantics without allowing legacy software to inherit Nexus supervisor authority.

## 1. The problem

Classic AROS exposes interfaces whose historical meaning assumes that trusted software may directly affect machine privilege.

Important examples include:

- `Supervisor()`;
- `SuperState()/UserState()`;
- `Disable()/Enable()`;
- `Forbid()/Permit()`;
- kernel.resource functions that manipulate interrupt or MMU state;
- direct PCI, MMIO, PIO and DMA operations in drivers.

On current native x86-64 AROS, these interfaces are not merely symbolic.

For example:

- `Supervisor()` can transfer execution into supervisor context;
- `SuperState()` uses `Supervisor()`;
- `Disable()` reaches `KrnCli()`;
- `Enable()` reaches `KrnSti()`;
- global mapping helpers can elevate privilege to modify the current page tables.

A protected Legacy Cell cannot retain those effects literally, because doing so would grant ABI v1 code authority over Nexus itself.

## 2. Principle

Inside a Legacy Cell:

> **legacy privilege is virtual privilege, not Nexus privilege.**

The Cell may preserve the *observable ABI contract* where practical, but it must not gain unrestricted access to the physical machine.

## 3. Privilege classes

Legacy operations are classified into four classes.

### P0 — Purely local compatibility operation

The operation affects only state inside the Legacy Cell.

Examples:

- task scheduling state;
- message ports;
- signals;
- legacy library state;
- `Forbid()/Permit()` as Cell scheduler semantics.

These remain local and should not cross into Nexus.

### P1 — Virtualised privileged operation

The operation historically affects CPU/system state but can be represented as Cell-local state.

Examples:

- virtual interrupt disable depth;
- legacy supervisor-state flag;
- Cell-local timer/scheduler inhibition.

Nexus remains physically preemptible and retains interrupt ownership.

### P2 — Mediated Nexus operation

The legacy API requests a real system action, but Nexus validates and performs it through a narrow interface.

Examples:

- reboot request;
- power-state request;
- mapping an authorised device region;
- allocating a DMA object;
- subscribing to an authorised IRQ;
- changing protection on Cell-owned memory.

The legacy caller never executes the privileged operation directly.

### P3 — Unsupported or privileged-legacy operation

Some historical software may depend on behaviour that cannot be safely virtualised without effectively giving it control of Nexus.

Examples may include:

- arbitrary CR3/CR0/CR4 writes;
- arbitrary MSR access;
- unrestricted physical-memory mapping;
- unrestricted PCI bus mastering;
- executing arbitrary caller-supplied code in real Nexus ring 0.

Such software is classified as:

- privileged legacy;
- dedicated trusted Cell;
- unsupported under protected mode;

depending on the use case.

## 4. Supervisor()

### Historical behaviour

`Supervisor(function)` may execute caller-supplied code at elevated CPU privilege on supported native targets.

This behaviour is incompatible with a security boundary if the function pointer is allowed to enter Nexus ring 0.

### Nexus rule

A normal Legacy Cell must never convert an arbitrary legacy function pointer into a Nexus privileged instruction pointer.

Instead the compatibility layer may provide one of three behaviours.

#### Mode A — virtual supervisor

For code that only checks supervisor state or depends on legacy control-flow semantics, the Cell marks the current legacy execution context as "legacy supervisor" while remaining in an unprivileged Nexus domain.

#### Mode B — recognised operation mediation

Known privileged sequences are replaced or redirected to explicit Nexus services.

#### Mode C — refusal

If arbitrary privileged execution is genuinely required, return a compatibility failure/alert or require an explicitly trusted Legacy Cell configuration.

### Non-goal

Nexus will not attempt to safely emulate every possible arbitrary x86 privileged instruction sequence solely to preserve unrestricted `Supervisor()` behaviour.

## 5. SuperState()/UserState()

These APIs should operate on Legacy Cell state.

They must not expose:

- Nexus supervisor stack pointers;
- Nexus trap frames;
- Nexus kernel virtual addresses;
- real privileged stack state.

A returned legacy supervisor token may need to become an opaque Cell-owned compatibility token internally even if the ABI still exposes an `APTR`.

The token must be validated before use.

## 6. Disable()/Enable()

### Historical problem

Current native implementations can reach physical interrupt disable/enable operations.

A Cell that could execute real `cli` indefinitely could freeze interrupt handling on a Nexus CPU.

### Nexus semantics

Inside a protected Legacy Cell:

- `Disable()` increments a Cell/vCPU interrupt-disable nesting count;
- physical CPU interrupts remain owned by Nexus;
- device/timer events destined for the Cell are marked pending;
- delivery into the Cell is deferred while its virtual interrupt state is disabled;
- Nexus may still preempt the Cell;
- `Enable()` decrements the virtual count and releases pending events when appropriate.

This preserves the useful observable property:

> legacy interrupt handlers do not run while interrupts are disabled inside the Cell

without giving the Cell control over the physical CPU's interrupt flag.

## 7. Forbid()/Permit()

`Forbid()/Permit()` are scheduler semantics, not machine privilege.

They remain inside the Legacy Cell.

A Cell task may prevent *Exec task switching inside that Cell* according to ABI v1 semantics.

It must not prevent Nexus from:

- preempting the Legacy Cell vCPU;
- running another protected process;
- servicing physical IRQs;
- running another Legacy Cell.

Therefore an infinite loop while forbidden can wedge a Cell, but not the machine.

## 8. Exception and interrupt delivery

Physical interrupt handling belongs to Nexus.

Legacy interrupt delivery becomes a virtual event path:

```
physical device IRQ
       |
       v
Nexus interrupt controller
       |
       +--> Nexus/driver service handling
       |
       +--> validated legacy event
                 |
                 v
          Legacy Cell vIRQ queue
                 |
          virtual interrupt state
                 |
                 v
            legacy handler
```

The Cell does not own the LAPIC/IOAPIC or physical IDT.

## 9. Privileged I/O instructions

A normal Legacy Cell must not execute unrestricted:

- `in/out`;
- `rdmsr/wrmsr`;
- control-register writes;
- `lidt/lgdt`;
- APIC programming.

Policy options:

- trap and mediate a defined subset;
- replace through HIDD/service adapters;
- reject unsupported access.

Direct hardware drivers are migration targets, not a permanent compatibility entitlement.

## 10. kernel.resource compatibility

Not every current `kernel.resource` entry point should survive as a direct Nexus operation.

Each API must be classified as:

- Nexus primitive;
- Legacy compatibility shim;
- service proxy;
- deprecated privileged legacy API.

See `NEXUS_EXEC_SPLIT.md`.

## 11. Restart semantics

When a Legacy Cell dies, Nexus must invalidate all state that could otherwise outlive it:

- virtual supervisor tokens;
- virtual IRQ subscriptions;
- service endpoints;
- capability handles;
- DMA grants;
- mapped device regions;
- timers.

No pointer or token from a dead Cell may become valid in a replacement Cell merely because virtual addresses are reused.

Generation-counted handles are preferred for cross-boundary objects.

## 12. Compatibility reporting

The migration SDK should eventually identify code that uses:

- `Supervisor()`;
- `SuperState()`;
- `Disable()/Enable()`;
- direct kernel.resource privilege APIs;
- direct PCI/MMIO/PIO;
- raw physical addresses.

Such software can then be classified before execution as:

- normal legacy;
- bridge-compatible;
- privileged legacy.

## 13. Required proof before protected Legacy Cell

A Legacy Cell must not be described as privilege-isolated until all are true:

- arbitrary `Supervisor()` cannot enter Nexus ring 0;
- `Disable()` cannot clear the physical CPU interrupt flag for the Cell's lifetime;
- the Cell cannot write CR3 or Nexus page tables;
- the Cell cannot install a physical IDT;
- direct device access is constrained according to the claimed isolation level.
