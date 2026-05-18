# controllers/test_api.py
# Comprehensive API for Driving School Test Module
# Odoo 19 Compatible - Using type="http" for all endpoints

import json
import logging
import base64
from datetime import datetime
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import AccessDenied, ValidationError, MissingError

_logger = logging.getLogger(__name__)


class TestApiController(http.Controller):
    """
    API Controller for Driving School Test Module
    Supports both Session and API Key authentication
    """
    
    # ================================================================
    # AUTHENTICATION HELPERS
    # ================================================================
    
    def _get_user_from_api_key(self):
        """Authenticate user via API key header."""
        api_key = (
            request.httprequest.headers.get("X-API-Key") or
            request.httprequest.headers.get("Authorization", "").replace("Bearer ", "").strip()
        )
        
        if not api_key:
            return None
        
        try:
            uid = request.env['res.users.apikeys'].sudo()._check_credentials(
                scope='rpc',
                key=api_key
            )
            
            if uid:
                user = request.env['res.users'].sudo().browse(uid)
                if user and user.active:
                    _logger.info("Test API: API Key Auth - User %s (id=%s)", user.name, user.id)
                    return user
            
            _logger.warning("Test API: Invalid API key attempt")
            return None
            
        except Exception as exc:
            _logger.warning("Test API: API key validation failed: %s", str(exc))
            return None
    
    def _ensure_authenticated(self):
        """Ensure user is authenticated via Session or API Key."""
        # Try API Key first
        user = self._get_user_from_api_key()
        if user:
            request.session.uid = user.id
            request.env = request.env(user=user.id)
            return request.env
        
        # Fall back to session authentication
        if request.session.uid:
            user = request.env['res.users'].browse(request.session.uid)
            if user and user.active:
                _logger.debug("Test API: Session Auth - User %s (id=%s)", user.name, user.id)
                return request.env
        
        raise AccessDenied(_("Unauthorized. Provide X-API-Key header or valid session."))
    
    def _get_json_data(self):
        """Parse JSON data from request body - works with type='http' routes."""
        try:
            raw_data = request.httprequest.get_data(as_text=True)
            _logger.info("Test API: Raw request data: %s", raw_data[:200] if raw_data else "empty")
            
            if raw_data:
                # Try to parse as JSON
                data = json.loads(raw_data)
                # If the request has a 'params' key (JSON-RPC format), extract it
                if isinstance(data, dict) and 'params' in data:
                    return data['params']
                return data
            return {}
        except json.JSONDecodeError as e:
            _logger.error("Test API: JSON decode error: %s", str(e))
            return {}
        except Exception as e:
            _logger.error("Test API: Failed to parse JSON: %s", str(e))
            return {}
    
    def _error_response(self, error, code=400):
        """Standard error response."""
        return {
            "success": False,
            "error": str(error),
            "code": code,
        }
    
    def _success_response(self, data=None, message="", status=200):
        """Standard success response."""
        return {
            "success": True,
            "data": data or {},
            "message": message,
        }
    
    # ================================================================
    # QUESTION SERIALIZATION
    # ================================================================
    
    def _serialize_question(self, question, include_answers=True):
        """Convert test.question to API response dict."""
        result = {
            "id": question.id,
            "question": question.question,
            "question_type": question.question_type,
            "question_type_label": dict(question._fields['question_type'].selection).get(question.question_type, ""),
            "sequence": question.sequence,
            "is_scored": question.is_scored,
            "constr_mandatory": question.constr_mandatory,
            "passing_score": question.passing_score if question.passing_score else 0,
            "has_image": bool(question.question_image),
            "survey_id": question.survey_id.id,
            "survey_title": question.survey_id.title,
        }
        
        if question.question_image:
            result["question_image_url"] = f"/web/image/test.question/{question.id}/question_image"
        
        if include_answers and question.suggested_answer_ids:
            result["answers"] = []
            for answer in question.suggested_answer_ids:
                answer_data = {
                    "id": answer.id,
                    "value": answer.value,
                    "is_correct": answer.is_correct,
                    "answer_score": answer.answer_score,
                    "sequence": answer.sequence,
                    "has_image": bool(answer.answer_image),
                }
                if answer.answer_image:
                    answer_data["answer_image_url"] = f"/web/image/test.question.answer/{answer.id}/answer_image"
                if answer.comment:
                    answer_data["comment"] = answer.comment
                result["answers"].append(answer_data)
        
        return result
    
    def _serialize_answer(self, answer):
        """Convert test.question.answer to API response dict."""
        return {
            "id": answer.id,
            "value": answer.value,
            "is_correct": answer.is_correct,
            "answer_score": answer.answer_score,
            "sequence": answer.sequence,
            "comment": answer.comment or "",
            "has_image": bool(answer.answer_image),
        }
    
    def _serialize_survey(self, survey, include_questions=False):
        """Convert test.survey to API response dict."""
        result = {
            "id": survey.id,
            "title": survey.title,
            "description": survey.description,
            "description_done": survey.description_done,
            "active": survey.active,
            "question_count": survey.question_count,
            "time_limit": survey.time_limit or 0,
        }
        
        if include_questions and survey.question_ids:
            result["questions"] = [self._serialize_question(q, include_answers=True) for q in survey.question_ids]
        
        return result
    
    # ================================================================
    # HEALTH CHECK ENDPOINT
    # ================================================================
    
    @http.route("/api/v1/test/health", auth="public", methods=["GET"], type="http", csrf=False)
    def health_check(self, **kwargs):
        """GET /api/v1/test/health - API health check"""
        return request.make_json_response({
            "success": True,
            "message": "Test API is running",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
        })
    
    # ================================================================
    # SURVEYS ENDPOINTS
    # ================================================================
    
    @http.route("/api/v1/test/surveys", auth="public", methods=["GET"], type="http", csrf=False)
    def list_surveys(self, **kwargs):
        """GET /api/v1/test/surveys - List all surveys/tests"""
        try:
            env = self._ensure_authenticated()
            
            limit = min(int(kwargs.get('limit', 100)), 500)
            offset = int(kwargs.get('offset', 0))
            include_questions = kwargs.get('include_questions', 'false').lower() == 'true'
            
            Survey = env["test.survey"].sudo()
            surveys = Survey.search([("active", "=", True)], limit=limit, offset=offset, order="id desc")
            total = Survey.search_count([("active", "=", True)])
            
            items = [self._serialize_survey(s, include_questions) for s in surveys]
            
            _logger.info("Test API: Listed %s surveys (total: %s)", len(items), total)
            
            return request.make_json_response(self._success_response({
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
            }))
            
        except AccessDenied as e:
            return request.make_json_response(self._error_response(str(e), 401), status=401)
        except Exception as e:
            _logger.exception("Test API: Failed to list surveys - %s", str(e))
            return request.make_json_response(self._error_response(str(e), 500), status=500)
    
    @http.route("/api/v1/test/surveys/<int:survey_id>", auth="public", methods=["GET"], type="http", csrf=False)
    def get_survey(self, survey_id, **kwargs):
        """GET /api/v1/test/surveys/:id - Get survey with questions"""
        try:
            env = self._ensure_authenticated()
            
            Survey = env["test.survey"].sudo()
            survey = Survey.browse(survey_id)
            
            if not survey.exists():
                return request.make_json_response(
                    self._error_response(f"Survey #{survey_id} not found.", 404),
                    status=404
                )
            
            include_questions = kwargs.get('include_questions', 'true').lower() == 'true'
            
            return request.make_json_response(
                self._success_response(self._serialize_survey(survey, include_questions))
            )
            
        except AccessDenied as e:
            return request.make_json_response(self._error_response(str(e), 401), status=401)
        except Exception as e:
            _logger.exception("Test API: Failed to get survey %s - %s", survey_id, str(e))
            return request.make_json_response(self._error_response(str(e), 500), status=500)
    
    # ================================================================
    # QUESTIONS ENDPOINTS
    # ================================================================
    
    @http.route("/api/v1/test/questions", auth="public", methods=["GET"], type="http", csrf=False)
    def list_questions(self, **kwargs):
        """GET /api/v1/test/questions - List all questions"""
        try:
            env = self._ensure_authenticated()
            
            limit = min(int(kwargs.get('limit', 100)), 500)
            offset = int(kwargs.get('offset', 0))
            survey_id = kwargs.get('survey_id')
            include_answers = kwargs.get('include_answers', 'true').lower() == 'true'
            
            domain = []
            if survey_id:
                domain.append(("survey_id", "=", int(survey_id)))
            
            Question = env["test.question"].sudo()
            questions = Question.search(domain, limit=limit, offset=offset, order="survey_id, sequence")
            total = Question.search_count(domain)
            
            items = [self._serialize_question(q, include_answers) for q in questions]
            
            _logger.info("Test API: Listed %s questions (total: %s)", len(items), total)
            
            return request.make_json_response(self._success_response({
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
            }))
            
        except AccessDenied as e:
            return request.make_json_response(self._error_response(str(e), 401), status=401)
        except Exception as e:
            _logger.exception("Test API: Failed to list questions - %s", str(e))
            return request.make_json_response(self._error_response(str(e), 500), status=500)
    
    @http.route("/api/v1/test/questions/<int:question_id>", auth="public", methods=["GET"], type="http", csrf=False)
    def get_question(self, question_id, **kwargs):
        """GET /api/v1/test/questions/:id - Get single question with answers"""
        try:
            env = self._ensure_authenticated()
            
            Question = env["test.question"].sudo()
            question = Question.browse(question_id)
            
            if not question.exists():
                return request.make_json_response(
                    self._error_response(f"Question #{question_id} not found.", 404),
                    status=404
                )
            
            include_answers = kwargs.get('include_answers', 'true').lower() == 'true'
            
            return request.make_json_response(
                self._success_response(self._serialize_question(question, include_answers))
            )
            
        except AccessDenied as e:
            return request.make_json_response(self._error_response(str(e), 401), status=401)
        except Exception as e:
            _logger.exception("Test API: Failed to get question %s - %s", question_id, str(e))
            return request.make_json_response(self._error_response(str(e), 500), status=500)
    
    @http.route("/api/v1/test/questions", auth="public", methods=["POST"], type="http", csrf=False)
    def create_question(self, **kwargs):
        """POST /api/v1/test/questions - Create a new question"""
        try:
            env = self._ensure_authenticated()
            
            # Log the raw request for debugging
            raw_data = request.httprequest.get_data(as_text=True)
            _logger.info("Test API: Create question - Raw data: %s", raw_data[:500] if raw_data else "empty")
            
            # Parse JSON data
            data = self._get_json_data()
            _logger.info("Test API: Parsed data: %s", data)
            
            # Validate required fields
            survey_id = data.get("survey_id")
            question_text = data.get("question")
            question_type = data.get("question_type", "simple_choice")
            
            if not survey_id:
                raise ValidationError(_("survey_id is required."))
            if not question_text:
                raise ValidationError(_("question text is required."))
            
            Survey = env["test.survey"].sudo()
            survey = Survey.browse(int(survey_id))
            if not survey.exists():
                raise ValidationError(_("Survey #%s not found.") % survey_id)
            
            vals = {
                "survey_id": survey.id,
                "question": question_text,
                "question_type": question_type,
                "sequence": data.get("sequence", 10),
                "is_scored": data.get("is_scored", True),
                "constr_mandatory": data.get("constr_mandatory", True),
                "passing_score": data.get("passing_score", 70),
            }
            
            Question = env["test.question"].sudo()
            question = Question.create(vals)
            
            # Create answers
            for answer_data in data.get("answers", []):
                answer_vals = {
                    "question_id": question.id,
                    "value": answer_data.get("value"),
                    "is_correct": answer_data.get("is_correct", False),
                    "answer_score": answer_data.get("answer_score", 0),
                    "sequence": answer_data.get("sequence", 10),
                    "comment": answer_data.get("comment", ""),
                }
                env["test.question.answer"].sudo().create(answer_vals)
            
            _logger.info("Test API: Created question id=%s", question.id)
            
            return request.make_json_response(
                self._success_response(
                    self._serialize_question(question, include_answers=True),
                    message="Question created successfully.",
                    status=201
                ),
                status=201
            )
            
        except AccessDenied as e:
            return request.make_json_response(self._error_response(str(e), 401), status=401)
        except ValidationError as e:
            return request.make_json_response(self._error_response(str(e), 400), status=400)
        except Exception as e:
            _logger.exception("Test API: Failed to create question - %s", str(e))
            return request.make_json_response(self._error_response(str(e), 500), status=500)
    
    @http.route("/api/v1/test/questions/<int:question_id>", auth="public", methods=["PUT"], type="http", csrf=False)
    def update_question(self, question_id, **kwargs):
        """PUT /api/v1/test/questions/:id - Update an existing question"""
        try:
            env = self._ensure_authenticated()
            
            data = self._get_json_data()
            
            Question = env["test.question"].sudo()
            question = Question.browse(question_id)
            
            if not question.exists():
                return request.make_json_response(
                    self._error_response(f"Question #{question_id} not found.", 404),
                    status=404
                )
            
            update_vals = {}
            for field in ['question', 'question_type', 'sequence', 'is_scored', 'constr_mandatory', 'passing_score']:
                if field in data:
                    update_vals[field] = data[field]
            
            if update_vals:
                question.write(update_vals)
            
            _logger.info("Test API: Updated question %s", question_id)
            
            return request.make_json_response(
                self._success_response(
                    self._serialize_question(question, include_answers=True),
                    message="Question updated successfully."
                )
            )
            
        except AccessDenied as e:
            return request.make_json_response(self._error_response(str(e), 401), status=401)
        except Exception as e:
            _logger.exception("Test API: Failed to update question %s - %s", question_id, str(e))
            return request.make_json_response(self._error_response(str(e), 500), status=500)
    
    @http.route("/api/v1/test/questions/<int:question_id>", auth="public", methods=["DELETE"], type="http", csrf=False)
    def delete_question(self, question_id, **kwargs):
        """DELETE /api/v1/test/questions/:id - Delete a question"""
        try:
            env = self._ensure_authenticated()
            
            Question = env["test.question"].sudo()
            question = Question.browse(question_id)
            
            if not question.exists():
                return request.make_json_response(
                    self._error_response(f"Question #{question_id} not found.", 404),
                    status=404
                )
            
            question.unlink()
            
            _logger.info("Test API: Deleted question %s", question_id)
            
            return request.make_json_response(
                self._success_response(
                    {"deleted_id": question_id},
                    message="Question deleted successfully."
                )
            )
            
        except AccessDenied as e:
            return request.make_json_response(self._error_response(str(e), 401), status=401)
        except Exception as e:
            _logger.exception("Test API: Failed to delete question %s - %s", question_id, str(e))
            return request.make_json_response(self._error_response(str(e), 500), status=500)
    
    # ================================================================
    # BATCH OPERATIONS
    # ================================================================
    
    @http.route("/api/v1/test/questions/batch", auth="public", methods=["POST"], type="http", csrf=False)
    def batch_create_questions(self, **kwargs):
        """POST /api/v1/test/questions/batch - Create multiple questions at once"""
        try:
            env = self._ensure_authenticated()
            
            data = self._get_json_data()
            
            survey_id = data.get("survey_id")
            questions_data = data.get("questions", [])
            
            if not survey_id:
                raise ValidationError(_("survey_id is required."))
            if not questions_data:
                raise ValidationError(_("questions array is required."))
            
            Survey = env["test.survey"].sudo()
            survey = Survey.browse(int(survey_id))
            if not survey.exists():
                raise ValidationError(_("Survey #%s not found.") % survey_id)
            
            created_questions = []
            errors = []
            
            for idx, q_data in enumerate(questions_data):
                try:
                    vals = {
                        "survey_id": survey.id,
                        "question": q_data.get("question"),
                        "question_type": q_data.get("question_type", "simple_choice"),
                        "sequence": q_data.get("sequence", (idx + 1) * 10),
                        "is_scored": q_data.get("is_scored", True),
                        "constr_mandatory": q_data.get("constr_mandatory", True),
                        "passing_score": q_data.get("passing_score", 70),
                    }
                    
                    question = env["test.question"].sudo().create(vals)
                    
                    for answer_data in q_data.get("answers", []):
                        env["test.question.answer"].sudo().create({
                            "question_id": question.id,
                            "value": answer_data.get("value"),
                            "is_correct": answer_data.get("is_correct", False),
                            "answer_score": answer_data.get("answer_score", 0),
                            "sequence": answer_data.get("sequence", 10),
                        })
                    
                    created_questions.append({
                        "id": question.id,
                        "question": question.question[:50],
                        "status": "created"
                    })
                    
                except Exception as e:
                    errors.append({
                        "index": idx,
                        "question": q_data.get("question", "Unknown")[:50],
                        "error": str(e)
                    })
            
            _logger.info("Test API: Batch created %s questions", len(created_questions))
            
            return request.make_json_response(
                self._success_response({
                    "created": created_questions,
                    "errors": errors,
                    "total_requested": len(questions_data),
                    "total_created": len(created_questions),
                }, message=f"Created {len(created_questions)} of {len(questions_data)} questions.")
            )
            
        except AccessDenied as e:
            return request.make_json_response(self._error_response(str(e), 401), status=401)
        except Exception as e:
            _logger.exception("Test API: Batch creation failed - %s", str(e))
            return request.make_json_response(self._error_response(str(e), 500), status=500)
    
    # ================================================================
    # ANSWERS ENDPOINTS
    # ================================================================
    
    @http.route("/api/v1/test/answers", auth="public", methods=["GET"], type="http", csrf=False)
    def list_answers(self, **kwargs):
        """GET /api/v1/test/answers - List answers"""
        try:
            env = self._ensure_authenticated()
            
            limit = min(int(kwargs.get('limit', 100)), 500)
            offset = int(kwargs.get('offset', 0))
            question_id = kwargs.get('question_id')
            
            domain = []
            if question_id:
                domain.append(("question_id", "=", int(question_id)))
            
            Answer = env["test.question.answer"].sudo()
            answers = Answer.search(domain, limit=limit, offset=offset, order="question_id, sequence")
            total = Answer.search_count(domain)
            
            items = [self._serialize_answer(a) for a in answers]
            
            return request.make_json_response(
                self._success_response({
                    "items": items,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                })
            )
            
        except AccessDenied as e:
            return request.make_json_response(self._error_response(str(e), 401), status=401)
        except Exception as e:
            _logger.exception("Test API: Failed to list answers - %s", str(e))
            return request.make_json_response(self._error_response(str(e), 500), status=500)