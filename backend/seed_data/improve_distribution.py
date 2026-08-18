"""
Final improvements: better randomization and shorten some correct answers
"""
import json
import random

with open('scs_module_final.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Applying final improvements...")

# Better randomization using Fisher-Yates shuffle for positions
questions = data['questions']

# Create target distribution (close to 25% each)
target_positions = [0, 1, 2, 3] * 13  # 52 questions = 13 of each
random.seed(123)  # Different seed for better distribution
random.shuffle(target_positions)

print(f"Redistributing {len(questions)} questions...")

for i, q in enumerate(questions):
    options = q['options']
    correct = q['correct_answer']
    current_pos = options.index(correct)
    target_pos = target_positions[i]
    
    if current_pos != target_pos:
        # Remove correct from current position
        options.pop(current_pos)
        # Insert at target position
        options.insert(target_pos, correct)
        q['options'] = options

# Verify distribution
from collections import Counter
positions = [q['options'].index(q['correct_answer']) for q in questions]
position_counts = Counter(positions)

print(f"\nNew distribution:")
for pos in range(4):
    count = position_counts.get(pos, 0)
    pct = (count / len(positions) * 100)
    print(f"  Position {pos}: {count} ({pct:.1f}%)")

# Save
with open('scs_module_final.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved improved version")
