# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TestQuestion(models.Model):
    _name = 'test.question'
    _description = 'Test Question'
    _rec_name = 'question'
    _order = 'sequence, id'
    _check_company_auto = True

    survey_id = fields.Many2one('test.survey', string='Survey', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company',
        related='survey_id.company_id', store=True)
    question = fields.Text(string='Question', required=True, translate=True)
    question_type = fields.Selection([
        ('simple_choice', 'Simple Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('text_box', 'Text Box'),
    ], string='Question Type', required=True, default='simple_choice')
    
    question_image = fields.Binary(string='Question Image', attachment=True)
    question_image_filename = fields.Char(string='Question Image Filename')
    
    sequence = fields.Integer(string='Sequence', default=10)
    is_scored = fields.Boolean(string='Is Scored', default=True)
    constr_mandatory = fields.Boolean(string='Mandatory Answer', default=True)
    
    passing_score = fields.Integer(string='Passing Score (%)', default=70)
    
    is_random = fields.Boolean(string='Random Selection')
    
    suggested_answer_ids = fields.One2many('test.question.answer', 'question_id', 
                                           string='Suggested Answers', required=True)
    correct_answer_id = fields.Many2one('test.question.answer', string='Correct Answer',
                                         compute='_compute_correct_answer', store=True)
    
    @api.depends('suggested_answer_ids', 'suggested_answer_ids.is_correct')
    def _compute_correct_answer(self):
        for question in self:
            correct = question.suggested_answer_ids.filtered(lambda a: a.is_correct)
            question.correct_answer_id = correct[:1].id if correct else False
    
    @api.constrains('suggested_answer_ids')
    def _check_correct_answers(self):
        for question in self:
            correct_answers = question.suggested_answer_ids.filtered(lambda a: a.is_correct)
            if question.question_type == 'simple_choice' and len(correct_answers) != 1:
                raise ValidationError(_("Simple choice questions must have exactly one correct answer."))
            if question.question_type == 'multiple_choice' and len(correct_answers) < 1:
                raise ValidationError(_("Multiple choice questions must have at least one correct answer."))


class TestQuestionAnswer(models.Model):
    _name = 'test.question.answer'
    _description = 'Test Question Answer'
    _order = 'question_id, sequence, id'

    question_id = fields.Many2one('test.question', string='Question', required=True, ondelete='cascade')
    survey_id = fields.Many2one('test.survey', related='question_id.survey_id', store=True, readonly=True)
    value = fields.Text(string='Answer Value', required=True, translate=True)
    value_eng = fields.Text(string='English Version', translate=True)
    
    answer_image = fields.Binary(string='Answer Image', attachment=True)
    answer_image_filename = fields.Char(string='Answer Image Filename')
    
    is_correct = fields.Boolean(string='Is Correct Answer', default=False)
    answer_score = fields.Float(string='Answer Score', default=1.0)
    sequence = fields.Integer(string='Sequence', default=10)
    
    comment = fields.Text(string='Answer Comment', translate=True)
    comment_eng = fields.Text(string='English Comment', translate=True)

    _positive_score = models.Constraint(
        'CHECK(answer_score >= 0)',
        'Answer score must be positive!',
    )
