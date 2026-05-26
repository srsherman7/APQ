#!/usr/bin/env python3
"""
Standalone Module Preparation Tool

Validates, balances, and packages a question set for import into the
AWS Certification Practice Platform.

Usage:
    python tools/prepare_module.py input.json --output ready_to_import.json

Input format (input.json):
{
    "module": {
        "name": "CompTIA Security+",
        "slug": "comptia-security-plus",  (optional — auto-generated)
        "description": "Prepare for the CompTIA Security+ SY0-701 exam",
        "icon": "security",
        "exam_question_count": 90,
        "exam_time_limit_seconds": 5400,
        "exam_passing_score": 75.0,
        "topic_areas": ["General Security Concepts", "Threats", "Architecture", "Operations", "Program Management"]
    },
    "questions": [
        {
            "question_text": "...",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "B",
            "explanation": "...",
            "memory_technique": "...",
            "topic_area": "General Security Concepts",
            "difficulty_level": 2,
            "it_context_mapping": "..." (optional)
        },
        ...
    ]
}

Output: A validated, balanced JSON file ready for POST /api/modules/<slug>/import
"""
import json
import sys
import random
import re
import argparse
from collections import Counter


def validate_module(module: dict) -> list:
    """Validate module configuration. Returns list of errors."""
    errors = []
    required = ['name', 'exam_question_count', 'exam_time_limit_seconds', 'exam_passing_score', 'topic_areas']
    for field in required:
        if field not in module:
            errors.append(f'Module missing required field: {field}')
    if 'topic_areas' in module:
        if not isinstance(module['topic_areas'], list) or len(module['topic_areas']) == 0:
            errors.append('Module topic_areas must be a non-empty array')
    if 'exam_passing_score' in module:
        score = module['exam_passing_score']
        if not (0 < score <= 100):
            errors.append(f'exam_passing_score must be between 0 and 100, got {score}')
    return errors


def validate_question(q: dict, index: int, topic_areas: list) -> list:
    """Validate a single question. Returns list of errors."""
    errors = []
    required = ['question_text', 'options', 'correct_answer', 'explanation', 'memory_technique', 'topic_area', 'difficulty_level']
    for field in required:
        if field not in q or not q[field]:
            errors.append(f'Question {index}: missing or empty field "{field}"')

    if 'options' in q:
        if not isinstance(q['options'], list):
            errors.append(f'Question {index}: options must be an array')
        elif len(q['options']) < 2 or len(q['options']) > 6:
            errors.append(f'Question {index}: options must have 2-6 items, got {len(q["options"])}')

    if 'correct_answer' in q and 'options' in q:
        if isinstance(q['options'], list) and q['correct_answer'] not in q['options']:
            errors.append(f'Question {index}: correct_answer "{q["correct_answer"][:50]}..." not found in options')

    if 'difficulty_level' in q:
        if not isinstance(q['difficulty_level'], int) or q['difficulty_level'] < 1 or q['difficulty_level'] > 5:
            errors.append(f'Question {index}: difficulty_level must be integer 1-5')

    if 'topic_area' in q and topic_areas:
        if q['topic_area'] not in topic_areas:
            errors.append(f'Question {index}: topic_area "{q["topic_area"]}" not in module topics')

    if 'question_text' in q and len(q['question_text']) > 1000:
        errors.append(f'Question {index}: question_text exceeds 1000 characters')

    if 'explanation' in q and isinstance(q['explanation'], str) and len(q['explanation']) < 50:
        errors.append(f'Question {index}: explanation must be at least 50 characters')

    return errors


