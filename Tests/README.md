# Tests

This folder contains tests that are run against notebooks in this repository to ensure they are working correctly.

Tests are run via Github actions using a small test database containing a small subset of datasets from the main DEA Sandbox datacube database.

## Add integration tests for notebook

For notebook requiring product and data not currently available in the integration test db, please add indexing instruction to `Tests/index_additional_data.sh`.

This is to allow development flexibility: once the test is fully functional, please reach  out to a maintainer to have additional data included in the base database.