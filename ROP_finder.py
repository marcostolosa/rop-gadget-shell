import re
import sys

# Enable history
try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline
    except ImportError:
        readline = None
        print("[!] readline not available: install with 'pip install pyreadline3'")

# ANSI color codes
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def load_rop_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.readlines()
    except FileNotFoundError:
        print(f"[!] File not found: {file_path}")
        return []

def ends_with_ret(line):
    line = line.strip().lower()
    if '; (' in line:
        line = line[:line.rfind('; (')].strip()
    parts = [p.strip() for p in line.split(';') if p.strip()]
    if not parts:
        return False
    last_instr = parts[-1]
    return last_instr == "ret" or last_instr.startswith("retn")

def highlight_matches(line, include_pattern, extra_patterns):
    try:
        regex = re.compile(include_pattern, re.IGNORECASE)
        line = regex.sub(lambda m: f"{RED}{m.group(0)}{RESET}", line)
        for pat in extra_patterns:
            if pat:
                pat_regex = re.compile(pat, re.IGNORECASE)
                line = pat_regex.sub(lambda m: f"{YELLOW}{m.group(0)}{RESET}", line)
        return line
    except re.error as e:
        return f"[!] Invalid regex pattern: {e}"

def search_gadgets(gadgets, include_pattern, highlight_patterns=None, exclude_patterns=None):
    try:
        include_regex = re.compile(include_pattern, re.IGNORECASE)
    except re.error as e:
        print(f"[!] Invalid include regex: {e}")
        return []

    exclude_regexes = []
    for p in (exclude_patterns or []):
        try:
            exclude_regexes.append(re.compile(p, re.IGNORECASE))
        except re.error as e:
            print(f"[!] Invalid exclude regex '{p}': {e}")
            return []

    results = []
    for line in gadgets:
        line_stripped = line.strip()
        if include_regex.search(line_stripped) and ends_with_ret(line_stripped):
            if any(ex.search(line_stripped) for ex in exclude_regexes):
                continue
            highlighted = highlight_matches(line_stripped, include_pattern, highlight_patterns or [])
            results.append(highlighted)
    return results

def wildcard_to_regex(pattern):
    pattern = re.escape(pattern)
    return pattern.replace(r'\*', '.*')

def parse_input(input_str):
    # Split by -exclude first
    parts = input_str.split('-exclude')
    include_part = parts[0]
    exclude_parts = parts[1:] if len(parts) > 1 else []

    # Split include part by -include
    include_sections = include_part.split('-include')
    main_include = wildcard_to_regex(include_sections[0].strip())
    additional_includes = [wildcard_to_regex(p.strip()) for p in include_sections[1:]] if len(include_sections) > 1 else []

    excludes = [wildcard_to_regex(p.strip()) for p in exclude_parts]
    return main_include, additional_includes, excludes

def interactive_shell(gadgets):
    print("=== ROP Gadget Search Shell ===")
    print("Usage:")
    print("  <include pattern> [-include <highlight>] [-exclude <pattern>] ...")
    print("  (Only gadgets ending with 'ret' or 'retn ...' are shown)")
    print("Examples:")
    print("  mov esp -include eax")
    print("  pop esi -exclude ebx\n")
    print("Type 'exit' or 'quit' to leave.\n")

    while True:
        try:
            user_input = input("search> ").strip()
            if user_input.lower() in ['exit', 'quit']:
                print("Exiting.")
                break

            main_include, extra_highlights, excludes = parse_input(user_input)
            results = search_gadgets(gadgets, main_include, extra_highlights, excludes)

            if results:
                print(f"[+] Found {len(results)} result(s):\n")
                for line in results:
                    print(line)
                print()
            else:
                print("[-] No matching gadgets found.\n")
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            print(f"[!] Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python rop_shell.py <rop_file.txt>")
        sys.exit(1)

    file_path = sys.argv[1]
    gadgets = load_rop_file(file_path)
    if gadgets:
        interactive_shell(gadgets)

if __name__ == "__main__":
    main()
