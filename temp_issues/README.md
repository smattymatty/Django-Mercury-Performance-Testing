# Mercury v0.1.1 Feature Proposals

**Status:** Planning phase
**Target Release:** v0.1.1

These issues represent the planned feature set for the next minor release. All features have been discussed and approved.

## Quick Summary

| # | Feature | Effort | Priority | Status |
|---|---------|--------|----------|--------|
| 1 | [NO_COLOR env var](01-no-color-env-var.md) | 5 min | High | 📋 Planned |
| 2 | [Summary report](02-summary-report.md) | 20 min | High | 📋 Planned |
| 3 | [Django management command](03-django-management-command.md) | 45 min | High | 📋 Planned |
| 5 | [HTML report export](05-html-report-export.md) | 40 min | Medium | 📋 Planned |

**Total estimated effort:** ~2 hours

## Implementation Order

### Phase 1: Quick Wins (30 min)
1. NO_COLOR env var (#1)
2. Summary report (#2)

**Goal:** Improve CI/CD experience immediately

### Phase 2: Django Native (45 min)
3. Management command with smart discovery (#3)

**Goal:** Make Mercury feel like part of Django

### Phase 3: Sharing & Reporting (40 min)
5. HTML export (#5)

**Goal:** Enable team collaboration and stakeholder sharing

## Notes

- **Issue #4 (pytest plugin) was rejected** - deemed unnecessary for v0.1.1
- All features maintain backward compatibility
- No breaking changes to existing API
- Focus on "Simple is better than Complex" philosophy

## How to Contribute

1. Pick an issue from the list
2. Create a branch: `git checkout -b feature/issue-N-short-name`
3. Implement following the spec in the issue markdown
4. Add tests
5. Update README.md with new feature
6. Submit PR

## Questions?

Open a discussion in the main repository or comment on the specific issue.

---

**Created:** 2025-12-10
**Last Updated:** 2025-12-10
