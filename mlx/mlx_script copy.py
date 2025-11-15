from prompt_format import PromptFormatter
from json_handler import get_json, append_to_json
import os
import glob

# Path to saved file (i.e. file in which novel is saved)
existing_folder_prompt = input("Enter path to existing novel folder (hit ENTER if new novel): ")


def get_existing_novel(given_file_path):
    saved_parts = get_json(given_file_path)
    num_chunks = len(saved_parts["chunks"])
    saved_dict = {
        "prompt": saved_parts["prompt"],
        "characters": saved_parts["characters"],
        "setting": saved_parts["setting"],
        "tone": saved_parts["tone"],
        "chapters": saved_parts["chapters"],
        "prev-chunk": saved_parts["chunks"][-2] if num_chunks > 1 else '',
        "current-chunk": saved_parts["chunks"][-1] if num_chunks > 0 else '',
        "chunk": max(0, num_chunks - 1)
    }
    print("Retrieved novel data: " + str(saved_dict))
    return saved_dict


# Gets existing novel pieces (if they exist/ resuming story)
existing_novel_parts = get_existing_novel(glob.glob(os.path.join(existing_folder_prompt, "*.json"))[0]) if existing_folder_prompt else None

# Get prompt
prompt = existing_novel_parts["prompt"] if existing_folder_prompt else input("> ")

# Save prompt
folder_path = existing_folder_prompt if existing_folder_prompt else f"folder_{prompt}"
txt_file_path = f"{folder_path}/novel_{prompt}.txt"
json_file_path = f"{folder_path}/background_{prompt}.json"

if not existing_folder_prompt:
    os.makedirs(os.path.dirname(txt_file_path), exist_ok=True)
    with open(txt_file_path, "a", encoding="utf-8") as f:
        f.write("Prompt: " + prompt + "\n\n")

    append_to_json(json_file_path, {"prompt": prompt})

# Chunk into pieces - roughly 91,000 words total
num_story_pieces = 14
words_per_chunk = 6500

PromptFormatter(prompt, existing_folder_prompt, existing_novel_parts, txt_file_path, json_file_path, num_story_pieces,
                words_per_chunk).generate_novel()
