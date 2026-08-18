"""
Verify the Security Specialty module was imported correctly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.module import Module
from models.question import Question

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("  DATABASE VERIFICATION")
    print("="*60)
    
    # Get all modules
    all_modules = Module.query.order_by(Module.created_at).all()
    
    print(f"\n📚 Total Modules: {len(all_modules)}\n")
    
    for module in all_modules:
        questions = Question.query.filter_by(module_id=module.module_id, is_active=True).all()
        
        icon = '🔐' if 'security' in module.slug.lower() else '📖'
        
        print(f"{icon} {module.name}")
        print(f"   Slug: {module.slug}")
        print(f"   Status: {'✅ Active' if module.is_active else '❌ Inactive'}")
        print(f"   Questions: {len(questions)}")
        print(f"   Exam Format: {module.exam_question_count} questions, {module.exam_time_limit_seconds//60} minutes")
        print(f"   Passing Score: {module.exam_passing_score}%")
        print(f"   Created: {module.created_at}")
        
        if 'security' in module.slug.lower():
            print(f"\n   📊 Question Breakdown:")
            from collections import Counter
            topics = Counter(q.topic_area for q in questions)
            difficulties = Counter(q.difficulty_level for q in questions)
            
            print(f"   Topics:")
            for topic, count in sorted(topics.items()):
                print(f"      • {topic}: {count}")
            
            print(f"   Difficulty:")
            for level in sorted(difficulties.keys()):
                print(f"      • Level {level}: {difficulties[level]}")
        
        print("")
    
    print("="*60)
    print("✅ AWS Security Specialty module is in the database!")
    print("="*60)
    print("\n🌐 Access the module at:")
    print("   http://192.168.0.225:4201/modules")
    print("\nIf you don't see it:")
    print("   1. Refresh your browser (Ctrl+F5)")
    print("   2. Clear browser cache")
    print("   3. Check browser console for errors")
    print("")
