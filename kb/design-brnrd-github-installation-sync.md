# brnrd GitHub installation sync

Status: active design after [`decision-brnrd-repo-first-model.md`](decision-brnrd-repo-first-model.md)

## Problem

GitHub login and GitHub App installation are different flows.

GitHub login answers:

```text
Who is this user?
```

GitHub App installation answers:

```text
Which repositories can brnrd access as an installed app?
```

The dashboard must not ask users to paste repository names or installation ids as the main path. It should sync the installation repositories and let the user connect them as brnrd repos.

## Required settings

```text
BRNRD_GITHUB_APP_ID
BRNRD_GITHUB_APP_PRIVATE_KEY_B64
BRNRD_GITHUB_APP_SLUG
BRNRD_GITHUB_BOT_LOGIN
BRNRD_GITHUB_WEBHOOK_SECRET
```

`BRNRD_GITHUB_APP_PRIVATE_KEY_B64` stores the GitHub App PEM key as base64 so deployment env vars do not have to preserve newlines.

## Flow

```text
GitHub redirects to /api/github/setup with installation_id
  -> brnrd stores or updates GitHubInstallation
  -> brnrd signs a GitHub App JWT
  -> brnrd requests an installation access token
  -> brnrd calls GET /installation/repositories
  -> brnrd upserts GitHubInstalledRepo rows
  -> dashboard shows those repos as available to connect
```

Installation webhooks should run the same sync path for app installs and repository-selection changes.

## Tables

```text
github_installations
  id
  account_id
  installation_id
  target_login
  target_type
  created_at
  last_synced_at

github_installed_repos
  id
  github_installation_id
  repo_full_name
  forge_repo_id
  is_private
  default_branch
  last_seen_at
```

These tables represent what GitHub says the app can see. They are not the same as brnrd's durable `repos` table.

## Reconciliation

For each installed GitHub repository:

```text
if Repo exists for account + repo_full_name:
  show as connected
else:
  show as available with a Connect action
```

Connecting creates a brnrd `Repo`. Daemons, Telegram routes, GitHub comments, and future runtime dispatch all route through that Repo.

## Dashboard implication

The dashboard should have two repo sections:

```text
Connected repos
  repos already known to brnrd

Available from GitHub
  repos synced from GitHub App installation
```

Manual repo entry can remain as an advanced/debug fallback, but not the normal onboarding path.
