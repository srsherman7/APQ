"""
Analyze question quality metrics
"""
import json
from collections import Counter

# Load balanced questions
with open('scs_module_balanced.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

questions = data['questions']

print("\n" + "="*70)
print("  AWS SECURITY SPECIALTY - QUESTION QUALITY ANALYSIS")
print("="*70)

# Check correct answer position distribution
positions = []
for q in questions:
    options = q['options']
    correct = q['correct_answer']
    try:
        pos = options.index(correct)
        positions.append(pos)
    except ValueError:
        print(f"WARNING: Correct answer not in options for question")

position_counts = Counter(positions)
print(f"\n📊 Correct Answer Position Distribution:")
print(f"   (Should be roughly equal - no pattern)")
total = len(positions)
for pos in range(4):
    count = position_counts.get(pos, 0)
    pct = (count / total * 100) if total > 0 else 0
    bar = "█" * int(pct / 2)
    print(f"   Position {pos} (Option {chr(65+pos)}): {count:2d} ({pct:5.1f}%) {bar}")

# Check if too many consecutive same-position answers
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

print(f"\n🎯 Randomization Check:")
print(f"   Max consecutive same position: {max_consecutive}")
if max_consecutive <= 3:
    print(f"   ✅ PASS - Good randomization (≤3 is acceptable)")
else:
    print(f"   ⚠️  WARNING - Pattern detected (>{max_consecutive} consecutive)")

# Check option length distribution
correct_lengths = []
other_lengths = []

for q in questions:
    options = q['options']
    correct = q['correct_answer']
    
    for opt in options:
        if opt == correct:
            correct_lengths.append(len(opt))
        else:
            other_lengths.append(len(opt))

avg_correct = sum(correct_lengths) / len(correct_lengths)
avg_other = sum(other_lengths) / len(other_lengths)

print(f"\n📏 Option Length Analysis:")
print(f"   Average correct answer length: {avg_correct:.1f} chars")
print(f"   Average distractor length: {avg_other:.1f} chars")
print(f"   Ratio: {avg_correct/avg_other:.2f}x")

if avg_correct / avg_other < 1.15:
    print(f"   ✅ PASS - Lengths are well balanced")
else:
    print(f"   ⚠️  WARNING - Correct answers tend to be longer")

# Check longest option is correct answer
longest_is_correct = 0
for q in questions:
    options = q['options']
    correct = q['correct_answer']
    longest = max(options, key=len)
    if longest == correct:
        longest_is_correct += 1

longest_pct = (longest_is_correct / len(questions)) * 100
print(f"\n📐 Longest Option Pattern:")
print(f"   Longest option is correct: {longest_is_correct}/{len(questions)} ({longest_pct:.1f}%)")
if longest_pct < 30:
    print(f"   ✅ PASS - No obvious length bias (<30%)")
else:
    print(f"   ⚠️  WARNING - Length could be a hint (>{longest_pct:.0f}%)")

# Check explanation lengths
explanation_lengths = [len(q['explanation']) for q in questions]
avg_explanation = sum(explanation_lengths) / len(explanation_lengths)
min_explanation = min(explanation_lengths)
max_explanation = max(explanation_lengths)

print(f"\n📝 Explanation Quality:")
print(f"   Average length: {avg_explanation:.0f} chars")
print(f"   Range: {min_explanation}-{max_explanation} chars")
if min_explanation >= 100:
    print(f"   ✅ PASS - All explanations are detailed (≥100 chars)")
else:
    print(f"   ⚠️  Some explanations are too short")

# Check for memory techniques
with_memory = sum(1 for q in questions if q.get('memory_technique') and len(q['memory_technique']) > 10)
print(f"\n💭 Memory Techniques:")
print(f"   Questions with memory aids: {with_memory}/{len(questions)} ({with_memory/len(questions)*100:.1f}%)")
if with_memory == len(questions):
    print(f"   ✅ PASS - All questions include memory techniques")

# Overall quality score
quality_checks = [
    max_consecutive <= 3,
    longest_pct < 30,
    min_explanation >= 100,
    with_memory == len(questions)
]

passed = sum(quality_checks)
print(f"\n" + "="*70)
print(f"  OVERALL QUALITY SCORE: {passed}/4 checks passed")
print("="*70)

if passed == 4:
    print("  ✅ EXCELLENT - Questions meet all quality standards")
elif passed >= 3:
    print("  ✅ GOOD - Questions meet most quality standards")
else:
    print("  ⚠️  NEEDS IMPROVEMENT - Some quality issues detected")

print("")
