import json
import sys


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_structure(ref, target, path=""):
    errors = []

    # Type mismatch check
    if type(ref) != type(target):
        # Allow int/float interchangeability for numbers, but report if strict JSON types differ
        if isinstance(ref, (int, float)) and isinstance(target, (int, float)):
            pass  # Acceptable number mismatch
        else:
            errors.append(
                f"[TYPE] {path}: Expected {type(ref).__name__}, got {type(target).__name__}"
            )
        return errors

    # Dictionary comparison
    if isinstance(ref, dict):
        ref_keys = set(ref.keys())
        target_keys = set(target.keys())

        missing = ref_keys - target_keys
        extra = target_keys - ref_keys

        if missing:
            for k in missing:
                errors.append(f"[MISSING] {path}.{k}")

        if extra:
            for k in extra:
                errors.append(f"[EXTRA] {path}.{k}")

        # Recursive compare for common keys
        common = ref_keys.intersection(target_keys)
        for k in common:
            errors.extend(compare_structure(ref[k], target[k], f"{path}.{k}"))

    # List comparison
    elif isinstance(ref, list):
        if not ref and not target:
            return errors

        # If target has items but ref doesn't, we can't check structure strictly unless we iterate target
        # If ref has items, use the first one as a schema template for all target items
        if ref:
            schema_template = ref[0]
            for i, item in enumerate(target):
                # We check up to first 5 items to avoid massive output
                if i >= 5:
                    break
                errors.extend(compare_structure(schema_template, item, f"{path}[{i}]"))

        # If ref is empty but target is not, strict schema definition is ambiguous but usually fine
        # We generally assume lists contain homogenous objects.

    return errors


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python compare_templates.py <ref_file> <target_file>")
        sys.exit(1)

    ref_file = sys.argv[1]
    target_file = sys.argv[2]

    print(f"Loading Reference: {ref_file}")
    print(f"Loading Target:    {target_file}")

    try:
        ref_data = load_json(ref_file)
        target_data = load_json(target_file)

        print("Comparing...")
        errors = compare_structure(ref_data, target_data, "root")

        if errors:
            print(f"\nFound {len(errors)} issues:")
            # Group errors by type to minimize noise (e.g. repeated missing keys in list items)
            # We'll just print unique error patterns (ignoring index numbers)

            unique_errors = set()
            for e in errors:
                # Remove specific list indices for grouping: [0] -> []
                # Simple regex-like replacement
                import re

                clean_e = re.sub(r"\[\d+\]", "[]", e)
                unique_errors.add(clean_e)

            for e in sorted(unique_errors):
                print(e)
        else:
            print("\n✅ No structural differences found!")

    except Exception as e:
        print(f"Error: {e}")
