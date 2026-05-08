# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request, route


class TestStudentPortal(http.Controller):
    """Student Portal Controller for Test Module"""

    @route(['/test/my'], type='http', auth='user', website=True)
    def test_my(self, **kw):
        """Student dashboard - shows list of available tests"""
        is_admin = request.env.user.has_group('base.group_system')
        
        # Use sudo() with user 1 to bypass all company restrictions
        if is_admin:
            surveys = request.env['test.survey'].sudo(1).search([('active', '=', True)])
            user_inputs = request.env['test.user_input'].sudo(1).search([
                ('partner_id', '=', request.env.user.partner_id.id)])
            values = {
                'surveys': surveys,
                'user_inputs': user_inputs,
                'page_name': 'test_my',
                'user_name': request.env.user.name,
            }
            return request.render('test.test_student_dashboard', values)
        
        # For portal users, check student details
        user_input = request.env['test.user_input'].sudo(1).search([
            ('partner_id', '=', request.env.user.partner_id.id)], limit=1)

        if not user_input or not (user_input.student_fullname and user_input.student_username and user_input.student_id_number):
            return request.redirect('/test/register')

        surveys = request.env['test.survey'].sudo(1).search([('active', '=', True)])
        user_inputs = request.env['test.user_input'].sudo(1).search([
            ('partner_id', '=', request.env.user.partner_id.id)])

        values = {
            'surveys': surveys,
            'user_inputs': user_inputs,
            'page_name': 'test_my',
            'user_name': request.env.user.name,
        }
        return request.render('test.test_student_dashboard', values)

    @route(['/test/register'], type='http', auth='user', website=True)
    def test_register(self, **kw):
        """Register student details"""
        is_admin = request.env.user.has_group('base.group_system')
        if is_admin:
            return request.redirect('/test/my')
        
        user_input = request.env['test.user_input'].sudo(1).search([
            ('partner_id', '=', request.env.user.partner_id.id)], limit=1)

        error = False
        if request.httprequest.method == 'POST':
            fullname = kw.get('fullname', '').strip()
            username = kw.get('username', '').strip()
            id_number = kw.get('id_number', '').strip()

            if not fullname or not username or not id_number:
                error = 'All fields are required'
            else:
                existing = request.env['test.user_input'].sudo(1).search([
                    ('student_username', '=', username),
                    ('id', '!=', user_input.id if user_input else 0)], limit=1)
                if existing:
                    error = 'Username already exists'
                else:
                    if user_input:
                        user_input.sudo(1).write({
                            'student_fullname': fullname,
                            'student_username': username,
                            'student_id_number': id_number,
                        })
                    else:
                        request.env['test.user_input'].sudo(1).create({
                            'partner_id': request.env.user.partner_id.id,
                            'email': request.env.user.email,
                            'student_fullname': fullname,
                            'student_username': username,
                            'student_id_number': id_number,
                        })
                    return request.redirect('/test/my')

        values = {'error': error, 'page_name': 'test_register'}
        return request.render('test.test_register_page', values)

    @route(['/test/start/<model("test.survey"):survey>'], type='http', auth='user', website=True)
    def test_start(self, survey, **kw):
        return self._start_test_by_survey(survey)

    @route(['/test/start/token/<string:token>'], type='http', auth='user', website=True)
    def test_start_by_token(self, token, **kw):
        survey = request.env['test.survey'].sudo(1).search([('access_token', '=', token)], limit=1)
        if not survey:
            return request.redirect('/test/my')
        return self._start_test_by_survey(survey)

    def _start_test_by_survey(self, survey):
        existing_input = request.env['test.user_input'].sudo(1).search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', request.env.user.partner_id.id),
            ('state', '=', 'new')], limit=1)

        if not existing_input:
            existing_input = request.env['test.user_input'].sudo(1).create({
                'survey_id': survey.id,
                'partner_id': request.env.user.partner_id.id,
                'email': request.env.user.email,
                'access_token': survey.access_token,
            })

        return request.redirect(f'/test/take/{survey.id}')

    @route(['/test/results/<model("test.user_input"):input_id>'], type='http', auth='user', website=True)
    def test_results(self, input_id, **kw):
        values = {'user_input': input_id, 'page_name': 'test_results'}
        return request.render('test.test_results_page', values)

    @route(['/test/take/<model("test.survey"):survey>'], type='http', auth='user', website=True)
    def test_take(self, survey, **kw):
        all_questions = request.env['test.question'].sudo(1).search([
            ('survey_id', '=', survey.id)], order='sequence ASC')

        total_questions = len(all_questions)

        if total_questions > 25:
            import random
            selected_ids = random.sample(list(all_questions.ids), 25)
            questions = request.env['test.question'].sudo(1).browse(selected_ids)
            questions = questions.sorted(key=lambda q: q.sequence)
        else:
            questions = all_questions

        user_input = request.env['test.user_input'].sudo(1).search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', request.env.user.partner_id.id),
            ('state', '=', 'new')], limit=1)

        if not user_input:
            user_input = request.env['test.user_input'].sudo(1).create({
                'survey_id': survey.id,
                'partner_id': request.env.user.partner_id.id,
                'email': request.env.user.email,
                'access_token': survey.access_token,
            })

        answered_lines = request.env['test.user.input.line'].sudo(1).search([
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

    @route(['/test/take/<model("test.survey"):survey>/question/<int:q_num>'], type='http', auth='user', website=True)
    def test_take_question(self, survey, q_num, **kw):
        user_input = request.env['test.user_input'].sudo(1).search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', request.env.user.partner_id.id),
            ('state', '=', 'new')], limit=1)

        if not user_input:
            return request.redirect(f'/test/take/{survey.id}')

        all_questions = request.env['test.question'].sudo(1).search([
            ('survey_id', '=', survey.id)], order='sequence ASC')

        total_questions = len(all_questions)

        if total_questions > 25:
            import random
            random.seed(user_input.id)
            selected_ids = random.sample(list(all_questions.ids), 25)
            questions = request.env['test.question'].sudo(1).browse(selected_ids)
            questions = questions.sorted(key=lambda q: q.sequence)
        else:
            questions = all_questions

        if q_num < 1 or q_num > len(questions):
            return request.redirect(f'/test/take/{survey.id}')

        current_question = questions[q_num - 1]

        answers = request.env['test.question.answer'].sudo(1).search([
            ('question_id', '=', current_question.id)
        ]) if current_question.question_type in ['simple_choice', 'multiple_choice'] else request.env['test.question.answer']

        user_line = request.env['test.user.input.line'].sudo(1).search([
            ('user_input_id', '=', user_input.id),
            ('question_id', '=', current_question.id)], limit=1)

        answered_lines = request.env['test.user.input.line'].sudo(1).search([
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

    @route(['/test/take/<model("test.survey"):survey>/answer'], type='http', auth='user', website=True, methods=['POST'])
    def test_take_answer(self, survey, **kw):
        question_id = int(kw.get('question_id', 0))
        answer_type = kw.get('answer_type', 'free_text')

        user_input = request.env['test.user_input'].sudo(1).search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', request.env.user.partner_id.id),
            ('state', '=', 'new')], limit=1)

        if not user_input:
            return request.redirect(f'/test/take/{survey.id}')

        user_line = request.env['test.user.input.line'].sudo(1).search([
            ('user_input_id', '=', user_input.id),
            ('question_id', '=', question_id)], limit=1)

        if not user_line:
            user_line = request.env['test.user.input.line'].sudo(1).create({
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

    @route(['/test/take/<model("test.survey"):survey>/finish'], type='http', auth='user', website=True)
    def test_take_finish(self, survey, **kw):
        user_input = request.env['test.user_input'].sudo(1).search([
            ('survey_id', '=', survey.id),
            ('partner_id', '=', request.env.user.partner_id.id),
            ('state', '=', 'new')], limit=1)

        if user_input:
            user_input.write({'state': 'done'})

        return request.redirect('/test/my')
