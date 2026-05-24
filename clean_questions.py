import json

# Load questions
with open('app/resources/questions.json', 'r', encoding='utf-8') as f:
    qdata = json.load(f)

all_loaded = qdata['questions']

# Keep only original questions (no variation key)
original_questions = [q for q in all_loaded if 'variation' not in q]

print(f"Original questions: {len(original_questions)}")

# Save only original questions
qdata['questions'] = original_questions
with open('app/resources/questions.json', 'w', encoding='utf-8') as f:
    json.dump(qdata, f, ensure_ascii=False, indent=2)

print(f"Saved {len(original_questions)} original questions to app/resources/questions.json")
