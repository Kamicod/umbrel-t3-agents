# T3 Agents for Umbrel

An Umbrel app that runs headless T3 Code in Docker with Claude Code, Codex CLI, and OpenCode. The app container keeps its own persistent home directory for T3 Connect, provider logins, MCP settings, and agent state. Projects live in a separate persistent folder.

## Install

1. In Umbrel, open **App Store → Community App Stores → Add a community app store** and add `https://github.com/Kamicod/umbrel-t3-agents`.
2. Find **T3 Agents** in the new Kamicod App Store and install it.
3. After the first start, the server is available from this tile and the T3 Connect account already linked to the migrated T3 profile.

The community store is needed because this is a personal app package, not an app in Umbrel's official store. Docker is already included with umbrelOS; Portainer is a separate management dashboard and is not needed for this app.

## Manage

Use the T3 Agents tile's app controls in Umbrel to start, stop, or restart the container. The T3 and agent data stays under the app's persistent data directory when the container is stopped or updated.

To update the image, change the app version and image tag together, push to `main`, and update the app from Umbrel. To update the CLI tools inside the persistent home, run `t3a-update` in the T3 terminal and restart the app from Umbrel.

## Configuration

MCP servers are read from Claude Code's `~/.claude.json` and mirrored to Codex and OpenCode. The MCP sync watcher runs inside the container. Secrets and login state are stored only in the app's persistent data directory; none are part of this repository or its Docker image.

The first boot installs any missing CLI tools. If a provider asks for authentication, sign in through its CLI in the T3 terminal. The T3 Connect account and T3 settings are carried over from the native Pi installation.

## Image publishing

GitHub Actions builds the ARM64 image for the Pi and publishes it to GHCR on pushes to `main` and version tags. The Docker build context is the repository root; the Dockerfile is `docker/Dockerfile`.
