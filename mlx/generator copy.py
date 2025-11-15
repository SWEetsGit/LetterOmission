from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler, make_logits_processors
from mask_script import MaskProcessor
from spell_checker_script import clean_text
import mlx.core as mx


class LLMGenerator:
    def __init__(self):
        # Load the model and tokenizer
        self.model, self.tokenizer = load(
            # "mlx-community/Mistral-Small-3.1-24B-Instruct-2503-4bit"
            # "mlx-community/deepseek-coder-33b-instruct"
            # "mlx-community/Llama-3-70B-Instruct-Gradient-262k-2bit"
            # "mlx-community/gpt-oss-20b-MXFP4-Q4"
            # "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
            # "mlx-community/Llama-3.3-70B-Instruct-4bit"
            # "mlx-community/Meta-Llama-3.1-70B-Instruct-4bit"
            # "cnfusion/Llama-3.1-Nemotron-70B-Instruct-HF-Q2-mlx"
            # "mlx-community/Qwen3-32B-4bit"
            # "deepseek-ai/DeepSeek-R1-Distill-Llama-70B"
            # "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
            # "mlx-community/Llama-3.2-3B-Instruct"
            "mlx-community/Llama-3.1-8B-Instruct"
            # "mlx-community/Meta-Llama-3.1-8B-Instruct-8bit"
            # "mlx-community/CodeLlama-13b-Instruct-hf-4bit-MLX"
            # "mlx-community/GLM-4.5-Air-4bit"
            # "mlx-community/quantized-gemma-7b-it"
            # "mlx-community/SmolVLM2-500M-Video-Instruct-mlx"
            # "mlx-community/lille-130m-instruct-fp16"
        )
        print("Model and tokenizer loaded.")

        # self.omit_list = "zqjxkvbpgyfmw" # least frequent in texts
        # self.omit_list = "qjxzwkvfybhmp" # least frequent in dictionaries
        # self.omit_list = "zqxjkvcdugmpy"  # chat gpt recommendation
        # self.omit_list = 'e'
        self.omit_list = ''
        self.logits_processors = [MaskProcessor(self.tokenizer, self.omit_list).get_masked_tokens()] + make_logits_processors(
            repetition_penalty=1.2)

    # Generates the responses from the LLM
    def generation(self, gen_prompt):
        messages = [{"role": "user", "content": f"{gen_prompt} Most importantly of all, make sure to generate output using normal and proper English. /no_think"}]
        chat_input = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True
        )

        text = generate(
            self.model,
            self.tokenizer,
            prompt=chat_input,
            verbose=False,
            max_tokens=5000,
            sampler=make_sampler(temp=0.9, top_p=0.9),
            # no_repeat_ngram_size=4,  # not available for mlx - functionality: prevents same 4-token phrase repetition
            logits_processors=self.logits_processors
        )

        mx.clear_cache()
        return clean_text(text.strip(), self.omit_list)
