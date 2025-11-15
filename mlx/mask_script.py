from transformers import LogitsProcessor
import string


# Token masking setup
class MaskCreator:
    def __init__(self, tokenizer, omit_list):
        self.tokenizer = tokenizer
        # Letters to omit
        self.omit_list = omit_list
        self.special_tokens = self.tokenizer.all_special_ids
        self.n_tokens = self.tokenizer.vocab_size

    # Remove non-English letters and most punctuation - disallowed tokens
    def remove_unneeded_chars(self):
        allowed_chars = string.ascii_letters + string.digits + "!\"$\',.;?" + " \n"
        allowed_tokens = []

        for i in range(self.tokenizer.vocab_size):
            token_str = self.tokenizer.decode([i])
            if all(ch in allowed_chars for ch in token_str):
                allowed_tokens.append(i)

        return [
            i for i in range(self.tokenizer.vocab_size)
            if i not in allowed_tokens and i not in self.tokenizer.all_special_ids
        ]

    def detect_unwanted_letters(self, token_str):
        omit_letters = "".join([o.upper() + o.lower() for o in self.omit_list])
        return any(c in omit_letters for c in token_str)

    def generate_mask_indices(self):
        return [
            i for i in range(self.n_tokens)
            if self.detect_unwanted_letters(self.tokenizer.decode([i])) and i not in self.special_tokens
        ]

    def get_all_masked_tokens(self):
        # all characters to mask
        final_mask = list(set(self.generate_mask_indices()) | set(self.remove_unneeded_chars()))

        print(f"Total number of models tokens: {self.n_tokens:,}")
        print(f"Masked total number of tokens: {len(final_mask):,}")

        return final_mask


class MaskLogits(LogitsProcessor):
    def __init__(self, mask_indices):
        self.mask_indices = mask_indices

    def __call__(self, input_ids, scores):
        scores[:, self.mask_indices] = -float("inf")
        return scores


# Only have to use this class outside this script
class MaskProcessor:
    def __init__(self, tokenizer, omit_list):
        self.tokenizer = tokenizer
        self.omit_list = omit_list

    def get_masked_tokens(self):
        mask_creator = MaskCreator(self.tokenizer, self.omit_list)
        return MaskLogits(mask_creator.get_all_masked_tokens())

