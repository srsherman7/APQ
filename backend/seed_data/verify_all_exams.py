"""
Verify all module exam configurations match AWS official exams
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.module import Module

app = create_app()

# Official AWS exam parameters
official_exams = {
    'cloud-practitioner': {
        'questions': 65,
        'minutes': 90,
        'passing': 70.0,
        'source': 'CLF-C02'
    },
    'developer-associate': {
        'questions': 65,
        'minutes': 130,
        'passing': 72.0,
        'source': 'DVA-C02'
    },
    'ml-specialty': {
        'questions': 85,
        'minutes': 170,
        'passing': 75.0,
        'source': 'MLS-C01'
    },
    'aws-security-specialty': {
        'questions': 65,
        'minutes': 170,
        'passing': 75.0,
        'source': 'SCS-C02'
    }
}

with app.app_context():
    modules = Module.query.all()
    
    print("\n" + "="*80)
    print("  EXAM CONFIGURATION VERIFICATION - ALL MODULES")
    print("="*80 + "\n")
    
    all_correct = True
    
    for module in modules:
        official = official_exams.get(module.slug)
        
        if not official:
            print(f"⚠️  {module.name}")
            print(f"   No official exam parameters found for slug: {module.slug}\n")
            continue
        
        # Check configuration
        correct_time = module.exam_time_limit_seconds == (official['minutes'] * 60)
        correct_questions = module.exam_question_count == official['questions']
        correct_passing = module.exam_passing_score == official['passing']
        
        all_match = correct_time and correct_questions and correct_passing
        icon = "✅" if all_match else "❌"
        
        print(f"{icon} {module.name} ({official['source']})")
        print(f"   Questions: {module.exam_question_count} {'✅' if correct_questions else '❌ Should be ' + str(official['questions'])}")
        print(f"   Time: {module.exam_time_limit_seconds//60}m {'✅' if correct_time else '❌ Should be ' + str(official['minutes']) + 'm'}")
        print(f"   Passing: {module.exam_passing_score}% {'✅' if correct_passing else '❌ Should be ' + str(official['passing']) + '%'}")
        print(f"   Time/Question: {module.exam_time_limit_seconds/module.exam_question_count/60:.2f} minutes")
        print("")
        
        if not all_match:
            all_correct = False
    
    print("="*80)
    if all_correct:
        print("✅ ALL MODULES MATCH OFFICIAL AWS EXAM PARAMETERS")
    else:
        print("⚠️  SOME MODULES NEED CONFIGURATION UPDATES")
    print("="*80 + "\n")
