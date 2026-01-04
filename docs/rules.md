# CodeWarden Development Rules

## Terminal Commands

### Commands I'll ask you to run:
- Installing system tools (Python, Node.js, pnpm, Docker)
- Setting up development environment
- Running/starting the project
- Any commands that modify your system configuration
- **Pushing to remote repositories** (git push)

### Commands I can run myself:
- Running tests (pytest, vitest, npm test)
- Linting and type checking
- Building the project
- Git operations (status, diff, commit when requested)
- File searches and exploration

---

## Git Branching Strategy

```
main (production)
  │
  └── develop (staging/integration)
        │
        ├── feature/feature-name
        ├── feature/another-feature
        └── ...
```

### Branch Descriptions

| Branch | Purpose | Merges From | Merges To |
|--------|---------|-------------|-----------|
| `main` | Production-ready, fully tested code | `develop` | - |
| `develop` | Locally tested, working code | `feature/*` | `main` |
| `feature/*` | Individual feature development | - | `develop` |

### Workflow Rules

1. **Feature Development**
   - Create feature branch from `develop`: `git checkout -b feature/my-feature develop`
   - Work on the feature
   - Test locally until working
   - Push to feature branch: `git push -u origin feature/my-feature`

2. **Merging to Develop**
   - Feature must be locally tested and working
   - Create PR from `feature/*` → `develop`
   - After review, merge to `develop`

3. **Merging to Main**
   - Code in `develop` must be fully tested
   - All features must work together
   - Create PR from `develop` → `main`
   - Only production-ready code goes to `main`

### Branch Protection

- **main**: Only accepts merges from `develop` after full testing
- **develop**: Only accepts merges from `feature/*` branches after local testing
- Direct commits to `main` or `develop` are not allowed

### Naming Conventions

- Feature branches: `feature/short-description`
- Bug fixes: `fix/short-description`
- Hotfixes (urgent prod fixes): `hotfix/short-description`

Examples:
- `feature/user-authentication`
- `feature/airlock-pii-scrubbing`
- `fix/redis-connection-timeout`
- `hotfix/security-patch`

---

## Document Update Rules

After every task, update these documents:

1. **audit.md** - Mark task status, add notes
2. **Error.md** - Log any errors encountered with solutions
3. **map.md** - Update file dependencies if new files created

---

## Reference Documents

Always refer to these when working:
- `docs/audits/audit.md` - Task tracking
- `docs/audits/Error.md` - Error tracking
- `docs/audits/map.md` - File dependencies
- `docs/BEST_PRACTICES.md` - Coding standards
- `docs/implementation/` - Implementation checklists
