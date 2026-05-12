# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from odoo import http
from odoo.http import request


class TestStudentPortal(http.Controller):
    """Student Portal Controller for Test Module"""

    @http.route(['/web'], type='http', auth='public', website=True)
    def web_redirect(self, **kw):
        if request.env.user._is_public():
            return None
        user = request.env.user
        try:
            if user.has_group('base.group_system'):
                return request.redirect('/odoo')
        except Exception:
            pass
        return request.redirect('/test/register')

    @http.route(['/test'], type='http', auth='user', website=True)
    def test_index(self, **kw):
        user = request.env.user
        try:
            if user.has_group('base.group_system'):
                return request.redirect('/test/admin')
        except Exception:
            pass
        return request.redirect('/test/register')

    @http.route(['/test/my'], type='http', auth='user', website=True)
    def test_my(self, **kw):
        user = request.env.user
        sudo_user = user.sudo()
        partner_id = sudo_user.partner_id.id if sudo_user.partner_id else False

        latest_registration = request.env['test.user_input'].sudo().search([
            ('partner_id', '=', partner_id),
            ('student_fullname', '!=', False),
            ('student_username', '!=', False),
            ('survey_id', '=', False),
        ], order='id desc', limit=1) if partner_id else None

        student_name = latest_registration.student_fullname if latest_registration else user.name
        surveys = request.env['test.survey'].sudo().search([('active', '=', True)])

        user_inputs = request.env['test.user_input'].sudo().search([
            ('partner_id', '=', partner_id),
            ('survey_id', '!=', False)
        ]) if partner_id else request.env['test.user_input'].sudo().browse([])

        company_logo = '/web/binary/company_logo'

        surveys_html = ''
        if surveys:
            for survey in surveys:
                surveys_html += f'''
                <div class="test-card">
                    <div class="test-card-header"><h3>{survey.title}</h3></div>
                    <div class="test-card-body">
                        <p>{"No description available." if not survey.description else survey.description}</p>
                        <p><strong>Questions:</strong> {survey.question_count or 0}</p>
                        <a href="/test/start/{survey.id}" class="btn btn-start">Start Test</a>
                    </div>
                </div>'''
        else:
            surveys_html = '<p class="text-muted">No tests available at the moment.</p>'

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
            <div class="dashboard-logo"><img src="{company_logo}" alt="Logo"></div>
            <h1>My Tests</h1>
            <p>Welcome, {student_name}!</p>
        </div>
        <div class="dashboard-body">
            <div class="section"><h2>Available Tests</h2>{surveys_html}</div>
            <div class="section">
                <h2>My Completed Tests</h2>
                <table>
                    <thead><tr><th>Test</th><th>Status</th><th>Score</th><th>Date</th></tr></thead>
                    <tbody>{completed_html}</tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>'''
        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

    @http.route(['/test/register'], type='http', auth='public', website=True)
    def test_register(self, **kw):
        user = request.env.user
        if user._is_public():
            return request.redirect('/web/login?redirect=/test/register')
        try:
            if user.has_group('base.group_system'):
                return request.redirect('/test/admin')
        except Exception:
            pass

        error = False
        success = False

        if request.httprequest.method == 'POST':
            fullname = kw.get('fullname', '').strip()
            username = kw.get('username', '').strip()
            if not fullname or not username:
                error = 'Full Name and Username are required.'
            else:
                existing = request.env['test.user_input'].sudo().search([
                    ('student_username', '=', username)
                ], limit=1)
                if existing:
                    error = 'Username already taken. Please choose another.'
                else:
                    partner_id = user.sudo().partner_id.id if user.sudo().partner_id else False
                    request.env['test.user_input'].sudo().create({
                        'partner_id': partner_id,
                        'email': user.sudo().email or '',
                        'student_fullname': fullname,
                        'student_username': username,
                        'student_class': kw.get('student_class', ''),
                        'student_id_number': '',
                        'survey_id': False,
                    })
                    success = True

        if success:
            return request.redirect('/test/my')

        company_logo = '/web/binary/company_logo'
        csrf_token = request.csrf_token()
        error_html = f'<div class="alert alert-error">{error}</div>' if error else ''

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Registration</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; padding: 20px; }}
        .register-card {{ background: #ffffff; border-radius: 16px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); width: 100%; max-width: 450px; overflow: hidden; }}
        .register-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; }}
        .register-header h1 {{ color: #ffffff; font-size: 28px; font-weight: 600; margin: 10px 0 0 0; }}
        .register-header p {{ color: rgba(255, 255, 255, 0.9); margin: 10px 0 0 0; font-size: 14px; }}
        .register-logo img {{ max-height: 60px; width: auto; margin-bottom: 10px; }}
        .register-body {{ padding: 30px; }}
        .alert {{ padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; }}
        .alert-error {{ background: #fee; border: 1px solid #fcc; color: #c33; }}
        .form-group {{ margin-bottom: 20px; }}
        .form-group label {{ display: block; margin-bottom: 8px; color: #333; font-weight: 500; font-size: 14px; }}
        .form-group input {{ width: 100%; padding: 14px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 15px; transition: border-color 0.3s; box-sizing: border-box; }}
        .form-group input:focus {{ outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }}
        .submit-btn {{ width: 100%; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }}
        .submit-btn:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4); }}
        .register-footer {{ text-align: center; padding: 20px; border-top: 1px solid #eee; }}
        .register-footer a {{ color: #667eea; text-decoration: none; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="register-card">
        <div class="register-header">
            <div class="register-logo"><img src="{company_logo}" alt="Logo"></div>
            <h1>Student Registration</h1>
            <p>Please enter your details to continue</p>
        </div>
        <div class="register-body">
            {error_html}
            <form method="POST" action="/test/register">
                <input type="hidden" name="csrf_token" value="{csrf_token}"/>
                <div class="form-group">
                    <label for="fullname">Full Name *</label>
                    <input type="text" id="fullname" name="fullname" required placeholder="Enter your full name">
                </div>
                <div class="form-group">
                    <label for="username">Username *</label>
                    <input type="text" id="username" name="username" required placeholder="Choose a username">
                    <small style="color:#666; font-size:12px; display:block; margin-top:5px;">This username will be used to identify your test results</small>
                </div>
                <button type="submit" class="submit-btn">Register &amp; Continue</button>
            </form>
        </div>
        <div class="register-footer"><a href="/web/logout">Logout</a></div>
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
        ], order='id desc', limit=1)

        existing_input = request.env['test.user_input'].sudo().search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', partner_id),
            ('state', '=', 'new')
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
        user_input = input_id.sudo()
        is_admin = False
        try:
            is_admin = request.env.user.has_group('base.group_system')
        except Exception:
            pass
        values = {
            'page_name': 'test_results',
            'user_input': user_input,
            'is_admin': is_admin,
        }
        return request.render('test.test_results_page', values)

    @http.route(['/test/admin'], type='http', auth='user', website=True)
    def test_admin(self, **kw):
        user = request.env.user
        is_admin = False
        try:
            is_admin = user.has_group('base.group_system')
        except Exception:
            pass
        if not is_admin:
            return request.redirect('/test/my')

        surveys = request.env['test.survey'].sudo().search([])
        all_inputs = request.env['test.user_input'].sudo().search([('state', '=', 'done')])
        total_tests = len(surveys)
        total_completions = len(all_inputs)

        surveys_html = ''
        if surveys:
            for survey in surveys:
                completions = request.env['test.user_input'].sudo().search([
                    ('survey_id', '=', survey.id), ('state', '=', 'done')
                ])
                completion_count = len(completions)
                avg_score = sum([c.scoring_percentage or 0 for c in completions]) / completion_count if completion_count > 0 else 0
                surveys_html += f'''
                <div class="test-card">
                    <div class="test-card-header">
                        <h3>{survey.title}</h3>
                        <span class="badge badge-primary">{completion_count} Completed</span>
                    </div>
                    <div class="test-card-body">
                        <p>{"No description available." if not survey.description else survey.description}</p>
                        <p><strong>Questions:</strong> {survey.question_count or 0}</p>
                        <p><strong>Avg Score:</strong> {avg_score:.1f}%</p>
                        <a href="/test/start/{survey.id}" class="btn">Take Test</a>
                    </div>
                </div>'''
        else:
            surveys_html = '<p>No tests available.</p>'

        company_logo = '/web/binary/company_logo'
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Management - Admin</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Segoe UI", sans-serif; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: flex-start; justify-content: center; padding: 40px 20px; }}
        .dashboard-card {{ background: #fff; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); width: 100%; max-width: 900px; overflow: hidden; }}
        .dashboard-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; }}
        .dashboard-header h1 {{ color: #fff; font-size: 28px; font-weight: 600; margin: 10px 0 0; }}
        .dashboard-header p {{ color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 14px; }}
        .dashboard-logo img {{ max-height: 60px; width: auto; margin-bottom: 10px; }}
        .dashboard-body {{ padding: 30px; }}
        .stats-row {{ display: flex; gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ flex: 1; background: #f8f9fa; padding: 20px; border-radius: 12px; text-align: center; }}
        .stat-card h3 {{ color: #667eea; font-size: 32px; margin: 0; }}
        .stat-card p {{ color: #666; margin: 5px 0 0; }}
        .test-card {{ border: 2px solid #e0e0e0; border-radius: 12px; margin-bottom: 15px; overflow: hidden; }}
        .test-card-header {{ background: #f8f9fa; padding: 15px 20px; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; }}
        .test-card-header h3 {{ margin: 0; color: #333; font-size: 18px; }}
        .test-card-body {{ padding: 20px; }}
        .test-card-body p {{ color: #666; margin: 5px 0; }}
        .btn {{ display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; text-decoration: none; border-radius: 8px; font-size: 14px; font-weight: 600; border: none; cursor: pointer; margin-right: 10px; }}
        .badge {{ padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .badge-primary {{ background: #667eea; color: #fff; }}
        section {{ margin-bottom: 30px; }}
    </style>
</head>
<body>
    <div class="dashboard-card">
        <div class="dashboard-header">
            <div class="dashboard-logo"><img src="{company_logo}" alt="Logo"></div>
            <h1>Test Management - Admin</h1>
            <p>Welcome, {user.name}!</p>
        </div>
        <div class="dashboard-body">
            <div class="stats-row">
                <div class="stat-card"><h3>{total_tests}</h3><p>Total Tests</p></div>
                <div class="stat-card"><h3>{total_completions}</h3><p>Completed</p></div>
            </div>
            <section><h2 style="margin-bottom:15px;">All Tests</h2>{surveys_html}</section>
            <section><a href="/odoo" class="btn">Back to Odoo</a></section>
        </div>
    </div>
</body>
</html>'''
        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

    def _get_questions_for_input(self, survey, user_input):
        """Return the deterministic question list for a given user_input."""
        all_questions = request.env['test.question'].sudo().search([
            ('survey_id', '=', survey.id)], order='sequence ASC')
        total_questions = len(all_questions)
        questions_limit = request.env['test.settings'].sudo().get_questions_limit()
        if total_questions > questions_limit:
            import random
            rng = random.Random(user_input.id)   # seed by input id so order is stable
            selected_ids = rng.sample(list(all_questions.ids), questions_limit)
            questions = request.env['test.question'].sudo().browse(selected_ids)
            questions = questions.sorted(key=lambda q: q.sequence)
        else:
            questions = all_questions
        return questions

    @http.route(['/test/take/<model("test.survey"):survey>'], type='http', auth='user', website=True)
    def test_take(self, survey, **kw):
        partner_id = request.env.user.partner_id.id if request.env.user.partner_id else None
        if not partner_id:
            return request.redirect('/test/register')

        user_input = request.env['test.user_input'].sudo().search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', partner_id),
            ('state', '=', 'new')], limit=1)

        if not user_input:
            registration = request.env['test.user_input'].sudo().search([
                ('partner_id', '=', partner_id),
                ('student_fullname', '!=', False),
                ('student_username', '!=', False),
                ('survey_id', '=', False),
            ], order='id desc', limit=1)
            vals = {
                'survey_id': survey.id,
                'partner_id': partner_id,
                'email': request.env.user.email or '',
                'access_token': survey.access_token,
            }
            if registration:
                vals.update({
                    'student_fullname': registration.student_fullname,
                    'student_username': registration.student_username,
                })
            user_input = request.env['test.user_input'].sudo().create(vals)

        questions = self._get_questions_for_input(survey, user_input)
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

    @http.route(['/test/take/<model("test.survey"):survey>/question/<int:q_num>'],
                type='http', auth='user', website=True)
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

        questions = self._get_questions_for_input(survey, user_input)

        if q_num < 1 or q_num > len(questions):
            return request.redirect(f'/test/take/{survey.id}/question/1')

        current_question = questions[q_num - 1]
        answers = request.env['test.question.answer'].sudo().search([
            ('question_id', '=', current_question.id)
        ]) if current_question.question_type in ['simple_choice', 'multiple_choice'] \
            else request.env['test.question.answer']

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
            'total_display': len(questions),          # needed by template progress bar
            'answers': answers,
            'user_input': user_input,
            'user_line': user_line,
            'answered_question_ids': answered_question_ids,
            'page_name': 'test_take_question',
        }
        return request.render('test.test_take_question_page', values)

    # ------------------------------------------------------------------ #
    #  Single, clean answer endpoint                                       #
    # ------------------------------------------------------------------ #
    @http.route(['/test/take/<model("test.survey"):survey>/answer'],
                type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def test_take_answer(self, survey, **kw):
        """Save answer and return JSON so the JS can navigate without a full reload."""

        question_id  = int(kw.get('question_id', 0))
        answer_type  = kw.get('answer_type', 'free_text')
        action       = kw.get('action', 'save')          # 'save' | 'navigate' | 'finish'
        redirect_to  = kw.get('redirect_to', '')         # target question number for 'navigate'

        partner_id = request.env.user.partner_id.id if request.env.user.partner_id else None
        if not partner_id:
            return self._json({'success': False, 'redirect': '/test/register'})

        # --- resolve user_input -------------------------------------------
        user_input = request.env['test.user_input'].sudo().search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', partner_id),
            ('state', '=', 'new')], limit=1)

        if not user_input:
            registration = request.env['test.user_input'].sudo().search([
                ('partner_id', '=', partner_id),
                ('student_fullname', '!=', False),
                ('student_username', '!=', False),
                ('survey_id', '=', False),
            ], order='id desc', limit=1)
            vals = {
                'survey_id': survey.id,
                'partner_id': partner_id,
                'email': request.env.user.email or '',
                'access_token': survey.access_token,
            }
            if registration:
                vals.update({
                    'student_fullname': registration.student_fullname,
                    'student_username': registration.student_username,
                })
            user_input = request.env['test.user_input'].sudo().create(vals)

        # --- save the answer (only if a question was supplied) ------------
        if question_id:
            user_line = request.env['test.user.input.line'].sudo().search([
                ('user_input_id', '=', user_input.id),
                ('question_id', '=', question_id)], limit=1)

            if not user_line:
                user_line = request.env['test.user.input.line'].sudo().create({
                    'user_input_id': user_input.id,
                    'question_id': question_id,
                    'answer_type': answer_type,
                })

            if answer_type in ['text_box', 'free_text']:
                user_line.write({'value_free_text': kw.get('value_free_text', '')})
            elif answer_type == 'simple_choice':
                val = kw.get('value_suggested', 0)
                if val:
                    user_line.write({'value_suggested': int(val)})
            elif answer_type == 'multiple_choice':
                selected_ids = [int(x) for x in request.httprequest.form.getlist('value_suggested_ids')]
                user_line.write({'value_suggested_ids': [(6, 0, selected_ids)]})
            elif answer_type == 'numerical_box':
                val = kw.get('value_numerical', 0)
                user_line.write({'value_numerical': float(val) if val else 0})

        # --- decide what to do next ---------------------------------------
        if action == 'finish':
            user_input.write({'state': 'done'})
            return self._json({'success': True, 'redirect': f'/test/results/{user_input.id}'})

        if action == 'navigate' and redirect_to:
            try:
                q_num = int(redirect_to)
                questions = self._get_questions_for_input(survey, user_input)
                q_num = max(1, min(q_num, len(questions)))
            except (ValueError, TypeError):
                q_num = 1
            return self._json({'success': True, 'redirect': f'/test/take/{survey.id}/question/{q_num}'})

        # plain save — return answered count so the progress bar can update
        answered_lines = request.env['test.user.input.line'].sudo().search([
            ('user_input_id', '=', user_input.id)])
        answered_count = len(answered_lines.mapped('question_id'))
        return self._json({'success': True, 'answered_count': answered_count})

    # ------------------------------------------------------------------ #
    #  Explicit finish endpoint (Finalise button fallback)                 #
    # ------------------------------------------------------------------ #
    @http.route(['/test/take/<model("test.survey"):survey>/finish'],
                type='http', auth='user', website=True)
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
            return request.redirect(f'/test/results/{user_input.id}')
        return request.redirect('/test/my')

    # ------------------------------------------------------------------ #
    #  Helper                                                              #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _json(data):
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')]
        )