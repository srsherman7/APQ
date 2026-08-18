# AWS Security Specialty Module

Complete question bank and study materials for the AWS Certified Security - Specialty (SCS-C02) exam.

## Files Created

1. **scs_module_ready.json** - Complete module with 52 questions ready for import
2. **scs_study_materials.json** - Comprehensive study guide covering all 5 exam domains
3. **scs_questions.py** - Initial question generator script
4. **add_more_scs.py** - Script that added additional questions

## Module Details

- **Exam**: AWS Certified Security - Specialty (SCS-C02)
- **Questions**: 52 professionally crafted scenario-based questions
- **Exam Format**: 65 questions, 180 minutes (3 hours), 75% passing score
- **Domains Covered**:
  - Incident Response (12%) - 6 questions
  - Logging and Monitoring (20%) - 11 questions  
  - Infrastructure Security (26%) - 11 questions
  - Identity and Access Management (20%) - 12 questions
  - Data Protection (22%) - 12 questions

## Question Distribution

### By Difficulty
- Level 1 (Foundational): 2 questions
- Level 2 (Associate): 22 questions
- Level 3 (Professional): 21 questions
- Level 4 (Expert): 7 questions

### Question Quality Features
- Scenario-based questions matching real AWS exam style
- Detailed explanations (150-300 words each)
- Memory techniques for retention
- IT context mapping to traditional security concepts
- All questions follow AWS security best practices

## Study Materials Coverage

Each domain includes:
- Overview and exam weight percentage
- 3-4 key AWS services with detailed information
- Service features, use cases, and exam tips
- 10+ best practices per domain
- Common security scenarios and patterns
- Real-world implementation guidance

## How to Import

### Option 1: Using API (Recommended)

```bash
# 1. Create the module
curl -X POST http://localhost:5000/api/modules/create \
  -H "Content-Type: application/json" \
  -d @scs_module_ready.json

# 2. The questions are already included, so you're done!
```

### Option 2: Manual Import Using Python

```python
import json
import requests

# Load the module data
with open('scs_module_ready.json', 'r') as f:
    data = json.load(f)

# Create module
module_response = requests.post(
    'http://localhost:5000/api/modules/create',
    json=data['module']
)

# Import questions
questions_response = requests.post(
    f'http://localhost:5000/api/modules/aws-security-specialty/import',
    json={'questions': data['questions']}
)

print(f"Module created: {module_response.status_code}")
print(f"Questions imported: {questions_response.status_code}")
```

### Option 3: Database Direct Import

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.module import Module
from models.question import Question
import json

app = create_app()

with app.app_context():
    # Load data
    with open('scs_module_ready.json', 'r') as f:
        data = json.load(f)
    
    # Create module
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
    db.session.flush()  # Get module_id
    
    # Create questions
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
    
    db.session.commit()
    print(f"Module created: {module.name}")
    print(f"Questions imported: {len(data['questions'])}")
```

## Verification

After importing, verify the module:

```bash
# Check module exists
curl http://localhost:5000/api/modules

# Get module details
curl http://localhost:5000/api/modules/aws-security-specialty

# Get questions
curl http://localhost:5000/api/modules/aws-security-specialty/questions
```

## Study Guide Integration

The study materials can be integrated into the module's `study_content` field:

```python
with app.app_context():
    module = Module.query.filter_by(slug='aws-security-specialty').first()
    
    with open('scs_study_materials.json', 'r') as f:
        study_data = json.load(f)
    
    module.study_content = study_data
    db.session.commit()
```

## Adding More Questions

To add more questions to the existing module:

```python
additional_questions = [
    {
        "question_text": "...",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "B",
        "explanation": "...",
        "memory_technique": "...",
        "topic_area": "Infrastructure Security",
        "difficulty_level": 3,
        "it_context_mapping": "..."
    }
]

requests.post(
    'http://localhost:5000/api/modules/aws-security-specialty/questions',
    json={'questions': additional_questions}
)
```

## Module Features

✅ 52 high-quality, scenario-based questions
✅ Comprehensive study guide for all 5 domains
✅ Memory techniques for better retention
✅ IT context mapping for traditional security professionals
✅ Detailed explanations with AWS best practices
✅ Balanced difficulty distribution
✅ Covers all exam objectives
✅ Real-world security scenarios

## Next Steps

1. Import the module using one of the methods above
2. Verify questions appear in the frontend
3. Test taking practice exams
4. Review study materials for each domain
5. Track progress and identify weak areas
6. Practice with timed exam mode

## Exam Resources

- **Official Exam Guide**: https://aws.amazon.com/certification/certified-security-specialty/
- **Exam Format**: 65 questions, 180 minutes, 75% passing
- **Prerequisites**: AWS Certified Cloud Practitioner OR Associate-level certification + 2 years hands-on experience
- **Cost**: $300 USD
- **Recertification**: Every 3 years

## Question Development Approach

All questions follow these principles:
1. **Scenario-based**: Real-world situations, not memorization
2. **Best practices**: Solutions follow AWS Well-Architected Framework
3. **Multiple services**: Questions often require combining multiple services
4. **Trade-offs**: Explain why other options are insufficient
5. **Practical**: Based on common security patterns and architectures

## Support

For issues or questions about this module:
1. Check that all questions imported correctly
2. Verify module appears in the frontend
3. Test with a few practice questions
4. Review study materials for comprehension

---

**Module Version**: 1.0
**Last Updated**: 2026-08-18
**Total Questions**: 52
**Study Materials**: 5 domains, 19 services, 50+ best practices
