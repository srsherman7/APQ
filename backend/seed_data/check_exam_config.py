"""
Check exam configuration for Security Specialty module
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.module import Module

app = create_app()

with app.app_context():
    modules = Module.query.all()
    
    print("\n" + "="*70)
    print("  EXAM MODE CONFIGURATION - ALL MODULES")
    print("="*70 + "\n")
    
    for module in modules:
        print(f"📚 {module.name}")
        print(f"   Slug: {module.slug}")
        print(f"   Exam Questions: {module.exam_question_count}")
        print(f"   Time Limit: {module.exam_time_limit_seconds} seconds ({module.exam_time_limit_seconds//60} minutes)")
        print(f"   Passing Score: {module.exam_passing_score}%")
        
        # Calculate time per question
        time_per_q = module.exam_time_limit_seconds / module.exam_question_count
        print(f"   Time per Question: {time_per_q:.1f} seconds ({time_per_q/60:.2f} minutes)")
        
        # Check against actual AWS exam
        if 'security' in module.slug.lower():
            print(f"\n   📋 AWS Actual Exam Parameters:")
            print(f"      Real Exam: 65 questions, 170 minutes (2h 50m)")
            print(f"      Real Time per Q: 2.62 minutes (157 seconds)")
            print(f"\n      Current Config: {module.exam_question_count} questions, {module.exam_time_limit_seconds//60} minutes")
            print(f"      Current Time per Q: {time_per_q/60:.2f} minutes ({time_per_q:.0f} seconds)")
            
            if module.exam_time_limit_seconds == 10200:  # 170 minutes
                print(f"      ✅ CORRECT - Matches real exam (170 minutes)")
            else:
                print(f"      ⚠️  INCORRECT - Should be 10200 seconds (170 minutes)")
        
        print("")
    
    print("="*70)
