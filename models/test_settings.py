from odoo import models, fields, api

class TestSettings(models.Model):
    _name = 'test.settings'
    _description = 'Test Settings'
    _rec_name = 'id'

    # General Settings
    default_time_limit = fields.Integer(
        string='Default Time Limit (minutes)',
        default=15,
        help='Default time limit for tests in minutes'
    )
    

    allow_multiple_attempts = fields.Boolean(
        string='Allow Multiple Attempts',
        default=True,
        help='Allow students to attempt tests multiple times'
    )
    
    show_correct_answers = fields.Boolean(
        string='Show Correct Answers After Submission',
        default=False,
        help='Show correct answers after test is submitted'
    )
    
    shuffle_questions = fields.Boolean(
        string='Shuffle Questions',
        default=False,
        help='Randomize the order of questions'
    )
    
    show_progress_bar = fields.Boolean(
        string='Show Progress Bar',
        default=True,
        help='Show progress bar during test'
    )
    
    # Notification Settings
    send_email_notifications = fields.Boolean(
        string='Send Email Notifications',
        default=True,
        help='Send email notifications to students'
    )
    
    # Question Selection Settings
    
    class1_passing_score = fields.Integer(string='Class 1 Passing Score', default=100, help='Minimum percentage to pass for Class 1 students')
    class2_passing_score = fields.Integer(string='Class 2 Passing Score', default=88, help='Minimum percentage to pass for Class 2 students')
    class4_passing_score = fields.Integer(string='Class 4 Passing Score', default=88, help='Minimum percentage to pass for Class 4 students')
    class2and4_passing_score = fields.Integer(string='Class 2 & 4 Passing Score', default=88, help='Minimum percentage to pass for Class 2 & 4 students')

    questions_limit = fields.Integer(
        string='Questions Limit',
        default=25,
        help='Maximum number of questions to randomly select from a test (if test has more questions than this limit)'
    )
    
    questions_per_page = fields.Integer(
        string='Questions Per Page',
        default=1,
        help='Number of questions to display per page'
    )
    
    show_question_navigator = fields.Boolean(
        string='Show Question Navigator',
        default=True,
        help='Show question navigation buttons'
    )
    
    @api.model
    def get_default_settings(self):
        """Get the default test settings — always return the single settings record."""
        settings = self.search([], order='id ASC', limit=1)
        if not settings:
            settings = self.create({})
        else:
            # Delete any duplicate records, keeping only the first
            duplicates = self.search([('id', '!=', settings.id)])
            if duplicates:
                duplicates.unlink()
        return settings
    
    @api.model
    def get_default_time_limit(self):
        """Get default time limit"""
        return self.get_default_settings().default_time_limit
    

    @api.model
    def get_questions_limit(self):
        """Get questions limit"""
        return self.get_default_settings().questions_limit
