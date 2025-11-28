"""
Post-init hook to process demo invoices after module installation.
This posts draft invoices and registers payments on some of them.
"""
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Post-init hook called after module installation.
    Posts demo invoices and registers payments on ~30% of them.
    """
    # Only run if demo data is being loaded
    if not env.context.get('demo', True):
        _logger.info("Chartly: Skipping invoice processing (demo mode not enabled)")
        return
    
    _logger.info("Chartly: Starting post-init hook to process demo invoices...")
    
    # Find all draft invoices created by our demo data
    # We identify them by the demo partner references
    demo_partner_refs = [
        'chartly.demo_partner_azure',
        'chartly.demo_partner_greenleaf', 
        'chartly.demo_partner_techstart',
        'chartly.demo_partner_metro',
        'chartly.demo_partner_sunrise'
    ]
    
    demo_partners = env['res.partner']
    for ref in demo_partner_refs:
        try:
            partner = env.ref(ref, raise_if_not_found=False)
            if partner:
                demo_partners |= partner
        except Exception:
            pass
    
    if not demo_partners:
        _logger.warning("Chartly: No demo partners found, skipping invoice processing")
        return
    
    # Find all draft invoices for demo partners
    draft_invoices = env['account.move'].search([
        ('partner_id', 'in', demo_partners.ids),
        ('state', '=', 'draft'),
        ('move_type', 'in', ['out_invoice', 'in_invoice', 'out_refund', 'in_refund'])
    ])
    
    _logger.info(f"Chartly: Found {len(draft_invoices)} draft invoices to post")
    
    if not draft_invoices:
        return
    
    # Post all invoices
    try:
        draft_invoices.action_post()
        _logger.info(f"Chartly: Successfully posted {len(draft_invoices)} invoices")
    except Exception as e:
        _logger.error(f"Chartly: Error posting invoices: {e}")
        return
    
    # Now register payments on approximately 30% of customer invoices
    customer_invoices = draft_invoices.filtered(lambda inv: inv.move_type == 'out_invoice')
    
    # Select ~30% to mark as paid (every 3rd invoice roughly)
    invoices_to_pay = customer_invoices[::3]  # Every 3rd invoice
    
    _logger.info(f"Chartly: Registering payments for {len(invoices_to_pay)} invoices")
    
    # Get the default payment journal (bank)
    bank_journal = env['account.journal'].search([('type', '=', 'bank')], limit=1)
    if not bank_journal:
        bank_journal = env['account.journal'].search([('type', '=', 'cash')], limit=1)
    
    if not bank_journal:
        _logger.warning("Chartly: No bank/cash journal found, skipping payment registration")
        return
    
    for invoice in invoices_to_pay:
        try:
            # Create a payment for this invoice
            payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'amount': invoice.amount_residual,
                'currency_id': invoice.currency_id.id,
                'journal_id': bank_journal.id,
                'payment_method_line_id': bank_journal.inbound_payment_method_line_ids[0].id if bank_journal.inbound_payment_method_line_ids else False,
            }
            
            payment = env['account.payment'].create(payment_vals)
            payment.action_post()
            
            # Reconcile the payment with the invoice
            receivable_line = invoice.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
            )
            payment_line = payment.move_id.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
            )
            
            if receivable_line and payment_line:
                (receivable_line + payment_line).reconcile()
                _logger.debug(f"Chartly: Paid invoice {invoice.name}")
                
        except Exception as e:
            _logger.warning(f"Chartly: Could not register payment for invoice {invoice.id}: {e}")
            continue
    
    _logger.info("Chartly: Post-init hook completed successfully")
