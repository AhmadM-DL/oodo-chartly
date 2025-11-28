"""
Demo utilities model - provides methods callable from demo XML data.
"""
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class ChartlyDemoUtils(models.AbstractModel):
    _name = 'chartly.demo.utils'
    _description = 'Chartly Demo Utilities'

    @api.model
    def post_demo_invoices(self):
        """
        Post all demo invoices and register payments on ~30% of them.
        Called from demo XML via: <function model="chartly.demo.utils" name="post_demo_invoices"/>
        """
        _logger.info("Chartly: Starting to post demo invoices...")
        
        # Find demo partners by their XML IDs
        demo_partner_refs = [
            'chartly.partner_adobe',
            'chartly.partner_wework',
            'chartly.partner_tesla',
            'chartly.partner_grainger',
            'chartly.partner_consultant',
        ]
        
        demo_partners = self.env['res.partner']
        for ref in demo_partner_refs:
            try:
                partner = self.env.ref(ref, raise_if_not_found=False)
                if partner:
                    demo_partners |= partner
            except Exception:
                pass
        
        if not demo_partners:
            _logger.warning("Chartly: No demo partners found")
            return True
        
        _logger.info(f"Chartly: Found {len(demo_partners)} demo partners")
        
        # Find all draft invoices for these partners
        draft_moves = self.env['account.move'].search([
            ('partner_id', 'in', demo_partners.ids),
            ('state', '=', 'draft'),
            ('move_type', 'in', ['out_invoice', 'in_invoice', 'out_refund', 'in_refund'])
        ])
        
        _logger.info(f"Chartly: Found {len(draft_moves)} draft moves to post")
        
        if not draft_moves:
            return True
        
        # Post all moves
        posted_count = 0
        for move in draft_moves:
            try:
                move.action_post()
                posted_count += 1
            except Exception as e:
                _logger.warning(f"Chartly: Could not post move {move.id}: {e}")
        
        _logger.info(f"Chartly: Successfully posted {posted_count} moves")
        
        # Now register payments on ~30% of CUSTOMER invoices only
        customer_invoices = self.env['account.move'].search([
            ('partner_id', 'in', demo_partners.ids),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
            ('payment_state', '=', 'not_paid'),
        ])
        
        # Pay every 3rd invoice (~33%)
        invoices_to_pay = list(customer_invoices)[::3]
        _logger.info(f"Chartly: Will register payments for {len(invoices_to_pay)} of {len(customer_invoices)} customer invoices")
        
        # Find a bank journal
        bank_journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
        if not bank_journal:
            bank_journal = self.env['account.journal'].search([('type', '=', 'cash')], limit=1)
        
        if not bank_journal:
            _logger.warning("Chartly: No bank/cash journal found, skipping payments")
            return True
        
        paid_count = 0
        for invoice in invoices_to_pay:
            try:
                # Use the payment register wizard
                payment_register = self.env['account.payment.register'].with_context(
                    active_model='account.move',
                    active_ids=invoice.ids,
                ).create({
                    'journal_id': bank_journal.id,
                })
                payment_register.action_create_payments()
                paid_count += 1
            except Exception as e:
                _logger.warning(f"Chartly: Could not pay invoice {invoice.name}: {e}")
        
        _logger.info(f"Chartly: Successfully paid {paid_count} invoices")
        _logger.info("Chartly: Demo invoice processing complete!")
        return True
