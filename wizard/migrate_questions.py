# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MigrateSurveyQuestions(models.TransientModel):
    """Wizard to migrate questions from survey.survey to test.survey"""
    _name = 'test.migrate_questions'
    _description = 'Migrate Survey Questions'

    source_survey_id = fields.Many2one(
        'survey.survey',
        string='Source Survey',
        required=True,
        help='Select the survey to copy questions from'
    )
    target_survey_id = fields.Many2one(
        'test.survey',
        string='Target Test Survey',
        required=True,
        help='Select the test survey to copy questions to'
    )
    copy_answers = fields.Boolean(
        string='Copy Answers',
        default=True,
        help='Copy question answers'
    )
    copy_images = fields.Boolean(
        string='Copy Images',
        default=True,
        help='Copy question images'
    )

    def action_migrate(self):
        """Migrate questions from survey to test"""
        self.ensure_one()
        
        source_questions = self.source_survey_id.question_ids
        target_survey = self.target_survey_id
        migrated_count = 0
        
        for source_q in source_questions:
            if source_q.is_page:
                test_question = self._create_test_section(source_q, target_survey)
            else:
                test_question = self._create_test_question(source_q, target_survey)
                
                if self.copy_answers and source_q.suggested_answer_ids:
                    self._create_answers(source_q, test_question)
            
            migrated_count += 1
        
        return {'type': 'ir.actions.act_window_close'}

    def _create_test_question(self, source_question, target_survey):
        TestQuestion = self.env['test.question']
        q_type = self._convert_question_type(source_question.question_type)
        
        # In survey.question, the field is is_scored_question (computed)
        # For questions with suggested answers, check if any are marked as correct
        is_scored = source_question.is_scored_question
        if not is_scored and source_question.suggested_answer_ids:
            is_scored = any(source_question.suggested_answer_ids.mapped('is_correct'))
        
        answer_score = 0
        if is_scored:
            # Get answer_score from the correct answer(s)
            if source_question.suggested_answer_ids:
                correct_answers = source_question.suggested_answer_ids.filtered('is_correct')
                if correct_answers:
                    answer_score = correct_answers[0].answer_score
            elif source_question.answer_score:
                answer_score = source_question.answer_score
        
        vals = {
            'survey_id': target_survey.id,
            'question': source_question.title,
            'question_type': q_type,
            'sequence': source_question.sequence,
            'is_scored': is_scored,
            'answer_score': answer_score,
            'constr_mandatory': source_question.constr_mandatory,
            'description': source_question.description,
        }
        
        return TestQuestion.create(vals)

    def _create_test_section(self, source_question, target_survey):
        TestQuestion = self.env['test.question']
        
        vals = {
            'survey_id': target_survey.id,
            'question': '',
            'question_type': False,
            'sequence': source_question.sequence,
            'is_page': True,
            'page_title': source_question.title,
            'description': source_question.description,
        }
        
        return TestQuestion.create(vals)

    def _create_answers(self, source_question, test_question):
        TestAnswer = self.env['test.question.answer']
        
        for source_answer in source_question.suggested_answer_ids:
            answer_vals = {
                'question_id': test_question.id,
                'value': source_answer.value,
                'sequence': source_answer.sequence,
                'answer_score': source_answer.answer_score,
            }
            TestAnswer.create(answer_vals)

    def _convert_question_type(self, survey_type):
        if not survey_type:
            return 'text_box'
        
        mapping = {
            'char_box': 'text_box',
            'text_box': 'text_box',
            'numerical_box': 'numerical_box',
            'date': 'date',
            'datetime': 'datetime',
            'simple_choice': 'simple_choice',
            'multiple_choice': 'multiple_choice',
            'matrix': 'multiple_choice',
        }
        result = mapping.get(survey_type, 'text_box')
        return result
