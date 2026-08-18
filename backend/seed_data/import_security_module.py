"""
Import AWS Security Specialty module directly into the database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.module import Module
from models.question import Question
import json

def import_security_module():
    app = create_app()
    
    with app.app_context():
        # Check if module already exists
        existing = Module.query.filter_by(slug='aws-security-specialty').first()
        if existing:
            print(f"Module already exists: {existing.name}")
            print(f"Questions: {existing.questions.count()}")
            return
        
        # Load the module data
        data_file = os.path.join(os.path.dirname(__file__), 'scs_module_ready.json')
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Creating module: {data['module']['name']}")
        
        # Create the module
        module = Module(
            slug=data['module']['slug'],
            name=data['module']['name'],
            description=data['module']['description'],
            icon=data['module']['icon'],
            exam_question_count=data['module']['exam_question_count'],
            exam_time_limit_seconds=data['module']['exam_time_limit_seconds'],
            exam_passing_score=data['module']['exam_passing_score'],
            topic_areas=data['module']['topic_areas'],
            is_active=True
        )
        db.session.add(module)
        db.session.flush()  # Get the module_id
        
        print(f"Module created with ID: {module.module_id}")
        print(f"Importing {len(data['questions'])} questions...")
        
        # Import questions
        question_count = 0
        for q_data in data['questions']:
            question = Question(
                module_id=module.module_id,
                question_text=q_data['question_text'],
                options=q_data['options'],
                correct_answer=q_data['correct_answer'],
                explanation=q_data['explanation'],
                memory_technique=q_data['memory_technique'],
                topic_area=q_data['topic_area'],
                difficulty_level=q_data['difficulty_level'],
                it_context_mapping=q_data.get('it_context_mapping'),
                is_active=True
            )
            db.session.add(question)
            question_count += 1
        
        db.session.commit()
        
        print(f"\n✅ SUCCESS!")
        print(f"Module: {module.name}")
        print(f"Slug: {module.slug}")
        print(f"Questions imported: {question_count}")
        print(f"\nThe module should now be visible at:")
        print(f"http://192.168.0.225:4201/modules")
        
        # Verify
        print(f"\n📊 Verification:")
        all_modules = Module.query.all()
        print(f"Total modules in database: {len(all_modules)}")
        for m in all_modules:
            q_count = Question.query.filter_by(module_id=m.module_id, is_active=True).count()
            print(f"  - {m.slug}: {q_count} questions")

if __name__ == '__main__':
    import_security_module()
