"""
Automated Source Code Instrumenter for ARIS.
Transparently weaves low-overhead runtime probes into Arduino sketches without requiring manual developer modifications.
"""

import re
from typing import Tuple

class SourceInstrumenter:
    def __init__(self):
        pass

    def instrument(self, source_code: str, baud_rate: int = 115200) -> Tuple[str, int]:
        """
        Injects ARIS runtime hooks into user sketch.
        Returns: (instrumented_code, probe_count)
        """
        code = source_code
        probe_count = 0

        # Check if already instrumented
        if "aris_runtime.h" in code or "ARIS.init" in code:
            return code, 0

        header_injection = '#include "aris_runtime.h"\nArisRuntime ARIS;\n\n'
        
        # 1. Instrument setup()
        setup_match = re.search(r'(void\s+setup\s*\(\s*\)\s*\{)', code)
        if setup_match:
            init_code = f"\n  ARIS.init({baud_rate});"
            insert_pos = setup_match.end()
            code = code[:insert_pos] + init_code + code[insert_pos:]
            probe_count += 1
        else:
            # Create a setup if not present
            code = f"void setup() {{\n  ARIS.init({baud_rate});\n}}\n" + code
            probe_count += 1

        # 2. Instrument loop()
        loop_match = re.search(r'(void\s+loop\s*\(\s*\)\s*\{)', code)
        if loop_match:
            enter_code = "\n  ARIS.loop_enter();"
            insert_pos = loop_match.end()
            
            # Find the matching closing brace for loop
            brace_count = 1
            idx = insert_pos
            while idx < len(code) and brace_count > 0:
                if code[idx] == '{':
                    brace_count += 1
                elif code[idx] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        break
                idx += 1
            
            loop_end_pos = idx
            exit_code = "\n  ARIS.loop_exit();\n"
            
            # Weave enter and exit probes
            code = code[:insert_pos] + enter_code + code[insert_pos:loop_end_pos] + exit_code + code[loop_end_pos:]
            probe_count += 2

        # 3. Add runtime header at the very top
        code = header_injection + code
        return code, probe_count
