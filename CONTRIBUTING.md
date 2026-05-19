# Contributing to ShopKeeper AI

## Commit Message Format

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <short description>
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | New feature or behaviour |
| `fix` | Bug fix |
| `chore` | Setup, config, tooling, dependencies |
| `refactor` | Code change that is not a fix or feature |
| `test` | Adding or updating tests |
| `docs` | Documentation only changes |
| `style` | Formatting, missing semicolons - no logic change |

### Scope (optional but recommended)

Use the area of the codebase affected. Examples:
- `feat(auth): add JWT refresh endpoint`
- `fix(payment): handle timeout state correctly`
- `chore(deps): add pytest to requirements.txt`
- `test(inventory): add unit tests for stock reservation`

### Rules

- Use lowercase only
- No period at the end
- Keep the description under 72 characters
- Use the imperative mood - "add" not "added", "fix" not "fixed"