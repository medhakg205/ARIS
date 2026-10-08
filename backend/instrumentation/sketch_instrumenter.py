"""
ARIS Transparent Sketch Instrumenter.
Automatically creates an isolated shadow build with ARIS runtime hooks
without altering the original Arduino sketch on disk.
"""

import os
import re
import difflib
import hashlib
import tempfile
import shutil
from typing import Dict, Any, Tuple, Optional, List
from pydantic import BaseModel, Field

from backend.telemetry.telemetry_schema import ArisException


class InstrumentationResult(BaseModel):
    """Encapsulates the transparent instrumentation output and metadata."""
    original_source: str
    instrumented_source: str
    diff: str
    inserted_blocks: List[str]
    board_id: str
    run_id: str
    original_file_path: Optional[str] = None
    original_file_hash: Optional[str] = None
    shadow_sketch_dir: Optional[str] = None
    shadow_sketch_path: Optional[str] = None
    verification_hash_match: bool = True


class SketchInstrumenter:
    """
    Syntactic analyzer and code transform engine for Arduino sketches.
    Parses functions using a comment/string-aware lexer, locates setup() and loop(),
    and produces an instrumented shadow copy.
    """

    @staticmethod
    def _mask_comments_and_strings(source: str) -> str:
        """
        Masks out comments and string/char literals with spaces while preserving
        exact character positions and newlines so regex/offset indexing remains 1:1.
        """
        chars = list(source)
        length = len(chars)
        i = 0

        while i < length:
            # Single-line comment: // ...
            if i + 1 < length and chars[i] == '/' and chars[i + 1] == '/':
                chars[i] = ' '
                chars[i + 1] = ' '
                i += 2
                while i < length and chars[i] != '\n':
                    chars[i] = ' '
                    i += 1
                continue

            # Multi-line comment: /* ... */
            if i + 1 < length and chars[i] == '/' and chars[i + 1] == '*':
                chars[i] = ' '
                chars[i + 1] = ' '
                i += 2
                while i < length:
                    if chars[i] == '\n':
                        i += 1
                        continue
                    if i + 1 < length and chars[i] == '*' and chars[i + 1] == '/':
                        chars[i] = ' '
                        chars[i + 1] = ' '
                        i += 2
                        break
                    chars[i] = ' '
                    i += 1
                continue

            # Double-quoted string: "..."
            if chars[i] == '"':
                chars[i] = ' '
                i += 1
                while i < length:
                    if chars[i] == '\\' and i + 1 < length:
                        chars[i] = ' '
                        chars[i + 1] = ' '
                        i += 2
                        continue
                    if chars[i] == '"':
                        chars[i] = ' '
                        i += 1
                        break
                    if chars[i] != '\n':
                        chars[i] = ' '
                    i += 1
                continue

            # Single-quoted char: '.'
            if chars[i] == "'":
                chars[i] = ' '
                i += 1
                while i < length:
                    if chars[i] == '\\' and i + 1 < length:
                        chars[i] = ' '
                        chars[i + 1] = ' '
                        i += 2
                        continue
                    if chars[i] == "'":
                        chars[i] = ' '
                        i += 1
                        break
                    if chars[i] != '\n':
                        chars[i] = ' '
                    i += 1
                continue

            i += 1

        return "".join(chars)

    @classmethod
    def _find_function_bounds(cls, masked: str, func_name: str) -> Tuple[int, int, int]:
        """
        Locates the declaration start, opening brace, and matching closing brace of a function.
        Returns (decl_start_idx, open_brace_idx, close_brace_idx).
        Raises ArisException if the function is missing or malformed.
        """
        pattern = re.compile(rf'\bvoid\s+{func_name}\s*\(\s*(void)?\s*\)', re.IGNORECASE)
        match = pattern.search(masked)
        if not match:
            raise ArisException(
                error_code="ARIS_INSTRUMENTATION_FAILED",
                message=f"Required Arduino lifecycle function 'void {func_name}()' was not found.",
                details={"function": func_name},
                recoverable=True,
                status_code=400
            )

        decl_start = match.start()
        # Find opening brace following the signature
        open_brace = masked.find('{', match.end())
        if open_brace == -1:
            raise ArisException(
                error_code="ARIS_INSTRUMENTATION_FAILED",
                message=f"Function 'void {func_name}()' is missing opening body brace '{{'.",
                details={"function": func_name},
                recoverable=True,
                status_code=400
            )

        # Count braces to find matching closing brace
        depth = 1
        i = open_brace + 1
        length = len(masked)
        close_brace = -1

        while i < length:
            c = masked[i]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    close_brace = i
                    break
            i += 1

        if close_brace == -1:
            raise ArisException(
                error_code="ARIS_INSTRUMENTATION_FAILED",
                message=f"Unmatched braces in function 'void {func_name}()'.",
                details={"function": func_name},
                recoverable=True,
                status_code=400
            )

        return (decl_start, open_brace, close_brace)

    @classmethod
    def instrument_code(
        cls,
        source_code: str,
        board_id: str = "arduino_uno",
        baud_rate: int = 115200,
        run_id: str = "DEMO-RUN"
    ) -> Tuple[str, List[str], str]:
        """
        Pure string transformation.
        Instruments setup() and loop(), prepends <aris_runtime.h>,
        and returns (instrumented_code, inserted_blocks, unified_diff).
        """
        if not source_code or not source_code.strip():
            raise ArisException(
                error_code="ARIS_EMPTY_SOURCE",
                message="Cannot instrument empty source code.",
                recoverable=True,
                status_code=400
            )

        # Check if already instrumented
        if "<aris_runtime.h>" in source_code and "ARIS.init" in source_code:
            diff = "".join(difflib.unified_diff(
                source_code.splitlines(keepends=True),
                source_code.splitlines(keepends=True),
                fromfile="original.ino",
                tofile="instrumented.ino"
            ))
            return source_code, ["(Source was already instrumented)"], diff

        masked = cls._mask_comments_and_strings(source_code)

        # Locate setup() and loop()
        _, setup_open, setup_close = cls._find_function_bounds(masked, "setup")
        _, loop_open, loop_close = cls._find_function_bounds(masked, "loop")

        inserted_blocks: List[str] = []

        # Code snippets to inject
        header_snippet = (
            "// ============================================================================\n"
            "// ARIS Studio Transparent Instrumentation (Auto-generated - DO NOT EDIT)\n"
            "// ============================================================================\n"
            "#include <aris_runtime.h>\n\n"
        )

        setup_init_snippet = (
            "\n  // [ARIS] Runtime Auto-Initialization\n"
            f'  ARIS.init("{board_id}", {baud_rate}UL, "{run_id}", ARIS_MODE_BALANCED);\n'
        )

        loop_enter_snippet = "\n  ARIS.loop_enter();\n"
        loop_exit_snippet = "  ARIS.loop_exit();\n"

        # Plan insertions by character index in descending order to preserve index validity
        # Tuple: (insert_idx, text_to_insert, description)
        edits: List[Tuple[int, str, str]] = []

        # 1. Header at index 0 (if not already included)
        if "<aris_runtime.h>" not in source_code:
            edits.append((0, header_snippet, "Header: #include <aris_runtime.h>"))

        # 2. setup(): ARIS.init before closing brace of setup
        edits.append((setup_close, setup_init_snippet, f"setup(): ARIS.init({board_id}, {baud_rate})"))

        # 3. loop(): ARIS.loop_enter() immediately after loop opening brace
        edits.append((loop_open + 1, loop_enter_snippet, "loop(): ARIS.loop_enter()"))

        # 4. loop(): ARIS.loop_exit() before closing brace of loop
        edits.append((loop_close, loop_exit_snippet, "loop(): ARIS.loop_exit()"))

        # Sort edits in reverse character index order so earlier indices remain unaffected
        edits.sort(key=lambda x: x[0], reverse=True)

        instrumented = source_code
        for idx, text, desc in edits:
            instrumented = instrumented[:idx] + text + instrumented[idx:]
            inserted_blocks.append(desc)

        # Reverse list so descriptions appear in logical top-to-bottom order
        inserted_blocks.reverse()

        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            source_code.splitlines(keepends=True),
            instrumented.splitlines(keepends=True),
            fromfile="original.ino",
            tofile="instrumented.ino"
        ))
        diff_str = "".join(diff_lines)

        return instrumented, inserted_blocks, diff_str

    @classmethod
    def create_shadow_workspace(
        cls,
        source_code: Optional[str] = None,
        source_path: Optional[str] = None,
        board_id: str = "arduino_uno",
        baud_rate: int = 115200,
        run_id: Optional[str] = None,
        base_build_dir: Optional[str] = None
    ) -> InstrumentationResult:
        """
        Generates an isolated shadow workspace without modifying the source file on disk.
        Records file hashes before and after to strictly prove the original remains untouched.
        """
        import time
        rid = run_id or f"RUN-SHADOW-{int(time.time())}"

        orig_hash_before: Optional[str] = None
        if source_path and os.path.exists(source_path):
            with open(source_path, "rb") as f:
                orig_hash_before = hashlib.sha256(f.read()).hexdigest()
            if not source_code:
                with open(source_path, "r", encoding="utf-8") as f:
                    source_code = f.read()

        if not source_code:
            raise ArisException(
                error_code="ARIS_NO_SOURCE",
                message="No source code or valid file path provided for instrumentation.",
                recoverable=True,
                status_code=400
            )

        instrumented_code, inserted_blocks, diff = cls.instrument_code(
            source_code=source_code,
            board_id=board_id,
            baud_rate=baud_rate,
            run_id=rid
        )

        # Setup isolated shadow build directory
        if not base_build_dir:
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            base_build_dir = os.path.join(backend_dir, ".aris_build")

        shadow_dir = os.path.join(base_build_dir, rid, "sketch")
        os.makedirs(shadow_dir, exist_ok=True)

        # Sketch name must match directory name or default to sketch.ino
        shadow_sketch_file = os.path.join(shadow_dir, "sketch.ino")
        with open(shadow_sketch_file, "w", encoding="utf-8") as f:
            f.write(instrumented_code)

        # Verify original source on disk was NOT touched
        orig_hash_after: Optional[str] = None
        hash_matched = True
        if source_path and os.path.exists(source_path):
            with open(source_path, "rb") as f:
                orig_hash_after = hashlib.sha256(f.read()).hexdigest()
            hash_matched = (orig_hash_before == orig_hash_after)

        return InstrumentationResult(
            original_source=source_code,
            instrumented_source=instrumented_code,
            diff=diff,
            inserted_blocks=inserted_blocks,
            board_id=board_id,
            run_id=rid,
            original_file_path=source_path,
            original_file_hash=orig_hash_after or orig_hash_before,
            shadow_sketch_dir=shadow_dir,
            shadow_sketch_path=shadow_sketch_file,
            verification_hash_match=hash_matched
        )
