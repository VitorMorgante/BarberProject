import re
import sys
from pathlib import Path

def validate_requirements_file():
    doc_path = Path(__file__).resolve().parent.parent / 'docs' / 'DELACRUZ_REQUIREMENTS_402.md'
    if not doc_path.exists():
        print(f"ERROR: {doc_path} does not exist.")
        return False

    content = doc_path.read_text(encoding='utf-8')
    pattern = r'\|\s*REQ-(\d{3})\s*\|'
    matches = re.findall(pattern, content)

    # Filter unique in order of occurrence
    seen = set()
    req_numbers = []
    duplicates = []
    for m in matches:
        num = int(m)
        if num in seen:
            if num not in duplicates:
                duplicates.append(num)
        else:
            seen.add(num)
            req_numbers.append(num)

    total_found = len(seen)
    missing = [i for i in range(1, 403) if i not in seen]

    print(f"=== DELACRUZ REQUIREMENTS VALIDATION ===")
    print(f"Total Unique REQs Found: {total_found} / 402")
    print(f"Duplicates: {len(duplicates)} -> {duplicates[:10] if duplicates else 'None'}")
    print(f"Missing REQs: {len(missing)} -> {missing[:10] if missing else 'None'}")

    # Check status distribution
    valid_statuses = [
        'EXISTING_VALIDATED', 'IMPLEMENTED', 'PARTIAL',
        'PLANNED', 'BLOCKED_EXTERNAL', 'BLOCKED_TECHNICAL'
    ]
    status_counts = {s: 0 for s in valid_statuses}
    
    for line in content.splitlines():
        if '| REQ-' in line or '|REQ-' in line:
            for s in valid_statuses:
                if f"| {s} " in line or f"|{s}|" in line or f"| {s}|" in line:
                    status_counts[s] += 1
                    break

    print("\nStatus Distribution:")
    for s, c in status_counts.items():
        print(f"  - {s}: {c}")

    if total_found == 402 and len(missing) == 0:
        print("\nSUCCESS: All 402 requirements are tracked and valid!")
        return True
    else:
        print("\nFAILURE: Requirements matrix does not have all 402 items.")
        return False

if __name__ == '__main__':
    success = validate_requirements_file()
    sys.exit(0 if success else 1)
