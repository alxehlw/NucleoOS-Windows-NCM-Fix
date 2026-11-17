# patches/

## full-diff-complete.patch

The exact reviewed change set for the fix.

- Source: `git -C <local worktree> diff 8a5c6be..a51c571`, exported verbatim
- Size: 19,316 B
- SHA256: `bd1dff9568885aa4374e318f3a0a0a09b0c158b986894f0dc73db03dec66db61`
- Diffstat: 4 files changed, 337 insertions(+), 3 deletions(-)
- Base: `8a5c6be` (`release: v0.8.7`)
- Head: `a51c571` (`usbnet: MS OS 2.0 (WINNCM) descriptors…`)

It was cross-checked against the reviewed `final-fix.patch` from the candidate directory and is byte-identical. Nothing here was reconstructed from prose.

Apply from the NucleoOS repository root:

```
git apply --check patches/full-diff-complete.patch
```

This must be checked against `8a5c6be`. Against any other base it should fail — that failure is the expected guard, not a bug.

## What is not here

### proposal-bcddevice-0101.patch

A 1,489 B (`4237a8ae…`) proposal that changed `bcdDevice` to `0x0101`. It is **already folded into `a51c571`**, and `git apply --check` against `8a5c6be` fails at `nucleo_usbnet.c:98`. Publishing it as an applicable patch would invite someone to apply a change that is already present. The `bcdDevice = 0x0101` decision and its rationale are documented in `docs/ROOT-CAUSE-AND-IMPLEMENTATION.md` instead.

### The stale diff

`full-diff-complete.patch` also existed at 18,855 B / `b439e3d2…` during the work. It predates the final `bcdDevice` integration and is superseded by the file in this directory. Do not use the stale hash.

## Licensing

The patch modifies NucleoOS v0.8.7 source and therefore remains under **PolyForm Noncommercial License 1.0.0**, with upstream copyright held by indecenti. It is not relicensed here. See `docs/LICENSE-AND-ATTRIBUTION.md`.
