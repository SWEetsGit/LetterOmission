from generator import LLMGenerator
import re
from json_handler import get_json, append_to_json, append_to_json_obj, append_new_element_to_json_obj


# Changes the string chapters output into a list
def chapters_str_to_lst(chap_text):
    # Find where the first numbered item starts
    match = re.search(r'\d+\.\s*', chap_text)
    if match:
        # Keep only the part starting from the first number
        numbered_part = chap_text[match.start():]
        # Split on numbers followed by a period
        items = re.split(r'\d+\.\s*', numbered_part)
        # Remove any empty strings from the list
        return [item.strip() for item in items if item.strip()]
    else:
        # If no numbered list found, return an empty list
        return []


# Load the background prompts
background_prompts = get_json('prompt_background.json')
print("Background prompts loaded.")


class PromptFormatter:
    def __init__(self, prompt, existing_file_prompt, existing_novel_parts, txt_file_path, json_file_path, num_story_pieces,
                 words_per_chunk):
        self.prompt = prompt
        self.existing_file_prompt = existing_file_prompt
        self.existing_novel_parts = existing_novel_parts
        self.txt_file_path = txt_file_path
        self.json_file_path = json_file_path
        self.num_story_pieces = num_story_pieces
        self.words_per_chunk = words_per_chunk

        self.llm_generator = LLMGenerator()
        self.starter_prompt = background_prompts['mainPrompt']['starterPrompt'].format(prompt)

    # Used for enforcing who the characters are, setting, and tone
    def generate_story_background(self):
        if self.existing_file_prompt:
            return self.existing_novel_parts["characters"], self.existing_novel_parts["setting"], \
                   self.existing_novel_parts[
                       "tone"]

        character_length = background_prompts['characters']['characterLength']
        setting_length = background_prompts['setting']['settingLength']
        tone_length = background_prompts['tone']['toneLength']

        character_prompt = background_prompts['characters']['characterPrompt'].format(self.starter_prompt)
        character_add = background_prompts['characters']['characterAdd']
        setting_prompt = background_prompts['setting']['settingPrompt'].format(self.starter_prompt)
        setting_add = background_prompts['setting']['settingAdd']
        tone_prompt = background_prompts['tone']['tonePrompt'].format(self.starter_prompt)
        tone_add = background_prompts['tone']['toneAdd']

        characters = self.llm_generator.generation(f"{character_prompt} {character_add} {character_length}")
        print(f"\nCharacters: {characters}\n")
        setting = self.llm_generator.generation(
            f"{setting_prompt} {setting_add} Here are a list of characters in this story. Do not reference them in the generation: {characters} {setting_length}")
        print(f"\nSetting: {setting}\n")
        tone = self.llm_generator.generation(
            f"{tone_prompt} {tone_add} Here are a list of characters and the setting in this story. Do not reference them in the generation: Characters: {characters} Setting: {setting} {tone_length}")
        print(f"\nTone: {tone}\n")

        with open(self.txt_file_path, "a", encoding="utf-8") as f:
            f.write("Characters: " + characters + "\n\n")
            f.write("Setting: " + setting + "\n\n")
            f.write("Tone: " + tone + "\n\n")

        append_to_json(self.json_file_path, {"characters": characters, "setting": setting, "tone": tone})

        return characters, setting, tone

    # Generates the chapters
    def chunk_text(self, background_prompt):
        if self.existing_file_prompt:
            return self.existing_novel_parts["chapters"]

        general_prompt = background_prompts['mainPrompt']['chunkGeneration']['generalPromptOld'].format(
            self.starter_prompt,
            self.num_story_pieces,
            self.words_per_chunk,
            self.num_story_pieces,
            self.num_story_pieces)

        no_repeat = background_prompts['mainPrompt']['chunkGeneration']['noRepeat']

        str_all_chapters = self.llm_generator.generation(f"{general_prompt} {background_prompt} {no_repeat}")
        all_chapters = chapters_str_to_lst(str_all_chapters)
        print('Initial chapters generated.')

        # Sometimes the LLM won't generate enough sentences (and sometimes it may generate more, which will be ignored)
        # Therefore, reiterate the prompt
        while len(all_chapters) < self.num_story_pieces:
            continue_prompt = f"Here are the first chapters in this story, continue where they left off: {str_all_chapters}"
            num_chapters_left = self.num_story_pieces - len(all_chapters)
            print("Remaining chapters left: " + str(num_chapters_left))
            modified_general_prompt = background_prompts['mainPrompt']['chunkGeneration']['generalPromptOld'].format(
                self.starter_prompt,
                num_chapters_left,
                self.words_per_chunk,
                num_chapters_left,
                num_chapters_left)
            new_chapters = self.llm_generator.generation(f"{modified_general_prompt} {background_prompt} {no_repeat} {continue_prompt}")
            str_all_chapters += (" " + new_chapters)
            all_chapters += chapters_str_to_lst(new_chapters)
            print("Number of total chapters: " + str(len(all_chapters)))

        print("All Chapters:\n" + '\n'.join(f"{i+1}. {chapter}" for i, chapter in enumerate(all_chapters)) + "\n\n")

        with open(self.txt_file_path, "a", encoding="utf-8") as f:
            f.write("Chapters: \n" + '\n'.join(all_chapters) + "\n\n")

        append_to_json(self.json_file_path, {"chapters": all_chapters})

        return all_chapters

    def chunk_generation(self, prev_chunk, chapter_number, chapter_sentence, background_prompt, prior_story='', gen_chap_header=True):
        # Generate chapter
        if gen_chap_header:
            with open(self.txt_file_path, "a", encoding="utf-8") as f:
                f.write(f"CHAPTER {chapter_number}: {chapter_sentence}\n\n")
            append_new_element_to_json_obj(self.json_file_path, "chunks")

        # Generate text
        chunk_whole_text = prior_story
        constant_text = background_prompts['mainPrompt']['mainGeneration']['constantText']
        chapter_text = background_prompts['mainPrompt']['mainGeneration']['chapterText'].format(chapter_sentence)
        additional_prompting = background_prompts['mainPrompt']['mainGeneration']['additionalPrompting']
        initial_prompt = True
        continuation_text = background_prompts['mainPrompt']['mainGeneration']['continuationTextTrue'].format(
            prev_chunk) if prev_chunk else ""  # text from previous chunk
        english_prompt = background_prompts['mainPrompt']['mainGeneration']['englishPrompt']
        present_tense = "All text should be in the present tense, if possible."  # might remove later

        while len(chunk_whole_text.split()) < self.words_per_chunk:
            # Format as a chat-style input (for instruct-tuned models)
            if initial_prompt:
                full_prompt = f"{self.prompt} {chapter_text} {continuation_text[-1000:]} {constant_text}"
            else:
                full_prompt = f"{self.prompt} Here is the first part of the story: {chunk_whole_text[-1000:]} {constant_text}"  # takes last 1,000 tokens - might want to change logic for more accuracy
            full_prompt += (" " + english_prompt)
            full_prompt += (" " + additional_prompting)
            full_prompt += (" " + background_prompt)
            full_prompt += (" " + present_tense)

            response = self.llm_generator.generation(full_prompt)
            print(f"Current Response: \n{response}\n")

            # Open file in append mode and write
            with open(self.txt_file_path, "a", encoding="utf-8") as f:
                f.write("\t" + response + "\n")

            append_to_json_obj(self.json_file_path, "chunks", response)

            # Update variables
            initial_prompt = False
            chunk_whole_text += ("\t" + response + "\n")

        with open(self.txt_file_path, "a", encoding="utf-8") as f:
            f.write("\n\n")
        return chunk_whole_text

    def generate_novel(self):
        whole_text = ""
        current_chunk = self.existing_novel_parts["chunk"] if self.existing_file_prompt else 0

        background_tuple = self.generate_story_background()
        characters = background_tuple[0]
        setting = background_tuple[1]
        tone = background_tuple[2]
        background_prompt = background_prompts['mainPrompt']['mainGeneration']['backgroundPrompt'].format(characters,
                                                                                                          setting,
                                                                                                          tone)

        parts = self.chunk_text(background_prompt)
        previous_text_chunk = self.existing_novel_parts["prev-chunk"] if self.existing_file_prompt else ""
        current_text_chunk = self.existing_novel_parts["current-chunk"] if self.existing_file_prompt else ""

        # This condition is if we are reloading the existing novel; we are finishing off the chapter
        if self.existing_file_prompt:
            regen_text = current_text_chunk
            current_text_chunk = self.chunk_generation(previous_text_chunk, current_chunk + 1, parts[current_chunk],
                                                       background_prompt, prior_story=regen_text, gen_chap_header=False)

            # Make sure not to include a bit of that chapter that was already added to the text file
            whole_text += current_text_chunk[len(regen_text):]
            current_chunk += 1

        while current_chunk < self.num_story_pieces:
            previous_text_chunk = current_text_chunk

            current_text_chunk = self.chunk_generation(previous_text_chunk, current_chunk + 1, parts[current_chunk],
                                                       background_prompt)

            whole_text += current_text_chunk
            current_chunk += 1

            print(f"Chunk {current_chunk} complete!")

        print("Whole Generation: " + whole_text)
