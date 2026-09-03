# Setup — Mark's Contribution Run

This package is ready for the GitHub profile repository `MarkMax29/MarkMax29`.

## Files

```text
MarkMax29/
├── README.md
├── assets/
│   └── contribution-run.svg
├── scripts/
│   └── generate_contribution_run.py
└── .github/
    └── workflows/
        └── contribution-run.yml
```

## What happens automatically

The workflow runs:

- when you first push the generator/workflow files;
- once every day at 02:17 UTC;
- whenever you manually click **Run workflow** in GitHub Actions.

It reads your public GitHub contribution calendar through GitHub's GraphQL API, regenerates `assets/contribution-run.svg`, and commits the new SVG back to the profile repository.

## First upload

Upload the whole folder structure to the root of `MarkMax29/MarkMax29` and commit it to `main`.

The included SVG is a demo so the README looks complete immediately. On the first successful workflow run it is replaced by a version generated from your real contribution calendar.

## If the Action says it cannot push

Open:

`Repository → Settings → Actions → General → Workflow permissions`

Select **Read and write permissions** and save, then run the workflow again from the **Actions** tab.

## Important limitation

GitHub does not allow changing the native contribution graph shown by GitHub itself. This solution renders a custom, animated copy of your real contribution calendar inside the profile README.
