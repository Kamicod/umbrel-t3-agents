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

## Sellbird

The store also carries **Sellbird**, an open-source cold-email agent ([ethanplusai/sellbird](https://github.com/ethanplusai/sellbird), AGPL-3.0), packaged from unmodified upstream source.

- The image is built from `docker/sellbird/` by the `Publish Sellbird container` workflow, which also smoke-tests it. The upstream commit is pinned in `docker/sellbird/Dockerfile` (`SELLBIRD_REF`).
- Sellbird's dashboard only answers on `127.0.0.1:5555`, so the image runs a small Caddy proxy on port 8080 in front of it. The dashboard's token check is unchanged.
- The dashboard token is the app's default password, shown by Umbrel. Paste it into the "Dashboard locked" box, or open `http://umbrel.local:5555/#token=<password>`.
- The AI runs through the Claude CLI and reuses the T3 Agents app's Claude login (`data/home/.claude`), so T3 Agents must be installed and signed in.
- Config, knowledge files and the database live in the app's `data` folder.
- Run one-off commands from the Pi with `sudo docker exec -it kamicod-sellbird_server_1 python -m sellbird <command>`, for example `setup` or `train <url>`.
- Sending stops when the container restarts. Start it again from the dashboard's Actions card.

To update Sellbird, change `SELLBIRD_REF`, the `VERSION` in the workflow, and the version and image tag in `kamicod-sellbird/`, then push to `main`.

## Hindsight

The store also carries **Hindsight** ([vectorize-io/hindsight](https://github.com/vectorize-io/hindsight), MIT), a long-term memory server with an MCP endpoint, using the official `ghcr.io/vectorize-io/hindsight:<version>-slim` image (no ML models in the container).

- **LLM:** Haiku 5.5 on the Claude plan, through the T3 Agents app's `claude-api` endpoint (`kamicod-t3-agents_server_1:8787`, a key in `~/claude-api/keys/`). T3 Agents must be installed and signed in.
- **Embeddings:** the `embed` container serves hs-embed-1 as an int8 ONNX model (about 150 MB) on an OpenAI-compatible `/v1/embeddings`. The model files are not in this repository; copy `model_int8.onnx` and `tokenizer.json` into the app's `data/embed/model/`. The container installs its Python packages once into `data/embed/deps` and waits until the model is there.
- **Decisions and reranking:** Cloudflare Workers AI (Clef-flash) for consolidation, OpenRouter's free decider for reflect, and NVIDIA's free Nemotron reranker, falling back to OpenRouter and then to plain fused ranking (`rrf`).
- **Secrets:** provider keys and the API key live only in the app's `data/secrets.env` (`HINDSIGHT_API_TENANT_API_KEY`, `HINDSIGHT_CP_DATAPLANE_API_KEY`, `HINDSIGHT_API_LLM_API_KEY`, `HINDSIGHT_API_RERANKER_NVIDIA_API_KEY`, `HINDSIGHT_API_RERANKER_1_OPENROUTER_API_KEY`, `HINDSIGHT_API_DECISION_MODEL_API_KEY`, `HINDSIGHT_API_DECISION_MODEL_BASE_URL`, `HINDSIGHT_API_REFLECT_DECISION_MODEL_API_KEY`).
- **Access:** the web UI opens from the tile (port 9999, behind Umbrel's login). The API and MCP endpoint are on port 8888 and need the API key, for example from Claude Code over Tailscale: `http://<pi-tailscale-ip>:8888/mcp/<bank>/` with `Authorization: Bearer <key>`.
- **Data:** the embedded Postgres lives in `data/pg0`. The image version is pinned so a database built elsewhere with the same Hindsight version can be restored here.
