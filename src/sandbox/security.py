"""Security scanning for code execution."""

import ast

from .types import SandboxConfig


class SandboxSecurityError(Exception):
    """Exception raised when security violation is detected."""

    def __init__(self, message: str, violations: list[str]):
        self.violations = violations
        super().__init__(message)


class SecurityScanner:
    """AST-based security scanner for Python code."""

    def __init__(self, config: SandboxConfig):
        """Initialize scanner with configuration.

        Args:
            config: Sandbox configuration with allowed/blocked modules
        """
        self.config = config
        self._blocked: set[str] = set(config.blocked_modules)
        self._allowed: set[str] | None = (
            set(config.allowed_modules) if config.allowed_modules else None
        )

    def scan_imports(self, code: str) -> list[str]:
        """Scan code for blocked imports.

        Args:
            code: Python code to scan

        Returns:
            List of blocked module names found in code

        Raises:
            SyntaxError: If code has invalid Python syntax
        """
        tree = ast.parse(code)  # May raise SyntaxError

        violations: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    if self._is_blocked(module_name):
                        violations.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split(".")[0]
                    if self._is_blocked(module_name):
                        violations.append(node.module)

        return violations

    def scan_dangerous_calls(self, code: str) -> list[str]:
        """Scan code for dangerous function calls.

        Args:
            code: Python code to scan

        Returns:
            List of dangerous calls found
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        dangerous_funcs = {"eval", "exec", "compile", "__import__"}
        violations: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                # Check for direct calls like eval()
                if isinstance(func, ast.Name) and func.id in dangerous_funcs:
                    violations.append(f"{func.id}()")
                # Check for attribute calls like __import__('os')
                elif isinstance(func, ast.Attribute):
                    if func.attr in dangerous_funcs:
                        violations.append(f"{func.attr}()")

        return violations

    def validate(self, code: str) -> None:
        """Validate code for security violations.

        Args:
            code: Python code to validate

        Raises:
            SyntaxError: If code has invalid Python syntax
            SandboxSecurityError: If any security violations are found
        """
        import_violations = self.scan_imports(code)
        call_violations = self.scan_dangerous_calls(code)

        all_violations = import_violations + call_violations

        if all_violations:
            raise SandboxSecurityError(
                f"Security violation: blocked imports or calls detected: {all_violations}",
                violations=all_violations,
            )

    def _is_blocked(self, module_name: str) -> bool:
        """Check if a module is blocked.

        Args:
            module_name: Name of the module to check

        Returns:
            True if module is blocked, False otherwise
        """
        # If allowlist is specified, only allow those modules
        if self._allowed is not None:
            return module_name not in self._allowed
        # Otherwise, use blocklist
        return module_name in self._blocked
