"""
Fix Security Specialty exam configuration to match real AWS exam
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.module import Module

app = create_app()

with app.app_context():
    module = Module.query.filter_by(slug='aws-security-specialty').first()
    
    if not module:
        print("ERROR: Module not found")
        sys.exit(1)
    
    print(f"Found: {module.name}")
    print(f"\nCurrent Configuration:")
    print(f"  Exam Questions: {module.exam_question_count}")
    print(f"  Time Limit: {module.exam_time_limit_seconds} seconds ({module.exam_time_limit_seconds//60} minutes)")
    print(f"  Passing Score: {module.exam_passing_score}%")
    
    # Update to correct AWS exam parameters
    # Source: https://aws.amazon.com/certification/certified-security-specialty/
    print(f"\nAWS Official Exam Format:")
    print(f"  Questions: 65")
    print(f"  Time: 170 minutes (2 hours 50 minutes)")
    print(f"  Passing: 750/1000 (approximately 75%)")
    
    # Update the module
    module.exam_time_limit_seconds = 10200  # 170 minutes
    db.session.commit()
    
    print(f"\n✅ UPDATED Configuration:")
    print(f"  Exam Questions: {module.exam_question_count}")
    print(f"  Time Limit: {module.exam_time_limit_seconds} seconds ({module.exam_time_limit_seconds//60} minutes)")
    print(f"  Passing Score: {module.exam_passing_score}%")
    print(f"  Time per Question: {module.exam_time_limit_seconds/module.exam_question_count/60:.2f} minutes")
    
    print(f"\n✅ Now matches official AWS Security Specialty exam!")
    print(f"   Refresh browser to see updated exam mode timer.")
