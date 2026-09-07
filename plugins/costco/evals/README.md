# Costco agentic evals

Four Harbor tasks cover warehouse discovery, product search, item-number lookup, and batch
shopping-list pricing. Each task runs the MCP server and a deterministic local
stand-in for Costco's four public website endpoints inside one task-local
environment. That layout runs with both Harbor's Docker and Modal providers.

Every task has two rewards:

- `outcome` compares `/app/answer.json` with fixture truth.
- `process` requires the expected MCP tool and rejects direct access to the mock,
  including calls delegated to subagents.

Generate the task files after changing the task table or templates:

```bash
python evals/generate_tasks.py
```

Check the real process criteria against solved, empty, bypassed, fallback,
delegated, delegated-bypass, and benign-shell trajectories without Harbor or a
model:

```bash
make validate-process
```

Run the agent gate locally with Docker:

```bash
export CLAUDE_CODE_OAUTH_TOKEN=...
HARBOR_MCP_REF="$(git rev-parse HEAD)" make evals
```

The git ref must already be pushed. CI sets `HARBOR_TEST_ENV=modal` and pins
`HARBOR_MCP_REF` to the PR head SHA so the environment installs the code under
review. Uploaded runs are named `ci-evals-costco`.
