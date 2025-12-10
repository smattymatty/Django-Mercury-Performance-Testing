# Issue #3: Add Django Management Command with Smart Discovery

**Label:** `enhancement`, `django-native`
**Milestone:** v0.1.1
**Estimated Effort:** 45 minutes (15 min base + 30 min smart filtering)

## Problem

Users have to remember test runner commands. A Django management command feels more native and enables smart test discovery.

## Proposed Solution

Add `python manage.py mercury_test` command that:
1. Finds test files where `monitor` is imported
2. Only runs test methods that actually use `with monitor()`
3. Provides nice summary output

```bash
# Run all tests using mercury monitor
python manage.py mercury_test

# Run specific app
python manage.py mercury_test myapp

# Run specific test file
python manage.py mercury_test myapp/tests/test_api.py

# Verbose mode
python manage.py mercury_test --verbose
```

**Example output:**
```
Discovering Mercury tests...
Found 3 test files using monitor():
  ✓ accounts/tests/test_auth_performance.py (2 tests)
  ✓ api/tests/test_user_endpoints.py (5 tests)
  ✓ dashboard/tests/test_views.py (1 test)

Running 8 Mercury performance tests...

[... test output ...]

================================ MERCURY SUMMARY ================================
8 tests ran in 1.23s
✓ 7 passed, ✗ 1 failed
=================================================================================
```

## Acceptance Criteria

- [ ] Management command: `python manage.py mercury_test`
- [ ] Smart discovery: AST parsing to find actual `monitor()` usage
- [ ] Only runs tests that use `monitor()` context manager
- [ ] Supports app/file/method targeting like Django's test command
- [ ] Integrates with existing test discovery
- [ ] Shows summary report automatically
- [ ] Respects Django test settings (database, etc.)

## Implementation Notes

**File:** `django_mercury/management/commands/mercury_test.py` (new)

```python
from django.core.management.base import BaseCommand
from django.test.utils import get_runner
import ast
import os

class Command(BaseCommand):
    help = 'Run performance tests that use Mercury monitor'

    def add_arguments(self, parser):
        parser.add_argument(
            'test_labels',
            nargs='*',
            help='Test labels (app.TestCase.test_method)',
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output',
        )

    def handle(self, *args, **options):
        # Discover tests using monitor()
        test_files = self._discover_mercury_tests()

        # Filter by test_labels if provided
        # Run tests
        # Show summary
        ...

    def _discover_mercury_tests(self):
        """Find test files that use monitor()."""
        mercury_tests = []

        for root, dirs, files in os.walk('.'):
            # Skip venv, migrations, etc.
            dirs[:] = [d for d in dirs if d not in ['venv', '.venv', 'migrations', '__pycache__']]

            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    path = os.path.join(root, file)
                    if self._file_uses_monitor(path):
                        test_methods = self._get_monitor_test_methods(path)
                        mercury_tests.append((path, test_methods))

        return mercury_tests

    def _file_uses_monitor(self, path: str) -> bool:
        """Check if file imports monitor from django_mercury."""
        try:
            with open(path, 'r') as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module == 'django_mercury':
                        if any(alias.name == 'monitor' for alias in node.names):
                            return True
                elif isinstance(node, ast.Import):
                    if any('django_mercury' in alias.name for alias in node.names):
                        return True
            return False
        except:
            return False

    def _get_monitor_test_methods(self, path: str) -> list:
        """Find test methods that actually call monitor()."""
        test_methods = []

        try:
            with open(path, 'r') as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_'):
                        # Check if function body uses 'with monitor()'
                        if self._uses_monitor_context(node):
                            test_methods.append(node.name)

        except:
            pass

        return test_methods

    def _uses_monitor_context(self, func_node: ast.FunctionDef) -> bool:
        """Check if function uses 'with monitor()' context manager."""
        for node in ast.walk(func_node):
            if isinstance(node, ast.With):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        if isinstance(item.context_expr.func, ast.Name):
                            if item.context_expr.func.id == 'monitor':
                                return True
        return False
```

## Technical Challenges

1. **AST parsing edge cases:**
   - Import aliases: `from django_mercury import monitor as m`
   - Indirect usage: `mon = monitor; with mon():`
   - Solution: Start simple, iterate

2. **Test runner integration:**
   - Need to work with Django's test discovery
   - Should respect `TEST_RUNNER` setting
   - Use `DiscoverRunner` as base

3. **Performance:**
   - AST parsing is fast (~1ms per file)
   - Cache results for repeated runs?

## Benefits

- **Smart:** Only runs performance tests (no need to run ALL tests)
- **Fast:** Skips tests without monitor()
- **Django-native:** Feels like `python manage.py test`
- **Discoverable:** Users find it via `manage.py --help`

## Future Enhancements (v0.2.0+)

- Watch mode: `--watch` to re-run on file changes
- Parallel execution: `--parallel` flag
- Profile mode: `--profile` for memory/CPU stats
- Export results: `--export=json` or `--export=html`
