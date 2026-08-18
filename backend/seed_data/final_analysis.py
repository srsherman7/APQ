"""
Final quality check on randomized questions
"""
import json
from collections import Counter

with open('scs_module_final.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

questions = data['questions']

print("\n" + "="*70)
print("  FINAL QUALITY ANALYSIS - AWS SECURITY SPECIALTY")
print("="*70)

# Position distribution
positions = [q['options'].index(q['correct_answer']) for q in questions]
position_counts = Counter(positions)

print(f"\n📊 Correct Answer Position Distribution:")
total = len(positions)
for pos in range(4):
    count = position_counts.get(pos, 0)
    pct = (count / total * 100)
    bar = "█" * int(pct / 2)
    status = "✅" if 15 <= pct <= 35 else "⚠️"
    print(f"   {status} Position {pos} (Option {chr(65+pos)}): {count:2d} ({pct:5.1f}%) {bar}")

# Consecutive check
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

print(f"\n🎯 Pattern Detection:")
print(f"   Max consecutive same position: {max_consecutive}")
status = "✅" if max_consecutive <= 3 else "⚠️"
print(f"   {status} {'PASS - Well randomized' if max_consecutive <= 3 else 'WARNING - Pattern detected'}")

# Option length check
correct_lengths = []
other_lengths = []
longest_is_correct = 0

for q in questions:
    options = q['options']
    correct = q['correct_answer']
    longest = max(options, key=len)
    
    if longest == correct:
        longest_is_correct += 1
    
    for opt in options:
        if opt == correct:
            correct_lengths.append(len(opt))
        else:
            other_lengths.append(len(opt))

avg_correct = sum(correct_lengths) / len(correct_lengths)
avg_other = sum(other_lengths) / len(other_lengths)
ratio = avg_correct / avg_other

print(f"\n📏 Option Length Fairness:")
print(f"   Avg correct answer: {avg_correct:.1f} chars")
print(f"   Avg distractors: {avg_other:.1f} chars")
print(f"   Length ratio: {ratio:.2f}x")
status = "✅" if ratio < 1.20 else "⚠️"
print(f"   {status} {'PASS - Balanced' if ratio < 1.20 else 'WARNING - Correct answers longer'}")

longest_pct = (longest_is_correct / len(questions)) * 100
print(f"\n📐 Longest = Correct Pattern:")
print(f"   {longest_is_correct}/{len(questions)} ({longest_pct:.1f}%)")
status = "✅" if longest_pct < 30 else "⚠️"
print(f"   {status} {'PASS - No length bias' if longest_pct < 30 else 'WARNING - Length is a hint'}")

# Quality checks summary
print(f"\n" + "="*70)
print("  QUALITY CHECKLIST")
print("="*70)

checks = {
    "Answer position randomized": max_consecutive <= 3,
    "No position pattern detected": all(15 <= (position_counts.get(i, 0)/total*100) <= 35 for i in range(4)),
    "Option lengths balanced": ratio < 1.20,
    "No longest-is-correct bias": longest_pct < 30,
    "All explanations detailed": all(len(q['explanation']) >= 100 for q in questions),
    "All have memory techniques": all(q.get('memory_technique') for q in questions)
}

for check, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"   {status} {check}")

passed_count = sum(checks.values())
total_checks = len(checks)

print(f"\n" + "="*70)
if passed_count == total_checks:
    print(f"  ✅ PERFECT SCORE: {passed_count}/{total_checks} checks passed")
    print("  Questions are ready for production!")
elif passed_count >= total_checks - 1:
    print(f"  ✅ EXCELLENT: {passed_count}/{total_checks} checks passed")
    print("  Questions meet quality standards")
else:
    print(f"  ⚠️  GOOD: {passed_count}/{total_checks} checks passed")
    print("  Minor improvements recommended")
print("="*70 + "\n")
