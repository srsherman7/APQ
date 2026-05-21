#!/usr/bin/env bash
# Render build script
set -e

echo "=== Installing Python dependencies ==="
pip install -r backend/requirements.txt
pip install gunicorn sqlalchemy-libsql

echo "=== Installing Node dependencies ==="
cd frontend
npm install
echo "=== Building Angular (production) ==="
npx ng build --configuration production
cd ..

echo "=== Seeding database ==="
cd backend
python -c "
import json
from app import create_app
from extensions import db
from models.module import Module
from models.question import Question

app = create_app()
with app.app_context():
    db.create_all()
    module = Module.query.filter_by(slug='cloud-practitioner').first()
    if not module:
        module = Module(
            slug='cloud-practitioner',
            name='AWS Cloud Practitioner',
            description='Prepare for the AWS Certified Cloud Practitioner exam.',
            icon='cloud',
            exam_question_count=65,
            exam_time_limit_seconds=5400,
            exam_passing_score=70.0,
            topic_areas=['Cloud Concepts', 'Security and Compliance', 'Technology', 'Billing and Pricing'],
        )
        db.session.add(module)
        db.session.commit()
    with open('seed_data/questions.json', encoding='utf-8') as f:
        questions = json.load(f)
    count = 0
    for q in questions:
        if not Question.query.filter_by(question_text=q['question_text']).first():
            db.session.add(Question(
                module_id=module.module_id,
                question_text=q['question_text'], options=q['options'],
                correct_answer=q['correct_answer'], explanation=q['explanation'],
                memory_technique=q['memory_technique'], topic_area=q['topic_area'],
                difficulty_level=q['difficulty_level'],
                it_context_mapping=q.get('it_context_mapping'), is_active=True
            ))
            count += 1
    db.session.commit()
    total = Question.query.filter_by(is_active=True).count()
    print(f'Seeded {count} new questions. Total: {total}')
"
cd ..

echo "=== Build complete ==="
