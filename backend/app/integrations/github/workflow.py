PR_TITLE = "Add BOMWatcher AI-BOM scan"
COMMIT_MESSAGE = "Add BOMWatcher AI-BOM scan workflow"
PR_BODY = (
    "This PR adds `.github/workflows/bomwatcher-scan.yml`.\n\n"
    "On every push to the default branch it generates a CycloneDX AI Bill of Materials "
    "(dependencies + AI models) **on GitHub's runners, using your Actions minutes**, and uploads it "
    "as a build artifact that BOMWatcher reads. Your source code never leaves GitHub.\n\n"
    "The workflow only has `contents: read` permission. Merge to start scanning; delete the file to stop."
)


def render_workflow(default_branch: str, action_ref: str) -> str:
    return f"""# Added by BOMWatcher. Generates a CycloneDX AI-BOM on GitHub's runners;
# your source code never leaves GitHub. Delete this file to stop scanning.
name: BOMWatcher scan

on:
  push:
    branches: ["{default_branch}"]
  workflow_dispatch:
permissions:
  contents: read

jobs:
  scan:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - uses: {action_ref}
"""
