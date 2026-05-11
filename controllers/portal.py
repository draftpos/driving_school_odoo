# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


class TestStudentPortal(http.Controller):
    """Student Portal Controller for Test Module"""

    @http.route(['/web'], type='http', auth='user', website=True)
    def web_redirect(self, **kw):
        try:
            if request.env.user.has_group('base.group_system'):
                return request.redirect('/odoo')
        except Exception:
            pass
        return request.redirect('/test')

    @http.route(['/test'], type='http', auth='user', website=True)
    def test_index(self, **kw):
        """Entry point - redirect to dashboard"""
        user = request.env.user
        sudo_user = user.sudo()
        try:
            if user.has_group('base.group_system'):
                return request.redirect('/test/my')
        except Exception:
            pass

        # Check if student is already registered
        partner_id = sudo_user.partner_id.id if sudo_user.partner_id else False
        if partner_id:
            registration = request.env['test.user_input'].sudo().search([
                ('partner_id', '=', partner_id),
                ('student_fullname', '!=', False),
                ('student_username', '!=', False),
            ], limit=1)
            if not registration:
                return request.redirect('/test/register')

        return request.redirect('/test/my')

    @http.route(['/test/my'], type='http', auth='user', website=True)
    def test_my(self, **kw):
        """Student dashboard - shows list of available tests with custom design"""
        user = request.env.user
        sudo_user = user.sudo()
        partner_id = sudo_user.partner_id.id if sudo_user.partner_id else False

        surveys = request.env['test.survey'].sudo().search([('active', '=', True)])

        user_inputs = request.env['test.user_input'].sudo().search([
            ('partner_id', '=', partner_id)
        ]) if partner_id else request.env['test.user_input'].sudo().browse([])

        is_admin = False
        try:
            is_admin = user.has_group('base.group_system')
        except Exception:
            pass

        # Build custom HTML response without Odoo layout (same design as register page)
        company_logo = '/web/binary/company_logo'

        # Build surveys list HTML
        surveys_html = ''
        if surveys:
            for survey in surveys:
                surveys_html += f'''
                <div class="test-card">
                    <div class="test-card-header">
                        <h3>{survey.title}</h3>
                    </div>
                    <div class="test-card-body">
                        <p>{"No description available." if not survey.description else survey.description}</p>
                        <p><strong>Questions:</strong> {survey.question_count or 0}</p>
                        <a href="/test/start/{survey.id}" class="btn btn-start">Start Test</a>
                    </div>
                </div>'''
        else:
            surveys_html = '<p class="text-muted">No tests available at the moment.</p>'

        # Build completed tests list HTML
        completed_html = ''
        if user_inputs:
            for inp in user_inputs:
                status = 'Completed' if inp.state == 'done' else 'In Progress'
                score = f'{inp.scoring_percentage:.1f}%' if inp.scoring_percentage else '-'
                date_str = ''
                if inp.end_datetime:
                    date_str = inp.end_datetime.strftime('%Y-%m-%d %H:%M')
                elif inp.start_datetime:
                    date_str = inp.start_datetime.strftime('%Y-%m-%d %H:%M')
                completed_html += f'''
                <tr>
                    <td>{inp.survey_id.title or 'N/A'}</td>
                    <td><span class="badge badge-{('success' if inp.state == 'done' else 'warning')}">{status}</span></td>
                    <td>{score}</td>
                    <td>{date_str}</td>
                </tr>'''
        else:
            completed_html = '<tr><td colspan="4" class="text-muted">You haven\'t taken any tests yet.</td></tr>'

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Tests</title>
    <link rel="stylesheet" href="/test/static/src/css/custom_register.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: flex-start; justify-content: center; padding: 40px 20px; }}
        .dashboard-card {{ background: #ffffff; border-radius: 16px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); width: 100%; max-width: 800px; overflow: hidden; }}
        .dashboard-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; }}
        .dashboard-header h1 {{ color: #ffffff; font-size: 28px; font-weight: 600; margin: 10px 0 0 0; }}
        .dashboard-header p {{ color: rgba(255, 255, 255, 0.9); margin: 10px 0 0 0; font-size: 14px; }}
        .dashboard-logo img {{ max-height: 60px; width: auto; margin-bottom: 10px; }}
        .dashboard-body {{ padding: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #333; font-size: 22px; margin-bottom: 15px; }}
        .test-card {{ border: 2px solid #e0e0e0; border-radius: 12px; margin-bottom: 15px; overflow: hidden; }}
        .test-card-header {{ background: #f8f9fa; padding: 15px 20px; border-bottom: 1px solid #e0e0e0; }}
        .test-card-header h3 {{ margin: 0; color: #333; font-size: 18px; }}
        .test-card-body {{ padding: 20px; }}
        .test-card-body p {{ color: #666; margin: 5px 0; }}
        .btn {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: 600; border: none; cursor: pointer; }}
        .btn:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4); }}
        .btn-secondary {{ background: #6c757d; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        th {{ background: #f8f9fa; color: #666; font-weight: 600; }}
        .badge {{ padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .text-muted {{ color: #999; }}
    </style>
</head>
<body>
    <div class="dashboard-card">
        <div class="dashboard-header">
            <div class="dashboard-logo">
                <img src="{company_logo}" alt="Logo">
            </div>
            <h1>My Tests</h1>
            <p>Welcome, {user.name}!</p>
        </div>
        <div class="dashboard-body">
            <div class="section">
                <h2>Available Tests</h2>
                {surveys_html}
            </div>
            <div class="section">
                <h2>My Completed Tests</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Test</th>
                            <th>Status</th>
                            <th>Score</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {completed_html}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>'''

        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

    @http.route(['/test/register'], type='http', auth='public', website=True)
    def test_register(self, **kw):
        """Register student details - completely custom HTML without Odoo header/footer
        Public route - accessible without login for student self-registration
        """
        user = request.env.user
        
        # If already logged in as admin, redirect to dashboard
        if user.id == request.env.ref('base.user_admin').id:
            try:
                if user.has_group('base.group_system'):
                    return request.redirect('/test/my')
            except Exception:
                pass

        error = False
        success = False
        alert_html = ''

        if request.httprequest.method == 'POST':
            fullname = kw.get('fullname', '').strip()
            username = kw.get('username', '').strip()
            id_number = kw.get('id_number', '').strip()
            email = kw.get('email', '').strip()

            if not fullname or not username:
                error = 'Full Name and Username are required.'
            else:
                existing = request.env['test.user_input'].sudo().search([
                    ('student_username', '=', username)
                ], limit=1)
                if existing:
                    error = 'Username already taken. Please choose another.'
                else:
                    # Get partner_id if user is logged in
                    partner_id = False
                    sudo_user = user.sudo()
                    if sudo_user.partner_id:
                        partner_id = sudo_user.partner_id.id
                    
                    # Create the registration record
                    request.env['test.user_input'].sudo().create({
                        'partner_id': partner_id,
                        'email': email or sudo_user.email or '',
                        'student_fullname': fullname,
                        'student_username': username,
                        'student_id_number': id_number,
                    })
                    success = True

        # Build custom HTML response without Odoo layout
        company_logo = '/web/binary/company_logo'
        csrf_token = request.csrf_token()

        # Error/Success alert HTML
        if error:
            alert_html = '<div class="alert alert-error">' + error + '</div>'
        elif success:
            alert_html = '<div class="alert alert-success">Registration successful! Redirecting to login...</div><meta http-equiv="refresh" content="2;url=/web/login">'
        else:
            alert_html = ''

        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Registration</title>
    <link rel="stylesheet" href="/test/static/src/css/custom_register.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; padding: 20px; }
        .register-card { background: #ffffff; border-radius: 16px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); width: 100%; max-width: 450px; overflow: hidden; }
        .register-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; }
        .register-header h1 { color: #ffffff; font-size: 28px; font-weight: 600; margin: 10px 0 0 0; }
        .register-header p { color: rgba(255, 255, 255, 0.9); margin: 10px 0 0 0; font-size: 14px; }
        .register-logo img { max-height: 60px; width: auto; margin-bottom: 10px; }
        .register-body { padding: 30px; }
        .alert { padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; }
        .alert-error { background: #fee; border: 1px solid #fcc; color: #c33; }
        .alert-success { background: #efe; border: 1px solid #cfc; color: #3c3; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; color: #333; font-weight: 500; font-size: 14px; }
        .form-group input { width: 100%; padding: 14px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; transition: border-color 0.3s; box-sizing: border-box; }
        .form-group input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }
        .submit-btn { width: 100%; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
        .submit-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4); }
        .register-footer { text-align: center; padding: 20px; border-top: 1px solid #eee; }
        .register-footer a { color: #667eea; text-decoration: none; font-size: 14px; }
        .register-footer a:hover { color: #764ba2; text-decoration: underline; }
    </style>
</head>
<body>
    <div class="register-card">
        <div class="register-header">
            <div class="register-logo">
                <img src="''' + company_logo + '''" alt="Logo">
            </div>
            <h1>Student Registration</h1>
            <p>Please fill in your details to continue</p>
        </div>
        <div class="register-body">''' + alert_html + '''<form method="POST" action="/test/register">
                <input type="hidden" name="csrf_token" value="''' + csrf_token + '''"/>
                <div class="form-group">
                    <label for="fullname">Full Name</label>
                    <input type="text" id="fullname" name="fullname" required="required" placeholder="Enter your full name">
                </div>
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required="required" placeholder="Choose a username">
                </div>
                <div class="form-group">
                    <label for="id_number">ID Number</label>
                    <input type="text" id="id_number" name="id_number" placeholder="Enter your ID number">
                </div>
                <div class="form-group">
                    <label for="email">Email (Optional)</label>
                    <input type="email" id="email" name="email" placeholder="Your email address">
                </div>
                <button type="submit" class="submit-btn">Register</button>
            </form>
        </div>
        <div class="register-footer">
            <a href="/web/login">Already have an account? Log in</a>
        </div>
    </div>
</body>
</html>'''

        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

    @http.route(['/test/start/<int:survey_id>'], type='http', auth='user', website=True)
    def test_start(self, survey_id, **kw):
        survey = request.env['test.survey'].sudo().browse(survey_id)
        if not survey.exists():
            return request.redirect('/test/my')
        return self._start_test_by_survey(survey)

    @http.route(['/test/start/token/<string:token>'], type='http', auth='user', website=True)
    def test_start_by_token(self, token, **kw):
        survey = request.env['test.survey'].sudo().search([('access_token', '=', token)], limit=1)
        if not survey:
            return request.redirect('/test/my')
        return self._start_test_by_survey(survey)

    def _start_test_by_survey(self, survey):
        user = request.env.user
        partner_id = user.sudo().partner_id.id if user.sudo().partner_id else None
        if not partner_id:
            return request.redirect('/test/register')
        registration = request.env['test.user_input'].sudo().search([
            ('partner_id', '=', partner_id),
            ('student_fullname', '!=', False),
            ('student_username', '!=', False),
            ('survey_id', '=', False),
        ], limit=1)
        existing_input = request.env['test.user_input'].sudo().search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', partner_id),
            ('state', '=', 'new'),
        ], limit=1)
        if not existing_input:
            vals = {
                'survey_id': survey.id,
                'partner_id': partner_id,
                'email': user.sudo().email or '',
                'access_token': survey.access_token,
            }
            if registration:
                vals.update({
                    'student_fullname': registration.student_fullname,
                    'student_username': registration.student_username,
                    'student_id_number': registration.student_id_number,
                })
            existing_input = request.env['test.user_input'].sudo().create(vals)
        return request.redirect(f'/test/take/{survey.id}')

    @http.route(['/test/results/<model("test.user_input"):input_id>'], type='http', auth='user', website=True)
    def test_results(self, input_id, **kw):
        values = {'user_input': input_id, 'page_name': 'test_results'}
        return request.render('test.test_results_page', values)

    @http.route(['/test/take/<model("test.survey"):survey>'], type='http', auth='user', website=True)
    def test_take(self, survey, **kw):
        all_questions = request.env['test.question'].sudo().search([
            ('survey_id', '=', survey.id)], order='sequence ASC')
        total_questions = len(all_questions)
        if total_questions > 25:
            import random
            selected_ids = random.sample(list(all_questions.ids), 25)
            questions = request.env['test.question'].sudo().browse(selected_ids)
            questions = questions.sorted(key=lambda q: q.sequence)
        else:
            questions = all_questions
        partner_id = request.env.user.partner_id.id if request.env.user.partner_id else None
        if not partner_id:
            return request.redirect('/test/register')
        user_input = request.env['test.user_input'].sudo().search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', partner_id),
            ('state', '=', 'new')], limit=1)
        if not user_input:
            user_input = request.env['test.user_input'].sudo().create({
                'survey_id': survey.id,
                'partner_id': partner_id,
                'email': request.env.user.email,
                'access_token': survey.access_token,
            })
        answered_lines = request.env['test.user.input.line'].sudo().search([
            ('user_input_id', '=', user_input.id)])
        answered_question_ids = answered_lines.mapped('question_id').ids
        values = {
            'survey': survey,
            'questions': questions,
            'user_input': user_input,
            'answered_question_ids': answered_question_ids,
            'total_display': len(questions),
            'page_name': 'test_take',
        }
        return request.render('test.test_take_page', values)

    @http.route(['/test/take/<model("test.survey"):survey>/question/<int:q_num>'], type='http', auth='user', website=True)
    def test_take_question(self, survey, q_num, **kw):
        partner_id = request.env.user.partner_id.id if request.env.user.partner_id else None
        if not partner_id:
            return request.redirect('/test/register')
        user_input = request.env['test.user_input'].sudo().search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', partner_id),
            ('state', '=', 'new')], limit=1)
        if not user_input:
            return request.redirect(f'/test/take/{survey.id}')
        all_questions = request.env['test.question'].sudo().search([
            ('survey_id', '=', survey.id)], order='sequence ASC')
        total_questions = len(all_questions)
        if total_questions > 25:
            import random
            random.seed(user_input.id)
            selected_ids = random.sample(list(all_questions.ids), 25)
            questions = request.env['test.question'].sudo().browse(selected_ids)
            questions = questions.sorted(key=lambda q: q.sequence)
        else:
            questions = all_questions
        if q_num < 1 or q_num > len(questions):
            return request.redirect(f'/test/take/{survey.id}')
        current_question = questions[q_num - 1]
        answers = request.env['test.question.answer'].sudo().search([
            ('question_id', '=', current_question.id)
        ]) if current_question.question_type in ['simple_choice', 'multiple_choice'] else request.env['test.question.answer']
        user_line = request.env['test.user.input.line'].sudo().search([
            ('user_input_id', '=', user_input.id),
            ('question_id', '=', current_question.id)], limit=1)
        answered_lines = request.env['test.user.input.line'].sudo().search([
            ('user_input_id', '=', user_input.id)])
        answered_question_ids = answered_lines.mapped('question_id').ids
        values = {
            'survey': survey,
            'questions': questions,
            'question': current_question,
            'question_number': q_num,
            'total_questions': len(questions),
            'answers': answers,
            'user_input': user_input,
            'user_line': user_line,
            'answered_question_ids': answered_question_ids,
            'page_name': 'test_take_question',
        }
        return request.render('test.test_take_question_page', values)

    @http.route(['/test/take/<model("test.survey"):survey>/answer'], type='http', auth='user', website=True, methods=['POST'])
    def test_take_answer(self, survey, **kw):
        question_id = int(kw.get('question_id', 0))
        answer_type = kw.get('answer_type', 'free_text')
        partner_id = request.env.user.partner_id.id if request.env.user.partner_id else None
        if not partner_id:
            return request.redirect('/test/register')
        user_input = request.env['test.user_input'].sudo().search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', partner_id),
            ('state', '=', 'new')], limit=1)
        if not user_input:
            return request.redirect(f'/test/take/{survey.id}')
        user_line = request.env['test.user.input.line'].sudo().search([
            ('user_input_id', '=', user_input.id),
            ('question_id', '=', question_id)], limit=1)
        if not user_line:
            user_line = request.env['test.user.input.line'].sudo().create({
                'user_input_id': user_input.id,
                'question_id': question_id,
                'answer_type': answer_type,
            })
        if answer_type == 'free_text':
            user_line.write({'value_free_text': kw.get('value_free_text', '')})
        elif answer_type == 'simple_choice':
            user_line.write({'value_suggested': int(kw.get('value_suggested', 0))})
        elif answer_type == 'multiple_choice':
            selected_ids = [int(x) for x in kw.getlist('value_suggested_ids', [])]
            user_line.write({'value_suggested_ids': [(6, 0, selected_ids)]})
        elif answer_type == 'numerical_box':
            user_line.write({'value_numerical': float(kw.get('value_numerical', 0))})
        redirect_q = kw.get('redirect_q')
        if redirect_q:
            return request.redirect(f'/test/take/{survey.id}/question/{int(redirect_q)}')
        return request.redirect(f'/test/take/{survey.id}')

    @http.route(['/test/take/<model("test.survey"):survey>/finish'], type='http', auth='user', website=True)
    def test_take_finish(self, survey, **kw):
        partner_id = request.env.user.partner_id.id if request.env.user.partner_id else None
        if not partner_id:
            return request.redirect('/test/register')
        user_input = request.env['test.user_input'].sudo().search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', partner_id),
            ('state', '=', 'new')], limit=1)
        if user_input:
            user_input.write({'state': 'done'})
        return request.redirect('/test/my')
