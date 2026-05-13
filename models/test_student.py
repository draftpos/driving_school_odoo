from odoo import models, fields, api

class TestStudent(models.Model):
    _name = 'test.student'
    _description = 'Test Student'
    _order = 'username ASC'
    _rec_name = 'username'

    name = fields.Char('Full Name', required=True)
    username = fields.Char('Username', required=True, index=True)
    student_class = fields.Selection([
        ('class1', 'Class 1 (Buses)'),
        ('class2', 'Class 2 (Heavy Vehicles)'),
        ('class4', 'Class 4 (Light Vehicles)'),
        ('class2and4', 'Class 2 & 4 (Heavy & Light)'),
    ], string='Student Class')
    partner_id = fields.Many2one('res.partner', string='Partner Account')
    user_input_ids = fields.One2many('test.user_input', 'student_id', string='Test Attempts', domain=[('survey_id', '!=', False)])
    
    attempt_count = fields.Integer('Attempt Count', compute='_compute_attempt_count')
    
    @api.depends('user_input_ids')
    def _compute_attempt_count(self):
        for student in self:
            student.attempt_count = len(student.user_input_ids)

    _sql_constraints = [
        ('username_uniq', 'unique(username)', 'Username must be unique!'),
    ]
