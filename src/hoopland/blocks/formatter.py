import json
import re

def save_compact_json(data, filepath):
    """
    Save data as JSON with standard indentation, but collapse "leaf" dictionaries and lists
    (those containing only primitive values) onto a single line.
    
    This matches the format of data/mappings/appearance-mapping.json where list items are compact.
    """
    # 1. Dump with standard indentation to get structure
    json_str = json.dumps(data, indent=4)
    
    # 2. Define regex to find leaf nodes (dicts/lists containing no nested dicts/lists)
    # Matches { ... } or [ ... ] where content does not have { [ ] }
    # This safely targets the innermost structures.
    pattern_dict = r'\{[^{}\[\]]*\}'
    pattern_list = r'\[[^{}\[\]]*\]'
    
    def collapse_match(match):
        content = match.group(0)
        # If it's already one line, leave it
        if '\n' not in content:
            return content
        # Replace newlines and extra spaces with a single space
        return re.sub(r'\s*\n\s*', ' ', content)

    # Apply collapse to dictionaries (e.g., attributes, appearance)
    json_str = re.sub(pattern_dict, collapse_match, json_str)
    
    # Apply collapse to lists (e.g., simple lists of numbers, though unlikely in this schema)
    json_str = re.sub(pattern_list, collapse_match, json_str)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(json_str)
