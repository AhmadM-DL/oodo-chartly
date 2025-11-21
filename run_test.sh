#!/bin/bash
cd /mnt/extra-addons/chartly/controllers
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

# Execute the test
exec(open('test_execute_query_real.py').read())
PYTHON_SCRIPT
