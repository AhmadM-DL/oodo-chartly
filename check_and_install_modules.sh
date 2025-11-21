#!/bin/bash
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import odoo
from odoo import api, SUPERUSER_ID

# Configure Odoo
odoo.tools.config.parse_config([
    '--db_host=db',
    '--db_user=odoo',
    '--db_password=odoo',
    '--database=odoo'
])

# Get database
db_name = odoo.tools.config['db_name']
registry = odoo.registry(db_name)

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    print("Checking and installing required modules...\n")
    
    # Modules to install
    required_modules = ['account', 'product', 'sale']
    
    for module_name in required_modules:
        module = env['ir.module.module'].search([('name', '=', module_name)])
        
        if module:
            print(f"Module '{module_name}': {module.state}")
            if module.state not in ['installed', 'to upgrade']:
                print(f"  → Installing {module_name}...")
                module.button_immediate_install()
                print(f"  ✅ Installed {module_name}")
            else:
                print(f"  ✅ Already installed")
        else:
            print(f"Module '{module_name}': NOT FOUND")
    
    cr.commit()
    print("\n✅ Module installation complete!")

PYTHON_SCRIPT
