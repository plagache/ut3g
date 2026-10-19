# Difference

Old:
the allocator owned a ring of bounce buffers, those buffers are GPU-owned sysmem exposed to the host as an MMIOInterface cpu_view.
That's why the pipeline work with zero host→GPU mapping: disk read loop fills the bounce buffer (host road), SDMA DMAs bounce → VRAM.

New:
staging moved from the allocator into the copy pattern
layer (stage_copy); _staging is a single preallocated buffer on the plain CPU device, sliced into 2 slots of 64 MiB.

## Answer

1. Client sends RPC MAP_SYSMEM_FD size=… contiguous=…
2. The TinyGPU app/dext allocates size bytes of host RAM and wires them into the GPU's page tables — it returns the physical address list (paddrs) that the GPU MM can map at a chosen GPU VA.
3. It hands the client back the same fd over the socket (SCM_RIGHTS). The client mmaps it and gets paddrs by reading the (paddr,size) pairs written into the front of the mapping itself.
4. The client then does dev_impl.mm.map_range(vaddr, size, [(paddr, 0x1000)…], aspace=AddrSpace.SYS) — that's the GPU-side view.

## Result
one block of memory, two views — the CPU pokes it through the mmap'd fd, the GPU reads it through its own page table. No per-byte RPC for the GPU to see host data. That's the property upstream
shorthand calls "GPU-owned sysmem": the dext created it and it's the only kind of host memory the GPU can touch on your setup.

(Minor naming footnote: MMIOInterface is a bit of a misnomer here — it's a uniform "address window" object with typed read/write/view; it's used for real MMIO BARs and for these sysmem mappings and —
most interestingly — its subclass RemoteMMIOInterface, where every __getitem__/__setitem__ is a socket RPC round-trip. Same API regardless of which side of the wire the bytes physically sit on.)

## Solution
sysmem hop at Buffer.copy_from — fork-only, zero hcq2 churn

Route through Buffer.copy_from (device.py:228) — every direction funnels there (run_linear, allocated src, eager).

- host→card (CPU/DISK/NPY → AMD): take a card-sysmem scratch buffer (cached; one big 128 MiB Buffer + Buffer.view(n, off) slices, or a small size-keyed cache given MAX_SYSMEM cap), fill its client view:
- CPU/NPY: plain host memcpy,
- DISK: src.allocator._copyout(stage_view, src) — reuse the existing FileIO loop (old-world bounce, verbatim behavior),
then a card→card UOp copy sysmem_view → dst (GPU-VA on both ends; lands on SDMA if has_copy_queue, else the copy-program path — both fine).
- card→host (AMD → CPU/DISK/NPY): UOp copy src → sysmem scratch (GPU writes inside GPU-VA — no mapping problem), then host memcpy out of the client view into the CPU buffer.
