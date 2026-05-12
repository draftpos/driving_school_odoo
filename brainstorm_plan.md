# Comprehensive Plan: Correct Errors in portal.py (test app)

## Information Gathered:
- **File**: `addons/test/controllers/portal.py` (~450 lines)
- **Model**: `test_user_input` in `addons/test/models/test_user_input.py`
- **Model**: `test_question` in `addons/test/models/test_question.py`
- **Model**: `test_settings` in `addons/test/models/test_settings.py`
- **Model**: `test_survey` in `addons/test/models/test_survey.py`

### Errors Identified:

1. **Indentation Error** - Line ~290 in `test_take` method:
   ```python
   user_input = request.env['test.user_input'].sudo().search([...])  # Wrongly dedented
   ```
   This should be inside the `if not partner_id:` block but at the same level.

2. **Indentation Error** - Line ~340 in `test_take_question` method:
   Similar indentation issue.

3. **Imports in middle of code** - Lines ~284, ~357:
   ```python
   import random  # Inside method instead of at top
   ```
   Should be moved to top of file.

4. **Question Type Mismatch**:
   - Portal uses `answer_type='free_text'` but TestQuestion uses `question_type='text_box'`
   - Portal uses `'numerical_box'` but TestQuestion model doesn't define this type

## Plan:
1. **Move import statement to top** of portal.py
2. **Fix indentation** in `test_take` method (~line 290)
3. **Fix indentation** in `test_take_question` method (~line 340)
4. **Update question type** references:
   - Change `'free_text'` to `'text_box'` in appropriate places
   - The model's question_type already supports the types needed

## Dependent Files to Edit:
- Only `addons/test/controllers/portal.py` needs editing

## Followup Steps:
1. Verify file loads correctly (no syntax errors)
2. The changes are backward compatible with existing data
