# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import api, fields, models


class TestUserInput(models.Model):
    """Test User Input - Similar to Survey User Input"""
    _name = 'test.user_input'
    _description = 'Test User Input'
    _order = 'create_date DESC'
    _rec_name = 'survey_id'
    _check_company_auto = False  # Disable company check for portal users

    survey_id = fields.Many2one('test.survey', string='Test Survey', required=False, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company',
        related='survey_id.company_id', store=True)

    # User info
    partner_id = fields.Many2one('res.partner', string='Partner')
    email = fields.Char('Email')
    nickname = fields.Char('Nickname')

    # Student details
    student_id = fields.Many2one('test.student', string='Student Participant', ondelete='cascade')
    student_fullname = fields.Char('Student Full Name')
    student_username = fields.Char('Student Username')
    student_id_number = fields.Char('Student ID Number')
    student_class = fields.Selection([
        ('class1', 'Class 1 (Buses)'),
        ('class2', 'Class 2 (Heavy Vehicles)'),
        ('class4', 'Class 4 (Light Vehicles)'),
        ('class2and4', 'Class 2 & 4 (Heavy & Light)'),
    ], string='Student Class')

    # State
    state = fields.Selection([
        ('new', 'New'),
        ('skip', 'Skipped'),
        ('done', 'Completed'),
    ], string='Status', default='new', required=True)

    # Scores
    scoring_total = fields.Float('Total Score', compute='_compute_scores', readonly=True, store=True)
    scoring_success = fields.Boolean('Success', compute='_compute_scores', readonly=True, store=True)
    scoring_percentage = fields.Float('Score (%)', compute='_compute_scores', readonly=True, store=True)
    scoring_answers = fields.Integer('# Correct Answers', compute='_compute_scores', readonly=True, store=True)
    max_scoring_possible = fields.Float('Max Possible Score', help="Maximum score obtainable for the specific questions assigned to this attempt.")

    # Predefined answers
    user_input_line_ids = fields.One2many('test.user.input.line', 'user_input_id', string='Answers')

    # Timestamps
    start_datetime = fields.Datetime('Start Datetime')
    end_datetime = fields.Datetime('End Datetime')
    deadline = fields.Datetime('Deadline')

    # Device info
    device = fields.Char('Device')

    # Access token
    access_token = fields.Char('Access Token', index=True)

    # IP address
    ip = fields.Char('IP Address')
    user_agent = fields.Char('User Agent')

    @api.depends(
        'user_input_line_ids.answer_score',
        'user_input_line_ids.answer_is_correct',
        'survey_id.scoring_type',
        'survey_id.scoring_max_obtainable',
    )
    def _compute_scores(self):
        for user_input in self:
            total_score = sum(line.answer_score for line in user_input.user_input_line_ids)
            answers_count = len(user_input.user_input_line_ids.filtered(lambda l: l.answer_is_correct))

            user_input.scoring_total = total_score

            if user_input.survey_id.scoring_type != 'no_scoring':
                settings = self.env['test.settings'].sudo().get_default_settings()
                limit = settings.get_questions_limit() or 25
                
                # The user wants all results to be "out of 25" (the limit)
                # regardless of how many questions are actually in the survey.
                max_score = float(limit)
                
                user_input.scoring_percentage = (total_score / max_score * 100) if max_score > 0 else 0
                # Use class-specific passing score if available
                passing_score = settings.class4_passing_score or 88
                
                if user_input.student_class == 'class1':
                    passing_score = settings.class1_passing_score
                elif user_input.student_class == 'class2':
                    passing_score = settings.class2_passing_score
                elif user_input.student_class == 'class4':
                    passing_score = settings.class4_passing_score
                elif user_input.student_class == 'class2and4':
                    passing_score = settings.class2and4_passing_score
                
                user_input.scoring_success = user_input.scoring_percentage >= passing_score
            else:
                user_input.scoring_percentage = 0
                user_input.scoring_success = False

            user_input.scoring_answers = answers_count

    def action_start_test(self):
        """Start the test"""
        self.ensure_one()
        self.write({
            'start_datetime': datetime.now(),
            'state': 'new',
        })
        return self.survey_id.get_start_url()

    def action_finish_test(self):
        """Finish the test"""
        self.ensure_one()
        self.write({
            'end_datetime': datetime.now(),
            'state': 'done',
        })

        if self.survey_id.scoring_type != 'no_scoring':
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': '/test/results/%s' % self.id,
            }

        return True

    def action_skip_test(self):
        """Skip the test"""
        self.ensure_one()
        self.write({
            'end_datetime': datetime.now(),
            'state': 'skip',
        })

    def action_results_redirect(self):
        """Redirect to the test results page"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/test/results/%s' % self.id,
            'target': 'new',
        }


class TestUserInputLine(models.Model):
    """Test User Input Line - Similar to Survey User Input Line"""
    _name = 'test.user.input.line'
    _description = 'Test User Input Line'
    _order = 'sequence, id'

    user_input_id = fields.Many2one('test.user_input', string='Test Response', required=True, ondelete='cascade')
    question_id = fields.Many2one('test.question', string='Question', required=True, ondelete='cascade')

    # Answer type
    answer_type = fields.Selection([
        ('text_box', 'Text Box'),
        ('simple_choice', 'One choice'),
        ('multiple_choice', 'Multiple choices'),
        ('numerical_box', 'Numerical'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
    ], string='Answer Type')

    # Value stores
    value_text_box = fields.Text('Text Box')
    value_suggested = fields.Many2one('test.question.answer', string='Suggested Answer')
    value_suggested_ids = fields.Many2many('test.question.answer', string='Multiple Suggested Answers')
    value_numerical = fields.Float('Numerical')
    value_date = fields.Date('Date')
    value_datetime = fields.Datetime('Datetime')

    # Score
    answer_score = fields.Float('Score')
    answer_is_correct = fields.Boolean('Correct')

    # Sequence
    sequence = fields.Integer('Sequence', related='question_id.sequence', store=True)

    # Skipped
    skipped = fields.Boolean('Skipped')

    @api.onchange('question_id')
    def _onchange_question(self):
        self.answer_type = self.question_id.question_type
