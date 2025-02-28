<!--- ⭐ This is a template you can follow to help construct a good pull request! --->

### Proposed changes
Include a brief description of the changes being proposed, and why they are necessary.

### Closes issues (optional)
- Closes Issue #000

### Checklist
<!--- (Replace `[ ]` with `[x]` to check off) --->

If this is a notebook, then have you: 
- [ ] Checked the structure of the notebook follows our [DEA-notebooks template](https://github.com/GeoscienceAustralia/dea-notebooks/wiki/NotebookTemplate)
- [ ] Removed any unused Python packages from `Load packages`
- [ ] Removed any unused/empty code cells
- [ ] Removed any guidance cells (e.g. `General advice`)
- [ ] Ensured that all code cells follow the [PEP8 standard](https://www.python.org/dev/peps/pep-0008/) for code. The `jupyterlab_code_formatter` tool can be used to format code cells to a consistent style: select each code cell, then click `Edit` and then one of the `Apply X Formatter` options (`YAPF` or `Black` are recommended).
- [ ] Included relevant tags in the final notebook cell (refer to the [DEA Tags Index](https://knowledge.dea.ga.gov.au/genindex/), and re-use tags if possible)
- [ ] Tested notebook on the [DEA Sandbox](https://knowledge.dea.ga.gov.au/guides/setup/Sandbox/sandbox/)
- [ ] Cleared all outputs, run notebook from start to finish, and save the notebook in the state where all cells have been sequentially evaluated
- [ ] If applicable, update the `Notebook currently compatible with` line below the notebook title to reflect the environments the notebook is compatible with
- [ ] Check for any spelling mistakes using the DEA Sandbox's built-in spellchecker (double click on markdown cells then right-click on pink highlighted words). For example:

![sandbox_spellchecker](https://github.com/GeoscienceAustralia/dea-notebooks/assets/17680388/c5e5848b-fd54-4eb5-aae9-29838761f2af)

<!--- 
⭐ Did you get stuck? These might help: 
- https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Getting-started-with-Git
- https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Create-a-DEA-Notebook
- https://github.com/GeoscienceAustralia/dea-notebooks/wiki/Edit-a-DEA-Notebook
--->