def balance_options(questions: list) -> tuple:
    """
    Balance option lengths so the correct answer isn't identifiable by length.
    Returns (balanced_questions, fix_count).
    """
    extensions = [
        ' with automatic scaling and management',
        ' across multiple availability zones',
        ' with built-in redundancy and failover',
        ' for enterprise workloads and applications',
        ' with integrated monitoring and alerting',
        ' using managed infrastructure services',
        ' with comprehensive security controls',
        ' supporting multiple deployment options',
        ' with high availability and fault tolerance',
        ' for both development and production use',
    ]

    fixed = 0
    for q in questions:
        options = q['options']
        correct = q['correct_answer']
        correct_len = len(correct)

        distractor_lens = [(i, len(o)) for i, o in enumerate(options) if o != correct]
        if not distractor_lens:
            continue

        max_distractor = max(l for _, l in distractor_lens)
        if correct_len <= max_distractor:
            continue

        # Find shortest distractor and extend it
        short = [(i, o) for i, o in enumerate(options) if o != correct and len(o) < correct_len * 0.8]
        if short:
            idx, opt = min(short, key=lambda x: len(x[1]))
            new_opt = opt.rstrip('.') + random.choice(extensions)
            while len(new_opt) < correct_len:
                new_opt += random.choice([' at scale', ' globally', ' securely'])
            options[idx] = new_opt
            fixed += 1

    return questions, fixed


def main():
    parser = argparse.ArgumentParser(description='Prepare a module for import into the practice platform')
    parser.add_argument('input', help='Input JSON file with module config and questions')
    parser.add_argument('--output', '-o', help='Output JSON file (default: <input>_ready.json)')
    parser.add_argument('--no-balance', action='store_true', help='Skip option length balancing')
    parser.add_argument('--stats', action='store_true', help='Print statistics only, no output file')
    args = parser.parse_args()

    # Load input
    try:
        with open(args.input, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f'ERROR: File not found: {args.input}')
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f'ERROR: Invalid JSON: {e}')
        sys.exit(1)

    module = data.get('module', {})
    questions = data.get('questions', [])

    print(f'\n{"="*60}')
    print(f'  Module Preparation Tool')
    print(f'{"="*60}')
    print(f'  Module: {module.get("name", "Unknown")}')
    print(f'  Questions: {len(questions)}')
    print(f'{"="*60}\n')

    # Validate module
    module_errors = validate_module(module)
    if module_errors:
        print('MODULE ERRORS:')
        for e in module_errors:
            print(f'  ✗ {e}')
        sys.exit(1)
    print('✓ Module configuration valid')

    # Generate slug if missing
    if 'slug' not in module:
        module['slug'] = re.sub(r'[^a-z0-9]+', '-', module['name'].lower()).strip('-')
        print(f'  Generated slug: {module["slug"]}')

    # Validate questions
    topic_areas = module.get('topic_areas', [])
    all_errors = []
    for i, q in enumerate(questions):
        errs = validate_question(q, i, topic_areas)
        all_errors.extend(errs)

    if all_errors:
        print(f'\nQUESTION ERRORS ({len(all_errors)}):')
        for e in all_errors[:20]:
            print(f'  ✗ {e}')
        if len(all_errors) > 20:
            print(f'  ... and {len(all_errors) - 20} more')
        sys.exit(1)
    print(f'✓ All {len(questions)} questions valid')

    # Balance options
    if not args.no_balance:
        questions, fix_count = balance_options(questions)
        longest_correct = sum(1 for q in questions if len(q['correct_answer']) == max(len(o) for o in q['options']))
        pct = 100 * longest_correct // len(questions) if questions else 0
        print(f'✓ Options balanced: fixed {fix_count} questions (correct is longest in {pct}% — target <30%)')
    else:
        print('⊘ Option balancing skipped')

    # Statistics
    diff_counts = Counter(q['difficulty_level'] for q in questions)
    topic_counts = Counter(q['topic_area'] for q in questions)

    print(f'\n  Difficulty distribution:')
    for level in sorted(diff_counts.keys()):
        print(f'    Level {level}: {diff_counts[level]}')

    print(f'\n  Topic distribution:')
    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f'    {topic}: {count}')

    if args.stats:
        print('\n  (Stats only — no output file generated)')
        return

    # Write output
    output_path = args.output or args.input.replace('.json', '_ready.json')
    output_data = {
        'module': module,
        'questions': questions
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f'\n✓ Output written to: {output_path}')
    print(f'\n  To import into the platform:')
    print(f'  1. Create the module:')
    print(f'     POST /api/modules/create')
    print(f'     Body: {json.dumps(module, indent=2)[:200]}...')
    print(f'  2. Import questions:')
    print(f'     POST /api/modules/{module["slug"]}/import')
    print(f'     Body: {{"questions": [...{len(questions)} items...]}}')
    print(f'\n{"="*60}\n')


if __name__ == '__main__':
    main()
