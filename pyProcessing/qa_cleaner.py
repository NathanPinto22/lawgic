import json

def clean_qa():
    cleaned_pairs = []
    with open("C:/Users/Acer/Desktop/Projects/Infipre/Chatbot/static/docs/acts/entertainment_tax_act_1964_qa.json", "r", encoding="UTF-8") as f:
        qa_pairs = json.load(f)
        for pair in qa_pairs:
            if pair["question"] == "..." or pair["answer"] == "...":
                continue
            else:
                cleaned_pairs.append(pair)
        f.close()

    with open("C:/Users/Acer/Desktop/Projects/Infipre/Chatbot/static/docs/acts/entertainment_tax_act_1964_qa2.json", "w", encoding="UTF-8") as f:
        json.dump(cleaned_pairs, f)