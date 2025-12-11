"""Django management command to run Mercury performance tests.

Smart discovery: Only runs tests that actually use monitor() context manager.
"""

import ast
import os
import sys
from typing import Dict, List, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand
from django.test.utils import get_runner


class Command(BaseCommand):
    """Run performance tests that use Mercury monitor()."""

    help = 'Run performance tests that use Mercury monitor() - smart discovery finds only relevant tests'

    def add_arguments(self, parser):
        parser.add_argument(
            'test_labels',
            nargs='*',
            help='Specific tests to run (app.TestClass.test_method)',
        )
        # Note: --verbosity is already provided by BaseCommand
        parser.add_argument(
            '--keepdb',
            action='store_true',
            help='Preserve test database between runs',
        )
        parser.add_argument(
            '--no-discover',
            action='store_true',
            help='Skip smart discovery, run standard Django test command',
        )
        parser.add_argument(
            '--html',
            nargs='?',
            const=True,
            default=None,
            metavar='FILENAME',
            help='Generate HTML report (optional: specify filename, default: auto-generate)',
        )

    def handle(self, *args, **options):
        """Main command handler."""
        verbosity = options['verbosity']

        # If no-discover, just run normal Django test
        if options['no_discover']:
            self._run_standard_tests(options)
            return

        # Smart discovery
        if verbosity >= 1:
            self.stdout.write(self.style.SUCCESS('\nDiscovering Mercury performance tests...\n'))

        mercury_files = self._discover_mercury_tests()

        if not mercury_files:
            self.stdout.write(
                self.style.WARNING(
                    'No tests found using monitor(). '
                    'Make sure you have:\n'
                    '  1. Test files starting with test_*.py\n'
                    '  2. Imported: from django_mercury import monitor\n'
                    '  3. Used: with monitor() as m: ...\n'
                )
            )
            return

        # Display discovery results
        if verbosity >= 1:
            self._display_discovery_results(mercury_files)

        # Build test labels from discovered files
        test_labels = self._build_test_labels(mercury_files, options['test_labels'])

        if not test_labels:
            self.stdout.write(self.style.WARNING('No matching tests found.'))
            return

        # Run tests
        self._run_tests(test_labels, options)

        # Generate HTML report if requested
        if options.get('html'):
            self._generate_html_report(options['html'], verbosity)

    def _discover_mercury_tests(self) -> Dict[str, List[str]]:
        """Discover test files using monitor().

        Returns:
            Dict mapping file paths to list of test method names
        """
        mercury_files = {}
        skip_dirs = {
            'venv',
            '.venv',
            'env',
            'migrations',
            '__pycache__',
            '.git',
            '.tox',
            'node_modules',
            'static',
            'media',
        }

        # Walk from current directory
        for root, dirs, files in os.walk('.'):
            # Filter out skip directories
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]

            for filename in files:
                if filename.startswith('test_') and filename.endswith('.py'):
                    filepath = os.path.join(root, filename)

                    # Check if file imports monitor
                    if self._file_uses_monitor(filepath):
                        # Find test methods using monitor()
                        test_methods = self._get_monitor_test_methods(filepath)
                        if test_methods:
                            mercury_files[filepath] = test_methods

        return mercury_files

    def _file_uses_monitor(self, filepath: str) -> bool:
        """Check if file imports monitor from django_mercury.

        Args:
            filepath: Path to Python file

        Returns:
            True if file imports monitor
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=filepath)

            for node in ast.walk(tree):
                # from django_mercury import monitor
                if isinstance(node, ast.ImportFrom):
                    if node.module == 'django_mercury':
                        if any(alias.name == 'monitor' for alias in node.names):
                            return True
                        if any(alias.name == '*' for alias in node.names):
                            return True

                # import django_mercury (less common)
                elif isinstance(node, ast.Import):
                    if any('django_mercury' in alias.name for alias in node.names):
                        return True

            return False

        except (SyntaxError, UnicodeDecodeError, OSError):
            # Skip files with syntax errors or encoding issues
            return False

    def _get_monitor_test_methods(self, filepath: str) -> List[str]:
        """Find test methods that use 'with monitor()'.

        Args:
            filepath: Path to Python file

        Returns:
            List of test method names
        """
        test_methods = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=filepath)

            # Find all class definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Look for test methods in this class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if item.name.startswith('test_'):
                                # Check if uses monitor() context
                                if self._uses_monitor_context(item):
                                    # Store as ClassName.test_method
                                    test_methods.append(f"{node.name}.{item.name}")

        except (SyntaxError, UnicodeDecodeError, OSError):
            pass

        return test_methods

    def _uses_monitor_context(self, func_node: ast.FunctionDef) -> bool:
        """Check if function uses 'with monitor()' context manager.

        Args:
            func_node: AST FunctionDef node

        Returns:
            True if function contains 'with monitor()' statement
        """
        for node in ast.walk(func_node):
            if isinstance(node, ast.With):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        # Check if it's calling monitor()
                        if isinstance(item.context_expr.func, ast.Name):
                            if item.context_expr.func.id == 'monitor':
                                return True
        return False

    def _display_discovery_results(self, mercury_files: Dict[str, List[str]]):
        """Display formatted discovery results.

        Args:
            mercury_files: Dict of filepath -> test methods
        """
        total_tests = sum(len(methods) for methods in mercury_files.values())

        self.stdout.write(
            self.style.SUCCESS(
                f'Found {len(mercury_files)} file(s) with {total_tests} Mercury test(s):\n'
            )
        )

        for filepath, methods in sorted(mercury_files.items()):
            # Clean up filepath (remove leading ./)
            clean_path = filepath.lstrip('./')
            self.stdout.write(f'  ✓ {clean_path} ({len(methods)} test{"s" if len(methods) != 1 else ""})')

        self.stdout.write('\n')

    def _build_test_labels(
        self, mercury_files: Dict[str, List[str]], user_labels: List[str]
    ) -> List[str]:
        """Build Django test labels from discovered files.

        Args:
            mercury_files: Dict of filepath -> test methods
            user_labels: User-provided test labels (for filtering)

        Returns:
            List of Django test labels
        """
        test_labels = []

        for filepath, methods in mercury_files.items():
            # Convert filepath to module path
            # e.g., ./myapp/tests/test_api.py -> myapp.tests.test_api
            module_path = (
                filepath.lstrip('./')
                .replace('/', '.')
                .replace('\\', '.')
                .replace('.py', '')
            )

            # If user provided labels, filter
            if user_labels:
                # Check if any user label matches this file/tests
                for method in methods:
                    full_label = f"{module_path}.{method}"
                    if any(label in full_label for label in user_labels):
                        test_labels.append(full_label)
            else:
                # Add all discovered tests
                for method in methods:
                    test_labels.append(f"{module_path}.{method}")

        return test_labels

    def _run_tests(self, test_labels: List[str], options: dict):
        """Run Django tests with the given labels.

        Args:
            test_labels: List of test labels to run
            options: Command options
        """
        TestRunner = get_runner(settings)

        test_runner = TestRunner(
            verbosity=options['verbosity'],
            interactive=False,
            keepdb=options.get('keepdb', False),
        )

        failures = test_runner.run_tests(test_labels)
        if failures:
            sys.exit(1)

    def _run_standard_tests(self, options: dict):
        """Fallback to standard Django test runner.

        Args:
            options: Command options
        """
        TestRunner = get_runner(settings)
        test_runner = TestRunner(
            verbosity=options['verbosity'],
            interactive=False,
            keepdb=options.get('keepdb', False),
        )

        test_labels = options.get('test_labels', None)
        failures = test_runner.run_tests(test_labels)
        if failures:
            sys.exit(1)

    def _generate_html_report(self, html_option, verbosity):
        """Generate HTML report after tests complete.

        Args:
            html_option: True (auto-generate filename) or string (custom filename)
            verbosity: Command verbosity level
        """
        from datetime import datetime

        from django_mercury.summary import MercurySummaryTracker

        tracker = MercurySummaryTracker.instance()

        if not tracker.results:
            if verbosity >= 1:
                self.stdout.write(
                    self.style.WARNING(
                        '\nNo Mercury results to export (no tests used monitor())'
                    )
                )
            return

        # Determine filename
        if html_option is True:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'mercury_report_{timestamp}.html'
        else:
            filename = html_option

        # Export HTML
        try:
            tracker.export_html(filename)
            if verbosity >= 1:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ HTML report generated: {filename}\n')
                )
        except Exception as e:
            if verbosity >= 1:
                self.stdout.write(
                    self.style.ERROR(f'\n✗ Failed to generate HTML report: {e}\n')
                )
