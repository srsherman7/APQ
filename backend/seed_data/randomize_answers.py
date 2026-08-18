"""
Randomize correct answer positions to prevent patterns
"""
import json
import random

# Load balanced questions
with open('scs_module_balanced.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Randomizing correct answer positions...")
print(f"Total questions: {len(data['questions'])}")

# Set seed for reproducibility but ensure randomness
random.seed(42)

randomized_count = 0
for q in data['questions']:
    options = q['options']
    correct = q['correct_answer']
    
    # Find current position
    current_pos = options.index(correct)
    
    # Choose a random new position (0-3)
    new_pos = random.randint(0, 3)
    
    # If different position, shuffle
    if new_pos != current_pos:
        # Remove correct answer
        options.remove(correct)
        # Insert at new position
        options.insert(new_pos, correct)
        # Update the list
        q['options'] = options
        q['correct_answer'] = correct  # Still the same answer, just different position
        randomized_count += 1

print(f"Randomized: {randomized_count} questions")

# Verify randomization
from collections import Counter
positions = []
for q in data['questions']:
    pos = q['options'].index(q['correct_answer'])
    positions.append(pos)

position_counts = Counter(positions)
print(f"\nNew distribution:")
for pos in range(4):
    count = position_counts.get(pos, 0)
    pct = (count / len(positions) * 100)
    print(f"  Position {pos} (Option {chr(65+pos)}): {count:2d} ({pct:5.1f}%)")

# Check consecutive pattern
consecutive_same = 0
max_consecutive = 0
prev_pos = None
for pos in positions:
    if pos == prev_pos:
        consecutive_same += 1
        max_consecutive = max(max_consecutive, consecutive_same)
    else:
        consecutive_same = 1
    prev_pos = pos

print(f"\nMax consecutive same position: {max_consecutive}")

# Save
with open('scs_module_final.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved to: scs_module_final.json")

if max_consecutive <= 3:
    print("✅ Randomization successful - no patterns detected")
else:
    print(f"⚠️  Still has pattern of {max_consecutive} consecutive")
