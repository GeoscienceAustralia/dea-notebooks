### Proposed changes
Include a brief description of the changes being proposed, and why they are necessary.

### Closes issues (optional)
- Closes Issue #000
- Closes Issue #000

### Checklist (replace `[ ]` with `[x]` to check off)
- [ ] Notebook created using the [DEA-notebooks template](https://github.com/GeoscienceAustralia/dea-notebooks/tree/develop)
- [ ] Remove any unused Python packages from `Load packages`
- [ ] Remove any unused/empty code cells
- [ ] Remove any guidance cells (e.g. `General advice`)
- [ ] Ensure that all code cells follow the [PEP8 standard](https://www.python.org/dev/peps/pep-0008/) for code. The `jupyterlab_code_formatter` tool can be used to format code cells to a consistent style: select each code cell, then click `Edit` and then one of the `Apply X Formatter` options (`YAPF` or `Black` are recommended).
- [ ] Include relevant tags in the final notebook cell (refer to the [DEA Tags Index](https://docs.dea.ga.gov.au/genindex.html), and re-use tags if possible)
- [ ] Clear all outputs, run notebook from start to finish, and save the notebook in the state where all cells have been sequentially evaluated
- [ ] Test notebook on both the `NCI` and `DEA Sandbox` (flag if not working as part of PR and ask for help to solve if needed)
- [ ] If applicable, update the `Notebook currently compatible with the NCI|DEA Sandbox environment only` line below the notebook title to reflect the environments the notebook is compatible with


