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

    @api.model
    def _setup_default_student(self):
        """
        Ensure the demo 'student' user exists as a plain internal user
        (base.group_user), NOT a portal user. This guarantees Odoo redirects
        them to /web after login, which our portal.py controller then
        intercepts to send them to /test/register.
        """
        student_user = self.env['res.users'].sudo().search(
            [('login', '=', 'student')], limit=1
        )
        if not student_user:
            # Create the demo student as an internal user
            partner = self.env['res.partner'].sudo().create({
                'name': 'Demo Student',
                'email': 'student@example.com',
            })
            student_user = self.env['res.users'].sudo().create({
                'name': 'Demo Student',
                'login': 'student',
                'password': 'student',
                'partner_id': partner.id,
                'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
            })
        else:
            # Remove portal group, ensure internal user group only
            portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
            internal_group = self.env.ref('base.group_user')
            if portal_group and portal_group in student_user.group_ids:
                student_user.sudo().write({
                    'group_ids': [
                        (3, portal_group.id),   # unlink portal group
                        (4, internal_group.id),  # add internal group
                    ]
                })
