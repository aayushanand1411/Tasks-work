import json

def extract_special_instructions(input_file, output_file):
    # Load JSON data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    prompts = {}
    count = 1

    # Loop through each entry in the input JSON
    for entry in data:
        if 'special_instructions' in entry and entry['special_instructions']:
            # Split by double newline
            parts = entry['special_instructions'].strip().split("\n\n")
            
            # Store each part as a separate prompt
            for part in parts:
                key = f"Prompt_{count}"
                prompts[key] = part.strip()
                count += 1

    # Write the extracted prompts to a new JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, indent=4, ensure_ascii=False)

    print(f"✅ Extracted {count - 1} prompts and saved to '{output_file}'")

# Example usage
extract_special_instructions(r"13oct/v3/questions_data2.json", r"13oct/v3/prompt2.json")
