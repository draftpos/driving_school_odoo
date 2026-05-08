# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TestSurvey(models.Model):
    """Test Survey - Similar to Survey Module"""
    _name = 'test.survey'
    _description = 'Test Survey'
    _order = 'create_date DESC'
    _rec_name = 'title'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_access_token(self):
        return str(uuid.uuid4())

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        if 'title' in fields_list and not result.get('title') and self.env.context.get('default_name'):
            result['title'] = self.env.context.get('default_name')
        return result

    # Basic fields
    title = fields.Char('Test Title', required=True, translate=True)
    description = fields.Html("Description", translate=True, sanitize=True, sanitize_overridable=True)
    description_done = fields.Html("End Message", translate=True)
    active = fields.Boolean("Active", default=True)
    color = fields.Integer('Color Index', default=0)

    # Access control
    access_mode = fields.Selection([
        ('public', 'Anyone with the link'),
        ('token', 'Invited people only')],
        string='Access Mode',
        default='public', required=True)
    access_token = fields.Char('Access Token', default=lambda self: self._get_default_access_token(), copy=False)
    users_login_required = fields.Boolean('Require Login')
    users_can_go_back = fields.Boolean('Users can go back', help="If checked, users can go back to previous pages.")
    restrict_user_ids = fields.Many2many('res.users', string='Restricted to', domain=[('share', '=', False)], tracking=True)

    # Questions
    question_ids = fields.One2many('test.question', 'survey_id', string='Questions', copy=True)
    question_count = fields.Integer('# Questions', compute='_compute_question_count')

    # Questions layout
    questions_layout = fields.Selection([
        ('page_per_question', 'One page per question'),
        ('page_per_section', 'One page per section'),
        ('one_page', 'One page with all the questions')],
        string="Pagination", required=True, default='page_per_question')
    questions_selection = fields.Selection([
        ('all', 'All questions'),
        ('random', 'Randomized per Section')],
        string="Question Selection", required=True, default='all',
        help="If randomized is selected, you can configure the number of random questions by section.")
    user_select_random_count = fields.Boolean(
        'User can set number of questions',
        help="If checked, test takers can choose the number of questions when they start the test")
    default_random_questions_count = fields.Integer(
        'Default number of questions',
        default=1,
        help="Default number of random questions when user selects their own count")
    progression_mode = fields.Selection([
        ('percent', 'Percentage left'),
        ('number', 'Number')],
        string='Display Progress as', default='percent',
        help="If Number is selected, it will display the number of questions answered on the total number of question to answer.")

    # Scoring
    scoring_type = fields.Selection([
        ('no_scoring', 'No scoring'),
        ('scoring_with_answers', 'Scoring with answers at the end'),
        ('scoring_without_answers', 'Scoring without answers')],
        string='Scoring', required=True, default='no_scoring')
    scoring_success_min = fields.Float('Required Score (%)', default=80.0)
    scoring_max_obtainable = fields.Float('Maximum obtainable score', compute='_compute_scoring_max_obtainable')

    # Time limit
    is_time_limited = fields.Boolean('The survey is limited in time')
    time_limit = fields.Float("Time limit (minutes)", default=10)

    # Attempts
    is_attempts_limited = fields.Boolean('Limited number of attempts', help="Check this option if you want to limit the number of attempts per user")
    attempts_limit = fields.Integer('Number of attempts', default=1)

    # Statistics
    answer_count = fields.Integer("Total Responses", compute='_compute_statistics')
    answer_done_count = fields.Integer("Completed", compute='_compute_statistics')
    success_count = fields.Integer("Success", compute='_compute_statistics')
    success_ratio = fields.Integer("Success Ratio (%)", compute='_compute_statistics')
    answer_score_avg = fields.Float("Avg Score (%)", compute='_compute_statistics')

    # Responsible
    user_id = fields.Many2one('res.users', string='Responsible',
        domain=[('share', '=', False)], tracking=True)

    # User inputs
    user_input_ids = fields.One2many('test.user_input', 'survey_id', string='Responses', readonly=True)

    _access_token_unique = models.Constraint(
        'unique(access_token)',
        'Access token should be unique',
    )

    @api.depends('question_ids')
    def _compute_question_count(self):
        for survey in self:
            survey.question_count = len(survey.question_ids)

    @api.depends('question_ids', 'question_ids.passing_score', 'question_ids.suggested_answer_ids', 'question_ids.suggested_answer_ids.answer_score')
    def _compute_scoring_max_obtainable(self):
        for survey in self:
            total_score = 0.0
            for question in survey.question_ids:
                if question.passing_score:
                    total_score += question.passing_score
                elif question.suggested_answer_ids:
                    total_score += sum(answer.answer_score for answer in question.suggested_answer_ids if answer.answer_score > 0)
            survey.scoring_max_obtainable = total_score

    @api.depends('user_input_ids.state', 'user_input_ids.scoring_success', 'user_input_ids.scoring_percentage')
    def _compute_statistics(self):
        for survey in self:
            user_inputs = survey.user_input_ids
            answer_count = len(user_inputs)
            answer_done_count = len(user_inputs.filtered(lambda u: u.state == 'done'))
            success_count = len(user_inputs.filtered(lambda u: u.scoring_success))

            score_total = sum(u.scoring_percentage for u in user_inputs.filtered(lambda u: u.scoring_percentage is not None))
            answer_score_avg = score_total / answer_count if answer_count > 0 else 0.0

            success_ratio = (success_count / answer_count * 100) if answer_count > 0 else 0.0

            survey.answer_count = answer_count
            survey.answer_done_count = answer_done_count
            survey.success_count = success_count
            survey.answer_score_avg = answer_score_avg
            survey.success_ratio = success_ratio

    @api.constrains('scoring_success_min')
    def _check_scoring_success_min(self):
        for survey in self:
            if survey.scoring_success_min and (survey.scoring_success_min < 0 or survey.scoring_success_min > 100):
                raise ValidationError(_("Success percentage must be between 0 and 100"))

    def action_start_test(self):
        """Start the test"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': 'Start Test',
            'target': 'new',
            'url': '/test/start/token/%s' % self.access_token,
        }

    def action_result_test(self):
        """View test results"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': 'Results',
            'target': 'new',
            'url': '/test/results/%s' % self.id,
        }

    def action_send_test(self):
        """Send test invitation"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send Test'),
            'view_mode': 'form',
            'res_model': 'test.invite',
            'target': 'new',
            'context': {'default_test_id': self.id},
        }

    def action_test_user_input(self):
        """Show all test responses/registrations"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Participants'),
            'res_model': 'test.user_input',
            'view_mode': 'list,form',
            'domain': [('survey_id', '=', self.id)],
            'context': {'default_survey_id': self.id},
        }

    def action_test_user_input_completed(self):
        """Show completed test responses/participants"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Participants'),
            'res_model': 'test.user_input',
            'view_mode': 'list,form',
            'domain': [('survey_id', '=', self.id), ('state', '=', 'done')],
            'context': {'default_survey_id': self.id},
        }

    def action_archive(self):
        """Archive the test"""
        self.ensure_one()
        self.write({'active': False})

    def action_unarchive(self):
        """Unarchive the test"""
        self.ensure_one()
        self.write({'active': True})

    def get_start_url(self):
        return '/test/start/%s' % self.access_token

    def get_start_short_url(self):
        """Get short URL for test access"""
        return '/t/%s' % self.access_token[:6]

    def get_print_url(self):
        return '/test/print/%s' % self.access_token

    def _create_answer(self, user=False, partner=False, email=False, **additional_vals):
        """Create a new user input/answer for this test"""
        self.check_access('read')

        user_inputs = self.env['test.user_input']
        for test in self:
            answer_vals = {
                'survey_id': test.id,
            }
            if user and not user._is_public():
                answer_vals['partner_id'] = user.partner_id.id
                answer_vals['email'] = user.email
            elif partner:
                answer_vals['partner_id'] = partner.id
                answer_vals['email'] = partner.email
            else:
                answer_vals['email'] = email

            answer_vals.update(additional_vals)
            user_inputs += user_inputs.create(answer_vals)

        return user_inputs
