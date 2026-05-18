# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # Add missing columns if they don't exist
    try:
        cr.execute("ALTER TABLE test_user_input ADD COLUMN IF NOT EXISTS student_fullname VARCHAR;")
        cr.execute("ALTER TABLE test_user_input ADD COLUMN IF NOT EXISTS student_username VARCHAR;")
        cr.execute("ALTER TABLE test_user_input ADD COLUMN IF NOT EXISTS student_id_number VARCHAR;")
    except Exception:
        pass
    
    # Create demo student user if it doesn't exist using Odoo API
    try:
        env = api.Environment(cr, SUPERUSER_ID, {})
        student_user = env['res.users'].with_context(active_test=False).search([('login', '=', 'student')], limit=1)
        
        if not student_user:
            # Create partner
            partner = env['res.partner'].create({
                'name': 'Demo Student',
                'email': 'student@example.com',
                'type': 'contact',
            })
            
            # Create user (Internal User)
            internal_group = env.ref('base.group_user')
            student_user = env['res.users'].create({
                'login': 'student',
                'password': 'student',
                'partner_id': partner.id,
                'group_ids': [(6, 0, [internal_group.id])],
                'active': True,
            })
        else:
            # Ensure it has the internal group even if it already exists
            internal_group = env.ref('base.group_user')
            if internal_group not in student_user.group_ids:
                student_user.write({'group_ids': [(4, internal_group.id)]})
            
            # Ensure it is active
            if not student_user.active:
                student_user.write({'active': True})
    except Exception as e:
        # Log error but don't block migration
        pass
