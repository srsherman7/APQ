"""
Final shuffle to eliminate consecutive patterns while maintaining distribution
"""
import json
import random

with open('scs_module_final.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

questions = data['questions']

# Get current positions
positions = [q['options'].index(q['correct_answer']) for q in questions]

# Shuffle positions to break consecutive runs while maintaining count
random.seed(456)

# Use a smarter shuffle that avoids long runs
def shuffle_avoiding_runs(items, max_run=3):
    """Shuffle list avoiding runs longer than max_run"""
    result = []
    remaining = items[:]
    random.shuffle(remaining)
    
    for _ in range(len(items)):
        # Check last max_run items
        if len(result) >= max_run:
            recent = result[-max_run:]
            if len(set(recent)) == 1:  # All same
                # Find different value
                different = [x for x in remaining if x != recent[0]]
                if different:
                    choice = random.choice(different)
                    remaining.remove(choice)
                    result.append(choice)
                    continue
        
        # Random choice
        if remaining:
            choice = random.choice(remaining)
            remaining.remove(choice)
            result.append(choice)
    
    return result

new_positions = shuffle_avoiding_runs(positions, max_run=3)

# Apply new positions
for i, q in enumerate(questions):
    options = q['options']
    correct = q['correct_answer']
    current_pos = options.index(correct)
    target_pos = new_positions[i]
    
    if current_pos != target_pos:
        options.pop(current_pos)
        options.insert(target_pos, correct)
        q['options'] = options

# Verify
from collections import Counter
final_positions = [q['options'].index(q['correct_answer']) for q in questions]
position_counts = Counter(final_positions)

# Check consecutive
consecutive_same = 0
max_consecutive = 0
prev_pos = None
for pos in final_positions:
    if pos == prev_pos:
        consecutive_same += 1
        max_consecutive = max(max_consecutive, consecutive_same)
    else:
        consecutive_same = 1
    prev_pos = pos

print(f"Distribution:")
for pos in range(4):
    count = position_counts.get(pos, 0)
    pct = (count / len(final_positions) * 100)
    print(f"  Position {pos}: {count} ({pct:.1f}%)")

print(f"\nMax consecutive: {max_consecutive}")

# Save
with open('scs_module_final.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

if max_consecutive <= 3:
    print("✅ Perfect - No problematic patterns")
else:
    print(f"⚠️  Still has {max_consecutive} consecutive (acceptable for real exams)")
