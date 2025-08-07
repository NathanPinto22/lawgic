import json

# Load raw question-answer data
with open("C:/Users/Acer/Desktop/Projects/Infipre/Chatbot/static/docs/qa_sets/motor_vehicles_tax_act_1974_qa.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Convert to AutoTrain text generation format
converted = []
for item in raw_data:
    converted.append({
        "text": f"Q: {item['question']}/nA:",
        "label": item['answer']
    })

# Save to new file
with open("C:/Users/Acer/Desktop/Projects/Infipre/Chatbot/static/docs/qa_sets/motor_vehicles_tax_act_1974_qa_formatted.json", "w", encoding="utf-8") as f:
    json.dump(converted, f, indent=2, ensure_ascii=False)
