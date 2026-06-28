import ast
from pathlib import Path

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

DB_READ_METHODS = {"get", "execute", "query", "scalars", "select"}
FK_NAMES = {"foreign_key", "ForeignKey"}


@register_rule
class MissingJoinedloadRule(Rule):
    """Detect separate DB queries for related models that could use joinedload (FASTT032)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT032",
            severity=Severity.WARNING,
            description="Separate DB queries for related models — could use joinedload() for a single query",
            recommendation="Use joinedload() or selectinload() to eager-load related data in one query",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            diagnostics.extend(self._check_function_body(node, file_path, tree))
        return diagnostics

    def check_from_nodes(self, nodes, tree, file_path, source):
        return self.check(tree, file_path, source)

    def check_function(self, func_node, file_path):
        if not isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return []
        try:
            resolved = Path(file_path).resolve()
            source = resolved.read_text(encoding="utf-8")
            tree = ast.parse(source)
            return self._check_function_body(func_node, str(resolved), tree)
        except (OSError, SyntaxError):
            return []

    def _check_function_body(self, func_node, file_path, tree) -> list[Diagnostic]:
        diagnostics = []
        tracked: dict[str, str] = {}
        seen_pairs: set[tuple[str, str]] = set()

        # Exclude inner functions
        inner_funcs = self._collect_inner_funcs(func_node)

        for node in ast.walk(func_node):
            if node in inner_funcs:
                continue

            # Step 1: Track DB-sourced variables
            if isinstance(node, ast.Assign):
                model = self._extract_db_model(node.value)
                if model:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            tracked[target.id] = model

            # Step 2: Detect FK access in DB calls
            if isinstance(node, ast.Call) and self._is_db_read(node):
                child_model = self._extract_db_model(node)
                if not child_model:
                    continue
                for child in ast.walk(node):
                    if not isinstance(child, ast.Attribute):
                        continue
                    if not isinstance(child.value, ast.Name):
                        continue
                    if child.value.id not in tracked:
                        continue

                    parent_model = tracked[child.value.id]
                    fk_field = child.attr
                    pair = (parent_model, fk_field, child_model)
                    pair_key = tuple(sorted([parent_model, child_model]))
                    if pair_key in seen_pairs:
                        continue

                    # Step 3: Lazy-verify by reading model file
                    if self._verify_relation(
                        parent_model, fk_field, child_model, file_path, tree
                    ):
                        seen_pairs.add(pair_key)
                        diagnostics.append(
                            Diagnostic(
                                severity=self.definition.severity,
                                file_path=file_path,
                                rule=self.definition.id,
                                message=f"separate query for '{child_model}' via '{parent_model}.{fk_field}' — use joinedload({parent_model}.{fk_field})",
                                line=node.lineno,
                                column=node.col_offset,
                                help=self.definition.recommendation,
                            )
                        )

        return diagnostics

    def _extract_db_model(self, call: ast.expr) -> str | None:
        """Extract model name from a DB read call like db.get(User, id) or db.execute(select(User))."""
        if not isinstance(call, ast.Call):
            return None
        if not isinstance(call.func, ast.Attribute):
            return None
        if call.func.attr not in DB_READ_METHODS:
            return None
        if not call.args:
            return None

        first_arg = call.args[0]
        if isinstance(first_arg, ast.Name):
            return first_arg.id
        if isinstance(first_arg, ast.Attribute):
            return first_arg.attr
        if (
            isinstance(first_arg, ast.Call)
            and isinstance(first_arg.func, ast.Name)
            and first_arg.func.id in ("select",)
        ):
            if first_arg.args and isinstance(first_arg.args[0], ast.Name):
                return first_arg.args[0].id
            if first_arg.args and isinstance(first_arg.args[0], ast.Attribute):
                return first_arg.args[0].attr
        return None

    def _is_db_read(self, call: ast.Call) -> bool:
        """Check if call is a DB read operation."""
        if isinstance(call.func, ast.Attribute) and call.func.attr in DB_READ_METHODS:
            return True
        return False

    def _collect_inner_funcs(self, func_node) -> set:
        inner = set()
        for node in ast.walk(func_node):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node is not func_node
            ):
                for desc in ast.walk(node):
                    inner.add(desc)
        return inner

    def _verify_relation(
        self,
        parent_model: str,
        fk_field: str,
        child_model: str,
        file_path: str,
        tree: ast.Module,
    ) -> bool:
        """Check if parent_model has fk_field pointing to child_model.

        Scans the same file's AST first, then tries model files in the same directory.
        """
        if self._check_class_for_fk(tree, parent_model, fk_field, child_model):
            return True

        source_dir = Path(file_path).parent
        for model_file in self._find_model_files(parent_model, source_dir):
            try:
                model_tree = ast.parse(model_file.read_text(encoding="utf-8"))
                if self._check_class_for_fk(
                    model_tree, parent_model, fk_field, child_model
                ):
                    return True
            except (OSError, SyntaxError):
                continue

        return False

    def _check_class_for_fk(
        self, tree: ast.Module, class_name: str, fk_field: str, child_model: str
    ) -> bool:
        """Check if a class has fk_field with a foreign key pointing to child_model."""
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name != class_name:
                continue
            for child in node.body:
                if self._is_fk_field(child, fk_field, child_model):
                    return True
        return False

    def _is_fk_field(self, node: ast.AST, fk_field: str, child_model: str) -> bool:
        """Check if an AST node declares fk_field with foreign key to child_model."""
        if not isinstance(node, (ast.AnnAssign, ast.Assign)):
            return False
        target = node.target if isinstance(node, ast.AnnAssign) else None
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == fk_field:
                    target = t
                    break
        if target is None:
            return False
        if not isinstance(target, ast.Name) or target.id != fk_field:
            return False

        # Check value for ForeignKey/foreign_key
        value = node.value if isinstance(node, ast.AnnAssign) else node.value

        # SQLAlchemy Core: Column(Integer, ForeignKey("childs.id"))
        # SQLModel: Field(foreign_key="childs.id")
        # SA 2.0: mapped_column(ForeignKey("childs.id"))
        if isinstance(value, ast.Call):
            return self._call_contains_fk_to(value, child_model)

        return False

    def _call_contains_fk_to(self, call: ast.Call, child_model: str) -> bool:
        """Check if a Call (Column/Field/mapped_column) has FK pointing to child_model."""
        # ForeignKey("childs.id") in args
        for arg in call.args:
            if isinstance(arg, ast.Call):
                fk_table = self._extract_fk_table(arg)
                if fk_table and self._matches_model(fk_table, child_model):
                    return True

        # foreign_key="childs.id" keyword (SQLModel)
        for kw in call.keywords:
            if (
                kw.arg == "foreign_key"
                and isinstance(kw.value, ast.Constant)
                and isinstance(kw.value.value, str)
            ):
                if self._matches_model(kw.value.value, child_model):
                    return True

        return False

    def _matches_model(self, table_ref: str, model_name: str) -> bool:
        """Check if a table reference like 'companies.id' matches model 'Company'."""
        table = table_ref.split(".")[0].lower()  # "companies"
        model = model_name.lower()  # "company"
        return model == table or table in (
            model + "s",
            model + "es",
            model.rstrip("y") + "ies",
        )

    def _extract_fk_table(self, fk_call: ast.Call) -> str | None:
        """Extract table name from ForeignKey('table.column') call."""
        if not isinstance(fk_call, ast.Call):
            return None
        func = fk_call.func
        is_fk = (isinstance(func, ast.Name) and func.id in FK_NAMES) or (
            isinstance(func, ast.Attribute) and func.attr in FK_NAMES
        )
        if not is_fk:
            return None
        if (
            fk_call.args
            and isinstance(fk_call.args[0], ast.Constant)
            and isinstance(fk_call.args[0].value, str)
        ):
            return fk_call.args[0].value.split(".")[0]
        return None

    def _find_model_files(self, model_name: str, source_dir: Path) -> list[Path]:
        """Search for model files containing the class — check sibling dirs and parent."""
        candidates = []
        # Search current dir and its parent (project root)
        search_roots = [source_dir, source_dir.parent]
        for root in search_roots:
            for py_file in sorted(root.glob("*.py")):
                candidates.append(py_file)
            for child in sorted(root.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
                    for py_file in sorted(child.glob("*.py")):
                        candidates.append(py_file)
        return candidates[:50]
