"""
Question Parser service for importing and validating questions from JSON files.
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from extensions import db
from models.question import Question


class ValidationError(Exception):
    """Exception raised when question validation fails."""
    def __init__(self, message: str, question_index: Optional[int] = None):
        self.message = message
        self.question_index = question_index
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        if self.question_index is not None:
            return f"Question at index {self.question_index}: {self.message}"
        return self.message


class JSONParseError(Exception):
    """Exception raised when JSON parsing fails."""
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        if self.line is not None and self.column is not None:
            return f"JSON parsing failed at line {self.line}, column {self.column}: {self.message}"
        return f"JSON parsing failed: {self.message}"


class QuestionParser:
    """
    Service for parsing, validating, and importing questions from JSON files.
    
    Validates questions according to requirements 13.8-13.14:
    - question_text: non-empty string, max 1000 characters
    - options: array of 2-6 strings, each max 500 characters
    - correct_answer: non-empty string matching one option
    - explanation: non-empty string, max 2000 characters
    - memory_technique: non-empty string, max 500 characters
    - difficulty_level: integer 1-5 inclusive
    - topic_area: required field
    """
    
    REQUIRED_FIELDS = [
        'question_text',
        'options',
        'correct_answer',
        'explanation',
        'topic_area',
        'difficulty_level',
        'memory_technique'
    ]
    
    VALID_TOPIC_AREAS = [
        'Cloud Concepts',
        'Security and Compliance',
        'Technology',
        'Billing and Pricing'
    ]
    
    def parse_json_file(self, file_path: str) -> List[Question]:
        """
        Parse JSON file containing questions.
        
        Args:
            file_path: Path to JSON file
        
        Returns:
            List of validated Question objects
        
        Raises:
            JSONParseError: If JSON is malformed or file cannot be read
            ValidationError: If question data is invalid
        """
        # Check file accessibility
        path = Path(file_path)
        if not path.exists():
            raise JSONParseError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise JSONParseError(f"Path is not a file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            raise JSONParseError(f"File access failed: {str(e)}")
        
        # Parse JSON with error reporting
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise JSONParseError(e.msg, e.lineno, e.colno)
        
        # Validate that data is an array
        if not isinstance(data, list):
            raise ValidationError("JSON root must be an array of question objects")
        
        # Parse and validate each question
        questions = []
        for index, question_data in enumerate(data):
            try:
                question = self._parse_question(question_data, index)
                questions.append(question)
            except ValidationError as e:
                # Re-raise with index if not already set
                if e.question_index is None:
                    raise ValidationError(e.message, index)
                raise
        
        return questions
    
    def _parse_question(self, question_data: Dict[str, Any], index: int) -> Question:
        """
        Parse and validate a single question.
        
        Args:
            question_data: Dictionary containing question fields
            index: Index of question in array (for error reporting)
        
        Returns:
            Validated Question object (not yet persisted to database)
        
        Raises:
            ValidationError: If validation fails
        """
        # Validate it's a dictionary
        if not isinstance(question_data, dict):
            raise ValidationError("Question must be an object", index)
        
        # Validate required fields are present
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in question_data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}", index)
        
        # Validate each field
        self._validate_question_text(question_data['question_text'], index)
        self._validate_options(question_data['options'], index)
        self._validate_correct_answer(question_data['correct_answer'], question_data['options'], index)
        self._validate_explanation(question_data['explanation'], index)
        self._validate_memory_technique(question_data['memory_technique'], index)
        self._validate_difficulty_level(question_data['difficulty_level'], index)
        self._validate_topic_area(question_data['topic_area'], index)
        
        # Create Question object (not yet persisted)
        question = Question(
            question_text=question_data['question_text'],
            options=question_data['options'],
            correct_answer=question_data['correct_answer'],
            explanation=question_data['explanation'],
            memory_technique=question_data['memory_technique'],
            topic_area=question_data['topic_area'],
            difficulty_level=question_data['difficulty_level'],
            incorrect_explanation=question_data.get('incorrect_explanation'),
            it_context_mapping=question_data.get('it_context_mapping'),
            is_active=question_data.get('is_active', True)
        )
        
        return question
    
    def _validate_question_text(self, question_text: Any, index: int) -> None:
        """Validate question_text field."""
        if not isinstance(question_text, str):
            raise ValidationError("question_text must be a string", index)
        
        if len(question_text.strip()) == 0:
            raise ValidationError("question_text cannot be empty", index)
        
        if len(question_text) > 1000:
            raise ValidationError("question_text exceeds maximum length of 1000 characters", index)
    
    def _validate_options(self, options: Any, index: int) -> None:
        """Validate options field."""
        if not isinstance(options, list):
            raise ValidationError("options must be an array", index)
        
        if len(options) < 2 or len(options) > 6:
            raise ValidationError("options must contain between 2 and 6 elements", index)
        
        for i, option in enumerate(options):
            if not isinstance(option, str):
                raise ValidationError(f"options[{i}] must be a string", index)
            
            if len(option.strip()) == 0:
                raise ValidationError(f"options[{i}] cannot be empty", index)
            
            if len(option) > 500:
                raise ValidationError(f"options[{i}] exceeds maximum length of 500 characters", index)
    
    def _validate_correct_answer(self, correct_answer: Any, options: List[str], index: int) -> None:
        """Validate correct_answer field."""
        if not isinstance(correct_answer, str):
            raise ValidationError("correct_answer must be a string", index)
        
        if len(correct_answer.strip()) == 0:
            raise ValidationError("correct_answer cannot be empty", index)
        
        if correct_answer not in options:
            raise ValidationError("correct_answer must match exactly one element in options array", index)
    
    def _validate_explanation(self, explanation: Any, index: int) -> None:
        """Validate explanation field."""
        if not isinstance(explanation, str):
            raise ValidationError("explanation must be a string", index)
        
        if len(explanation.strip()) == 0:
            raise ValidationError("explanation cannot be empty", index)
        
        if len(explanation) > 2000:
            raise ValidationError("explanation exceeds maximum length of 2000 characters", index)
    
    def _validate_memory_technique(self, memory_technique: Any, index: int) -> None:
        """Validate memory_technique field."""
        if not isinstance(memory_technique, str):
            raise ValidationError("memory_technique must be a string", index)
        
        if len(memory_technique.strip()) == 0:
            raise ValidationError("memory_technique cannot be empty", index)
        
        if len(memory_technique) > 500:
            raise ValidationError("memory_technique exceeds maximum length of 500 characters", index)
    
    def _validate_difficulty_level(self, difficulty_level: Any, index: int) -> None:
        """Validate difficulty_level field."""
        if not isinstance(difficulty_level, int):
            raise ValidationError("difficulty_level must be an integer", index)
        
        if difficulty_level < 1 or difficulty_level > 5:
            raise ValidationError("difficulty_level must be between 1 and 5 inclusive", index)
    
    def _validate_topic_area(self, topic_area: Any, index: int) -> None:
        """Validate topic_area field."""
        if not isinstance(topic_area, str):
            raise ValidationError("topic_area must be a string", index)
        
        if len(topic_area.strip()) == 0:
            raise ValidationError("topic_area cannot be empty", index)
    
    def validate_question(self, question_data: Dict[str, Any]) -> bool:
        """
        Validate a single question without creating a Question object.
        
        Args:
            question_data: Dictionary containing question fields
        
        Returns:
            True if valid
        
        Raises:
            ValidationError: If validation fails
        """
        self._parse_question(question_data, 0)
        return True
    
    def format_to_json(self, questions: List[Question]) -> str:
        """
        Format Question objects to JSON string.
        
        Args:
            questions: List of Question objects
        
        Returns:
            JSON string representation
        """
        questions_data = []
        for question in questions:
            question_dict = {
                'question_text': question.question_text,
                'options': question.options,
                'correct_answer': question.correct_answer,
                'explanation': question.explanation,
                'memory_technique': question.memory_technique,
                'topic_area': question.topic_area,
                'difficulty_level': question.difficulty_level,
            }
            
            # Add optional fields if present
            if question.incorrect_explanation:
                question_dict['incorrect_explanation'] = question.incorrect_explanation
            
            if question.it_context_mapping:
                question_dict['it_context_mapping'] = question.it_context_mapping
            
            questions_data.append(question_dict)
        
        return json.dumps(questions_data, indent=2, ensure_ascii=False)
    
    def batch_import(self, questions: List[Question]) -> int:
        """
        Import multiple questions in a single transaction.
        
        Args:
            questions: List of validated Question objects
        
        Returns:
            Number of questions imported
        
        Raises:
            Exception: If database transaction fails
        """
        try:
            # Add all questions to session
            for question in questions:
                db.session.add(question)
            
            # Commit transaction
            db.session.commit()
            
            return len(questions)
        
        except Exception as e:
            # Rollback on error
            db.session.rollback()
            raise Exception(f"Batch import failed: {str(e)}")
