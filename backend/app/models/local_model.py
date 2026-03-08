# backend/app/models/local_model.py
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class LocalLLM:
    """
    Minimal wrapper for a small local LLM suitable for CPU/GPU.
    """
    def __init__(self, model_name="Qwen/Qwen3-0.6B"):
        print("Loading small LLM...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto" if self.device=="cuda" else None,
            low_cpu_mem_usage=True
        )
        self.model.to(self.device)
        print(f"Model loaded on {self.device}.")

    def generate(self, prompt, max_length=128):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_length=max_length,
            do_sample=True,
            top_p=0.9,
            temperature=0.7
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
