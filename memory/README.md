# Understanding memory

Consider, we want to run large computations using finite resources
(including supercomputers such as NCI Gadi, or cloud virtual machine clusters
such as AWS EC2).
Often jobs are more constrained by memory than CPUs.
We want to run as many tasks per node as will fit in memory, but no more.
Hence, we need to know how to assess this accurately.

Often reported memory usage appears inexplicably large,
and tends to grow monotonicly (until something is terminated),
seemingly out of relation with the expected usage pattern.
Resolving this is the path to minimising resource costs.


## Address space

User software does not directly index into the physical memory
(the volatile storage, i.e. RAM).
Instead, each process has its own address space.
(The CPU translates addresses to physical memory locations on the fly,
using page tables managed by the kernel.)
The process must only read or write to those address ranges for which it has
obtained permission.
The virtual memory size is a measure of how much address space to which a
process currently has access.

Address space is usually a much more plentiful resource than physical memory.
(several thousand PB for each process.)
This facilitates having mmore than two growable areas of memory,
without collisions occuring before the physical memory is exhausted.
(Growable areas include: the traditional heap, the area for new memory maps,
and each individual thread's stack.)

Usually each page is 4KB.
This means fragmentation (space-inefficient packing sequences) should not
waste physical memory (except for small allocations).

Not all of the allocated virtual memory occupies physical memory.
For example, it is possible for a file
(potentially larger than the physical memory capacity)
to be mapped onto the address space,
and for the kernel to defer reading any blocks into memory until the process
attempts to use them,
or to swap pages out again (in anticipation that the process might have
finished accessing those blocks).
The resident set size (RSS) measures how much of the virtual memory for a
process is currently represented in physical memory.
Note that some areas of physical memory (e.g., libraries) can be shared
between concurrent processes (even from unrelated applications).
Some systems are able to report on unique and proportional sets (accounting
for sharing), and some can report on working sets (the subset of pages that
the process is accessing nearly at present).

## Cache

The kernel uses free memory as a storage cache, to improve IO latency.
That is, it speculatively prefetches data that is likely to be read soon
(assuming sequential access patterns), or delays purging to disk (in case
of further modification).

As such, hardly any physical memory may be truly unused.
Cache can generally be relinquished, on demand,
to service new allocation requests.
However, insufficient cache may dramatically impair performance
(especially for interactive tasks).

This simply means that if reported free memory is scarce,
but reported cache is substantial, then there is no problem.

Note, there is also a very small amount of memory cache in the CPU,
so that the CPU is less interrupted by latency accessing the main RAM.
Consequently, some calculations can be made faster if arranged so as to
complete all operations on each tiny chunk of memory
before starting on the next.

## Dynamic allocations

In most compiled languages, while the stack area is used for storing
local variables, the heap is the memory area for all longer lived objects
which are dynamically created and discarded.
(Examples include arrays returned by the function that produces them.)
The language expects each basic object (such as a variable or array)
to be located in a continuous address range interval.
The heap is susceptible to fragmentation.
(For example as a program replaces objects,
freeing and re-allocating for them, then,
even if the sum total of the program's allocation demands does not exceed
a previous high water mark,
the heap may still need to continue growing if,
due to packing order,
the freed gaps are not contiguous.)


The heap is specific to the process, not shared across the system.
The low level functions to allocate (or to subsequently free) space in the heap
are implemented in the C runtime libraries, which execute as part of the
user process.
Traditionally, these functions were implemented using (sbrk) calls to adjust the
length of the data segment memory area that is allocated to the process by the
kernel.
Alternatively, implementations may make calls for the kernel to establish
("anonymous" rather than file-backed) memory mappings.


## Python memory management

Allocating memory is generally considered slow.

## Conclusion


Other than the kernel,


RSS (resident set size is how much RAM a process occupies. Excludes anything
paged out to swap or not yet loaded. (Note VDI has no swap, according
to "free" command.) Distinct from USS (unique) or PSS (proportional), differing
from RSS in the inclusion of shared memory (that leads to double counting).

Virtual size - basically address space, which may be more plentiful resource
than memory. Includes much that is not currently in RAM. Presumably each
process will have its own virtual address space. Segments will be occupied for
the code ("text") and global variables, and growable areas for the stack of
each thread, the heap, and mmaps. (Since there are more than two growable
elements in the one-dimensional space, a collision may occur long before it is
fully exhausted.)

Caching - any available physical memory may be tentatively purposed for
(disk file) caching by the operating system. This isn't necessarily
unavailable if a process wants memory, although some may be, and
performance would suffer if there was no space left for caching.

Malloc is implemented in the C library. It uses system calls, either mmap
(mapping some process-private anonymous address-space) or brk (adjusting the
size of the process's data segment or heap). The latter is only used on some
systems, and mostly for smaller allocations. The algorithm for malloc is
probably not hurried about relinquishing memory.


Nested memory managers..