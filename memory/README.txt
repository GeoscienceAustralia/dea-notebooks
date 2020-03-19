Understanding memory.

Consider, we want to run large tasks on Gadi/NCI. Often jobs are mor
constrained by memory than CPUs. Want to run as many tasks per node as will
fit in memory, but no more. Hence, want to know how to assess this accurately.



RSS - Resident swap size is how much RAM a process occupies. Excludes anything
      paged out to swap or not yet loaded. (Note VDI has no swap, according
      to "free" command.)

      Distinct from USS (unique) or PSS (proportional), presumably RSS includes
      shared memory (leading to double counting).

Virtual size - basically address space, which may be more plentiful resource
      than memory. Includes much that is not currently in RAM.