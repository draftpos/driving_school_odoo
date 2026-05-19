# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import random
from datetime import datetime, timedelta
from odoo import http, _, fields
from odoo.http import request
from odoo.addons.web.controllers.home import Home
from odoo.addons.portal.controllers.portal import CustomerPortal


class TestCustomerPortal(CustomerPortal):
    """Override the portal home to redirect students to the test registration page."""

    @http.route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, page=0, date_begin=None, date_end=None, sortby=None, **kw):
        """
        Intercept the portal home page (/my).
        Non-admin users (students) are redirected to /test/register.
        Admins fall through to the standard portal/backend.
        """
        user = request.env.user
        try:
            if user.has_group('base.group_system'):
                return request.redirect('/odoo')
        except Exception:
            pass
        return request.redirect('/test/register')


class TestHome(Home):
    """Override Odoo's Home controller to intercept post-login redirects."""

    def _login_redirect(self, uid, redirect=None):
        """
        Called immediately after successful login.
        Redirects non-admin users straight to /test/register
        so they never reach the backend or portal home.
        If a specific redirect URL was already set (e.g. from a link),
        honour it for admins only.
        """
        try:
            user = request.env['res.users'].sudo().browse(uid)
            if user.has_group('base.group_system'):
                return super()._login_redirect(uid, redirect=redirect)
        except Exception:
            pass
        # All non-admin users (students, portal users) go to register
        return redirect if redirect and redirect.startswith('/test') else '/test/register'


