# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # Add missing columns if they don't exist (with error handling for already-existing columns)
    try:
        cr.execute("""
            ALTER TABLE test_user_input 
            ADD COLUMN student_fullname VARCHAR;
        """)
    except Exception:
        pass
    
    try:
        cr.execute("""
            ALTER TABLE test_user_input 
            ADD COLUMN student_username VARCHAR;
        """)
    except Exception:
        pass
    
    try:
        cr.execute("""
            ALTER TABLE test_user_input 
            ADD COLUMN student_id_number VARCHAR;
        """)
    except Exception:
        pass
    
    # Create demo student user if it doesn't exist
    try:
        cr.execute("SELECT id FROM res_users WHERE login = 'student'")
        if not cr.fetchone():
            # Create partner first
            cr.execute("""
                INSERT INTO res_partner (name, email, customer, vendor, create_date, write_date)
                VALUES ('Demo Student', 'student@example.com', false, false, now(), now())
                RETURNING id
            """)
            partner_id = cr.fetchone()[0]
            
            # Create user with user group
            cr.execute("""
                INSERT INTO res_users (login, password, partner_id, create_date, write_date, active)
                VALUES ('student', 'student', %s, now(), now(), true)
                RETURNING id
            """, (partner_id,))
            user_id = cr.fetchone()[0]
            
            # Add user to user group (not portal)
            cr.execute("""
                INSERT INTO res_groups_users_rel (gid, uid)
                SELECT g.id, %s
                FROM res_groups g
                WHERE g.name = 'User' AND g.category_id IN (SELECT id FROM ir_module_category WHERE name = 'User Type')
            """, (user_id,))
    except Exception:
        pass
