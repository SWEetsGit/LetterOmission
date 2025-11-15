from symspellpy import SymSpell, Verbosity

# spell checker (sometimes model will output words that don't exist - some of them can be corrected without adding omitted letters)
sym_spell = SymSpell(max_dictionary_edit_distance=2)
sym_spell.load_dictionary("./word_dictionary.txt", term_index=0, count_index=1)


def clean_text(text, omit_list):
    corrected_words = []
    for word in text.split():
        if not word.isalpha():
            corrected_words.append(word)
            continue
        suggestions = sym_spell.lookup(word.lower(), Verbosity.CLOSEST)
        if suggestions and not any(ch in omit_list for ch in suggestions[0].term):
            term = suggestions[0].term
            new_word = term.capitalize() if word[0].isupper() else term
            corrected_words.append(new_word)
        else:
            corrected_words.append(word)
    return " ".join(corrected_words)