class TestStudentPortal(http.Controller):
    """Student Portal Controller for Test Module"""

    @http.route(['/test/debug/settings'], type='http', auth='user', website=True)
    def test_debug_settings(self, **kw):
        all_settings = request.env['test.settings'].sudo().search([], order='id ASC')
        active = request.env['test.settings'].sudo().get_default_settings()
        rows = ''.join(
            f"<tr style='background:{'#e0ffe0' if s.id == active.id else 'white'}'>"
            f"<td style='padding:8px;border:1px solid #ccc'>{s.id}</td>"
            f"<td style='padding:8px;border:1px solid #ccc'>{s.default_time_limit} mins</td>"
            f"<td style='padding:8px;border:1px solid #ccc'>{'← ACTIVE (portal reads this)' if s.id == active.id else ''}</td>"
            f"</tr>"
            for s in all_settings
        )
        return f"""
            <h2>Settings Records in Database</h2>
            <table style='border-collapse:collapse'>
                <tr style='background:#667eea;color:white'>
                    <th style='padding:8px;border:1px solid #ccc'>ID</th>
                    <th style='padding:8px;border:1px solid #ccc'>Time Limit</th>
                    <th style='padding:8px;border:1px solid #ccc'>Status</th>
                </tr>
                {rows}
            </table>
            <br/><b>Portal currently uses: {active.default_time_limit} mins (Record ID: {active.id})</b>
        """

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

    @http.route(['/web/login_successful'], type='http', auth='user', website=True, sitemap=False)
    def login_successful(self, **kwargs):
        """
        Odoo 19 redirects portal/external users here after login.
        We intercept it to send students to /test/register instead.
        """
        user = request.env.user
        try:
            if user.has_group('base.group_system'):
                return request.redirect('/odoo')
        except Exception:
            pass
        return request.redirect('/test/register')

    @http.route(['/my', '/my/home'], type='http', auth='user', website=True)
    def portal_home_redirect(self, **kw):
        """
        Portal users land on /my after login (Odoo portal home).
        Redirect students to /test/register instead.
        Admins are sent to the backend.
        """
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
        student_username = latest_registration.student_username if latest_registration else '-'
        student_class = latest_registration.student_class if latest_registration else '-'
        class_mapping = {
            'class1': 'Class 1',
            'class2': 'Class 2',
            'class4': 'Class 4',
            'class2and4': 'Class 2 & 4'
        }
        student_class_label = class_mapping.get(student_class, student_class)

        surveys = request.env['test.survey'].sudo().search([('active', '=', True)])

        user_inputs = request.env['test.user_input'].sudo().search([
            ('partner_id', '=', partner_id),
            ('survey_id', '!=', False)
        ]) if partner_id else request.env['test.user_input'].sudo().browse([])

        company_logo = '/web/binary/company_logo'

        surveys_html = ''
        if surveys:
            for survey in surveys:
                limit_text = f"{survey.time_limit} mins" if survey.time_limit else "No limit"
                avg_score = survey.get_average_score()
                surveys_html += f'''
                <div class="test-card">
                    <div class="test-card-header"><h3>{survey.title}</h3></div>
                    <div class="test-card-body">
                        <t t-set="settings" t-value="request.env['test.settings'].sudo().get_default_settings()"/>
                        <t t-set="q_limit" t-value="settings.get_questions_limit() or 25"/>
                        <t t-set="display_q_count" t-value="min(survey.question_count, q_limit)"/>
                        <p>Questions: {display_q_count}</p>
                        <p>Time Limit: <strong>{limit_text}</strong></p>
                        <p>Avg. Score: {avg_score:.1f}%</p>
                        <div style="margin-top: 15px;"><a href="/test/start/{survey.id}" class="btn btn-start">Start Test</a></div>
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
        body {{ font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; height: 100vh; width: 100vw; overflow: hidden; background: #f8fafc; }}
        .dashboard-container {{ height: 100vh; width: 100vw; display: flex; flex-direction: column; }}
        .dashboard-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; color: white; }}
        .dashboard-header h1 {{ font-size: 18px; font-weight: 600; }}
        .dashboard-logo img {{ max-height: 30px; width: auto; }}
        .dashboard-body {{ flex: 1; padding: 20px 40px; overflow-y: auto; background: #f1f5f9; }}
        .section {{ margin-bottom: 25px; }}
        .section h2 {{ color: #1e293b; font-size: 16px; margin-bottom: 15px; border-left: 3px solid #667eea; padding-left: 12px; }}
        .test-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }}
        .test-card {{ background: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); overflow: hidden; transition: transform 0.2s; border: 1px solid #e2e8f0; }}
        .test-card-header {{ background: #f8fafc; padding: 10px 15px; border-bottom: 1px solid #e2e8f0; }}
        .test-card-header h3 {{ margin: 0; color: #1e293b; font-size: 14px; font-weight: 600; }}
        .test-card-body {{ padding: 12px; text-align: center; }}
        .test-card-body p {{ color: #64748b; margin-bottom: 10px; font-size: 12px; }}
        .btn {{ display: inline-block; width: 100%; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 600; border: none; cursor: pointer; }}
        .btn-outline {{ background: white; color: #667eea; border: 2px solid #667eea; margin-top: 10px; }}
        table {{ width: 100%; border-collapse: separate; border-spacing: 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        th, td {{ padding: 16px 24px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f8fafc; color: #64748b; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
        .badge {{ padding: 6px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; }}
        .badge-success {{ background: #dcfce7; color: #166534; }}
        .badge-warning {{ background: #fef9c3; color: #854d0e; }}
        @media (max-width: 1200px) {{ .test-grid {{ grid-template-columns: repeat(3, 1fr); }} }}
        @media (max-width: 900px) {{ .test-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
        @media (max-width: 600px) {{ .test-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="dashboard-header">
            <div class="dashboard-logo"><img src="{company_logo}" alt="Logo"></div>
            <h1>Student Portal</h1>
            <div style="text-align: right;">
                <p>Welcome, <strong>{student_name}</strong></p>
                <p style="font-size: 12px; opacity: 0.8; margin-bottom: 5px;">ID: {student_username} | Class: {student_class_label}</p>
                <a href="/test/register" style="color: white; font-size: 12px; text-decoration: underline;">Switch Profile</a>
            </div>
        </div>
        <div class="dashboard-body">
            <div class="section">
                <h2>Available Tests</h2>
                <div class="test-grid">{surveys_html}</div>
            </div>
            <div style="margin-top: 20px;">
                <a href="/web/logout" class="btn btn-outline" style="width: auto; padding: 10px 20px;">Logout</a>
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
            is_login = kw.get('login_mode') == '1'

            if not username or (not is_login and not fullname):
                error = 'Required fields are missing.'
            else:
                existing = request.env['test.user_input'].sudo().search([
                    ('student_username', '=', username)
                ], limit=1)
                
                if existing:
                    # Check if username belongs to current user
                    if existing.partner_id.id == user.partner_id.id:
                        return request.redirect('/test/my')
                    error = 'Username already taken by another user.'
                elif is_login:
                    error = 'Username not found. Please register first.'
                else:
                    partner_id = user.partner_id.id if user.partner_id else None
                    
                    # Create or update student participant record
                    student = request.env['test.student'].sudo().search([('username', '=', username)], limit=1)
                    if not student:
                        student = request.env['test.student'].sudo().create({
                            'name': fullname,
                            'username': username,
                            'student_class': kw.get('student_class', ''),
                            'partner_id': partner_id,
                        })
                    else:
                        if student.partner_id and student.partner_id.id != partner_id:
                            error = "This username is already taken by another account."
                        else:
                            student.sudo().write({
                                'name': fullname,
                                'student_class': kw.get('student_class', ''),
                                'partner_id': partner_id,
                            })
                    
                    if not error:
                        request.env['test.user_input'].sudo().create({
                            'student_id': student.id,
                            'partner_id': partner_id,
                            'email': user.sudo().email or '',
                            'student_fullname': fullname,
                            'student_username': username,
                            'student_class': kw.get('student_class', ''),
                            'student_id_number': kw.get('id_number', ''),
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
    <div class="register-card" id="main_card">
        <div class="register-header">
            <div class="register-logo"><img src="{company_logo}" alt="Logo"></div>
            <h1 id="page_title">Student Registration</h1>
            <p id="page_subtitle">Please enter your details to continue</p>
        </div>
        <div class="register-body" id="register_section">
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
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 5px;">
                        <small style="color:#666; font-size:12px;">This username will identify your results</small>
                        <small style="color:#667eea; font-size:12px; cursor: pointer; font-weight: 600;" onclick="toggleMode('login')">Already registered?</small>
                    </div>
                </div>
                <div class="form-group">
                    <label for="id_number">ID Number</label>
                    <input type="text" id="id_number" name="id_number" placeholder="Enter your ID number">
                </div>
                <div class="form-group">
                    <label for="student_class">Class</label>
                    <select id="student_class" name="student_class" required="required" style="width:100%; padding:14px 16px; border:2px solid #e0e0e0; border-radius:8px; font-size:15px;">
                        <option value="">Select your class</option>
                        <option value="class1">Class 1</option>
                        <option value="class2">Class 2</option>
                        <option value="class4">Class 4</option>
                        <option value="class2and4">Class 2 &amp; 4</option>
                    </select>
                </div>
                <button type="submit" class="submit-btn">Register &amp; Continue</button>
            </form>
        </div>
        
        <div class="register-body" id="login_section" style="display: none;">
            {error_html}
            <form method="POST" action="/test/register">
                <input type="hidden" name="csrf_token" value="{csrf_token}"/>
                <input type="hidden" name="login_mode" value="1"/>
                <div class="form-group">
                    <label for="login_username">Enter your Username</label>
                    <input type="text" id="login_username" name="username" required placeholder="Your registered username" style="font-size: 18px; text-align: center; border-color: #667eea;">
                    <p style="margin-top: 15px; color: #64748b; font-size: 13px; text-align: center;">Enter the username you used when you first registered to access your tests.</p>
                </div>
                <button type="submit" class="submit-btn" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">Login &amp; Continue</button>
                <div style="text-align: center; margin-top: 20px;">
                    <a href="#" onclick="toggleMode('register')" style="color: #64748b; text-decoration: none; font-size: 14px;">&larr; Back to Registration</a>
                </div>
            </form>
        </div>
        
        <div class="register-footer"><a href="/web/logout">Logout Account</a></div>
    </div>
    <script>
        function toggleMode(mode) {{
            const reg = document.getElementById('register_section');
            const log = document.getElementById('login_section');
            const title = document.getElementById('page_title');
            const subtitle = document.getElementById('page_subtitle');
            
            if (mode === 'login') {{
                reg.style.display = 'none';
                log.style.display = 'block';
                title.innerText = 'Student Login';
                subtitle.innerText = 'Welcome back! Enter your username';
            }} else {{
                reg.style.display = 'block';
                log.style.display = 'none';
                title.innerText = 'Student Registration';
                subtitle.innerText = 'Please enter your details to continue';
            }}
        }}
        // If there was a login error, stay on login mode
        if (window.location.search.includes('login_mode=1') || "{'login' if kw.get('login_mode') else ''}" === 'login') {{
            toggleMode('login');
        }}
    </script>
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
                    'student_id': registration.student_id.id if registration.student_id else False,
                    'student_fullname': registration.student_fullname,
                    'student_username': registration.student_username,
                    'student_id_number': registration.student_id_number,
                    'student_class': registration.student_class,
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
        questions = self._get_questions_for_input(user_input.survey_id, user_input)
        values = {
            'page_name': 'test_results',
            'user_input': user_input,
            'questions': questions,
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
                
                settings = request.env['test.settings'].sudo().get_default_settings()
                limit_text = f"{settings.default_time_limit} mins"
                surveys_html += f'''
                <div class="test-card">
                    <div class="test-card-header">
                        <h3>{survey.title}</h3>
                        <span class="badge badge-primary">{completion_count} Participants</span>
                    </div>
                    <div class="test-card-body">
                        <p style="margin-bottom: 10px; font-size: 0.9em; color: #64748b;">
                            Questions: {min(survey.question_count, settings.get_questions_limit() or 25)}
                        </p>
                        <p style="margin-bottom: 10px; font-size: 0.9em; color: #64748b;">Time Limit: <strong>{limit_text}</strong></p>
                        <p style="margin-bottom: 20px; font-size: 0.9em; color: #64748b;">Avg. Score: {avg_score:.1f}%</p>
                        <a href="/test/take/{survey.id}" class="btn" style="display: block; text-align: center; width: 100%;">Take Test Preview</a>
                    </div>
                </div>'''
        else:
            surveys_html = '<p>No tests available.</p>'

        participants_html = ''
        recent_inputs = request.env['test.user_input'].sudo().search([
            ('survey_id', '!=', False),
            ('state', '=', 'done')
        ], order='end_datetime desc', limit=20)

        if recent_inputs:
            for inp in recent_inputs:
                score = f'{inp.scoring_percentage:.1f}%' if inp.scoring_percentage else '0%'
                date_str = inp.end_datetime.strftime('%Y-%m-%d %H:%M') if inp.end_datetime else '-'
                participants_html += f'''
                <tr>
                    <td>{inp.student_username or '-'}</td>
                    <td>{inp.student_fullname or '-'}</td>
                    <td>{inp.survey_id.title or 'N/A'}</td>
                    <td><span class="badge badge-success">{score}</span></td>
                    <td>{date_str}</td>
                </tr>'''
        else:
            participants_html = '<tr><td colspan="5" class="text-muted">No recent participants found.</td></tr>'

        company_logo = '/web/binary/company_logo'
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Management - Havano</title>
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
            <h1>Havano Test Management</h1>
            <p>Welcome, {user.name}!</p>
        </div>
        <div class="dashboard-body">
            <div class="stats-row">
                <div class="stat-card"><h3>{total_tests}</h3><p>Total Tests</p></div>
                <div class="stat-card"><h3>{total_completions}</h3><p>Total Completions</p></div>
            </div>
            
            <section>
                <h2>All Tests</h2>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                    {surveys_html}
                </div>
            </section>

            <section>
                <h2 style="margin-bottom:15px;">Recent Participants</h2>
                <table style="width: 100%; border-collapse: separate; border-spacing: 0; background: white; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0;">
                    <thead>
                        <tr style="background: #f8fafc;">
                            <th style="padding: 16px 20px; text-align: left; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px; border-bottom: 1px solid #e2e8f0;">Username</th>
                            <th style="padding: 16px 20px; text-align: left; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px; border-bottom: 1px solid #e2e8f0;">Full Name</th>
                            <th style="padding: 16px 20px; text-align: left; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px; border-bottom: 1px solid #e2e8f0;">Test</th>
                            <th style="padding: 16px 20px; text-align: left; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px; border-bottom: 1px solid #e2e8f0;">Score</th>
                            <th style="padding: 16px 20px; text-align: left; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px; border-bottom: 1px solid #e2e8f0;">Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {participants_html}
                    </tbody>
                </table>
            </section>

            <section style="display: flex; gap: 10px; margin-top: 30px;">
                <a href="/odoo" class="btn" style="width: auto;">Back to Havano</a>
                <a href="/test/my" class="btn" style="width: auto; background: #64748b;">View Student Portal</a>
            </section>
        </div>
    </div>
</body>
</html>'''
        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

    def _get_questions_for_input(self, survey, user_input):
        """Return the deterministic question list for a given user_input."""
        if user_input and user_input.question_ids:
            return user_input.question_ids.sorted(key=lambda q: q.sequence)

        all_questions = request.env['test.question'].sudo().search([
            ('survey_id', '=', survey.id)], order='sequence ASC')
        total_questions = len(all_questions)
        questions_limit = request.env['test.settings'].sudo().get_questions_limit()
        if total_questions > questions_limit:
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

        # Find and cancel/mark as done any existing in-progress attempts to ensure a fresh start
        existing_attempts = request.env['test.user_input'].sudo().search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', partner_id),
            ('state', 'in', ['new', 'in_progress'])
        ])
        if existing_attempts:
            existing_attempts.write({'state': 'done'}) # Mark as done to clear them

        # Always create a fresh attempt for a clean start
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
            'start_datetime': fields.Datetime.now(),
        }
        if registration:
            vals.update({
                'student_fullname': registration.student_fullname,
                'student_username': registration.student_username,
                'student_class': registration.student_class,
            })
        user_input = request.env['test.user_input'].sudo().create(vals)
        questions = self._get_questions_for_input(survey, user_input)
        
        # Calculate session-specific max possible score
        max_possible = 0.0
        for q in questions:
            if q.suggested_answer_ids:
                max_possible += sum(a.answer_score for a in q.suggested_answer_ids if a.answer_score > 0)
            else:
                max_possible += 1.0
        user_input.sudo().write({
            'max_scoring_possible': max_possible,
            'question_ids': [(6, 0, questions.ids)],
        })

        answered_lines = request.env['test.user.input.line'].sudo().search([
            ('user_input_id', '=', user_input.id)])
        answered_question_ids = answered_lines.mapped('question_id').ids

        return request.redirect(f'/test/take/{survey.id}/question/1')

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
            
        # Ensure start_datetime is set
        if not user_input.start_datetime:
            user_input.sudo().write({'start_datetime': datetime.now()})

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
        # Only include lines that have an actual answer
        answered_question_ids = []
        for line in answered_lines:
            is_answered = False
            if line.answer_type == 'simple_choice' and line.value_suggested:
                is_answered = True
            elif line.answer_type == 'multiple_choice' and line.value_suggested_ids:
                is_answered = True
            elif line.answer_type == 'text_box' and line.value_text_box:
                is_answered = True
            elif line.answer_type == 'numerical_box' and line.value_numerical:
                is_answered = True
            
            if is_answered:
                answered_question_ids.append(line.question_id.id)

        settings = request.env['test.settings'].sudo().get_default_settings()
        student_class = user_input.student_class
        passing_score = settings.class4_passing_score or 88
        if student_class == 'class1':
            passing_score = settings.class1_passing_score
        elif student_class == 'class2':
            passing_score = settings.class2_passing_score
        elif student_class == 'class4':
            passing_score = settings.class4_passing_score
        elif student_class == 'class2and4':
            passing_score = settings.class2and4_passing_score

        # Robust timer calculation using Odoo UTC-aware datetime
        now = fields.Datetime.now()
        start = user_input.start_datetime
        # Timer always reads from global Settings — applies to all tests
        limit_mins = settings.default_time_limit or 15
        
        elapsed_seconds = (now - start).total_seconds() if start else 0
        seconds_left = int((limit_mins * 60) - elapsed_seconds)
        
        values = {
            'survey': survey,
            'questions': questions,
            'question': current_question,
            'question_number': q_num,
            'total_questions': len(questions),
            'total_display': len(questions),
            'answers': answers,
            'user_input': user_input,
            'user_line': user_line,
            'answered_question_ids': answered_question_ids,
            'page_name': 'test_take_question',
            'passing_score': passing_score,
            'seconds_left': max(0, seconds_left),
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
        answer_type  = kw.get('answer_type', 'text_box')
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
                    'student_class': registration.student_class,
                })
            user_input = request.env['test.user_input'].sudo().create(vals)
            questions = self._get_questions_for_input(survey, user_input)
            max_possible = 0.0
            for q in questions:
                if q.suggested_answer_ids:
                    max_possible += sum(a.answer_score for a in q.suggested_answer_ids if a.answer_score > 0)
                else:
                    max_possible += 1.0
            user_input.sudo().write({
                'max_scoring_possible': max_possible,
                'question_ids': [(6, 0, questions.ids)],
            })

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

            if answer_type == 'text_box':
                user_line.write({'value_text_box': kw.get('value_text_box', '')})
            elif answer_type == 'simple_choice':
                val = kw.get('value_suggested', 0)
                if val:
                    answer_id = int(val)
                    user_line.write({'value_suggested': answer_id})
                    # Evaluate correctness
                    answer_rec = request.env['test.question.answer'].sudo().browse(answer_id)
                    is_correct = bool(answer_rec.is_correct)
                    score = answer_rec.answer_score if is_correct else 0.0
                    user_line.write({'answer_is_correct': is_correct, 'answer_score': score})
                else:
                    user_line.write({'answer_is_correct': False, 'answer_score': 0.0})
            elif answer_type == 'multiple_choice':
                selected_ids = [int(x) for x in request.httprequest.form.getlist('value_suggested_ids')]
                user_line.write({'value_suggested_ids': [(6, 0, selected_ids)]})
                # Evaluate correctness: all correct answers selected and no wrong ones
                question_rec = request.env['test.question'].sudo().browse(question_id)
                correct_ids = set(question_rec.suggested_answer_ids.filtered(lambda a: a.is_correct).ids)
                selected_set = set(selected_ids)
                is_correct = (correct_ids == selected_set) and bool(correct_ids)
                score = sum(
                    a.answer_score for a in question_rec.suggested_answer_ids
                    if a.id in selected_ids and a.is_correct
                ) if is_correct else 0.0
                user_line.write({'answer_is_correct': is_correct, 'answer_score': score})
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
        
        answered_count = 0
        for line in answered_lines:
            if line.value_suggested or line.value_suggested_ids or line.value_text_box or line.value_numerical:
                answered_count += 1
                
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