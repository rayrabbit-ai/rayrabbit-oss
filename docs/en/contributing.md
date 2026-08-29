# Contributing to RayRabbit

We are excited that you want to contribute to the next-generation interoperability infrastructure for AI agents!

As an open-source project licensed under the **GNU Affero General Public License v3 (AGPL-3.0)**, we adhere to strict code standards, security practices, and testing flows to maintain the integrity of the network.

---

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct and ensure all communications remain professional, respectful, and constructive.

---

## Development Setup

To configure your system for active development, refer to our [Installation Guide](getting-started/installation.md).

### 1. Install Dev Tools
```bash
pip install -e .[dev]
```

### 2. PEP 8 Compliance
RayRabbit enforces strict **PEP 8** style guidelines:
* Use type annotations globally.
* Document all modules, classes, and methods using clear docstrings.
* Ensure all functions are asynchronous (`async`/`await`) where applicable.

---

## Testing Guidelines

We enforce **100% test coverage** on core transport and security files. Ensure your changes do not break existing suites:

```bash
# Run the entire test suite
pytest

# Check code coverage
pytest --cov=rayrabbit
```

---

## Git branching & PR Flow

1. Fork the repository on GitHub.
2. Create a clean branch from `main` or `master`:
   ```bash
   git checkout -b feature/amazing-improvement
   ```
3. Commit your changes following standard semantic messages:
   ```bash
   git commit -m "feat(security): integrate JWS verification on websocket ingest"
   ```
4. Push your branch to GitHub:
   ```bash
   git push origin feature/amazing-improvement
   ```
5. Open a Pull Request. Your PR will run CI checks automatically before merging.
