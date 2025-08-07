from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, TaskType
import torch

# === CONFIG ===
MODEL_ID = "meta-llama/Meta-Llama-3.1-8B-Instruct"  # you must have access
DATA_PATH = "static/docs/discarded/data.json"  # your dataset
PUSH_TO_HUB = True
HF_USERNAME = "nlearn"  # replace with your Hugging Face username
HUB_MODEL_ID = f"{HF_USERNAME}/legal-llama3"

# === Load & Preprocess Dataset ===
dataset = load_dataset("json", data_files=DATA_PATH, split="train")

def format_prompt(example):
    prompt = f"{example['instruction']}\n\n{example['question']}\nA:"
    output = example['answer']
    full_text = prompt + " " + output
    tokens = tokenizer(full_text, padding="max_length", truncation=True, max_length=512)
    tokens["labels"] = tokens["input_ids"].copy()
    return tokens

# === Load Tokenizer & Model ===
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    low_cpu_mem_usage=True
)

# === Apply LoRA ===
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    task_type=TaskType.CAUSAL_LM,
    lora_dropout=0.1,
    bias="none"
)
model = get_peft_model(model, lora_config)

# === Tokenize ===
tokenized = dataset.map(format_prompt, remove_columns=dataset.column_names)

# === Training ===
training_args = TrainingArguments(
    output_dir=HUB_MODEL_ID,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    learning_rate=2e-5,
    save_strategy="epoch",
    fp16=True,
    logging_dir="./logs",
    push_to_hub=PUSH_TO_HUB,
    hub_model_id=HUB_MODEL_ID,
    hub_strategy="every_save"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    tokenizer=tokenizer
)

trainer.train()

if PUSH_TO_HUB:
    trainer.push_to_hub()
else:
    model.save_pretrained("legal-llama3")
    tokenizer.save_pretrained("legal-llama3")
