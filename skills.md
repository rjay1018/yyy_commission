ODOO 12 CE DEVELOPER PROMPT
With UI/UX & Code Standards Guidelines
Version 12 Community Edition
1. OVERVIEW
This prompt guides development of Odoo 12 Community Edition (CE) modules with emphasis on user interface design, user experience consistency, and maintainable coding practices. Developers should follow these principles for every feature, view, and function implemented.

2. CORE PRINCIPLES
2.1 UI/UX Excellence
Clarity Over Complexity: Every interface element should have a clear purpose. Avoid unnecessary buttons, fields, or visual elements.
Consistency: Use Odoo standard widgets, button styles, and layouts. Maintain visual consistency across all views within your module.
User Feedback: Provide clear feedback for user actions (success notifications, error messages, loading states).
Accessibility: Ensure all form labels are meaningful, buttons are properly sized, and color is not the only indicator of state.

2.2 Code Quality
DRY Principle: Do not repeat code. Extract common logic into helper methods or utility modules.
Readability: Write code that explains itself. Use meaningful variable/method names and avoid cryptic abbreviations.
Modularity: Each function should do one thing well. Keep methods focused and under 30 lines when possible.
Error Handling: Always handle exceptions gracefully with informative error messages.

2.3 Performance
Query Optimization: Use ORM search with proper domains. Avoid N+1 queries with prefetch_related().
Lazy Loading: Load data only when needed. Do not fetch all records if you only need a subset.
Caching: Use Odoo's caching mechanisms (@api.depends_context) for computed fields that don't change frequently.

3. PROJECT STRUCTURE
A well-organized module follows this directory structure:

my_module/   __init__.py                    # Package initializer   __manifest__.py                # Module metadata      models/     __init__.py                  # Model imports     my_model.py                  # Model definitions        views/     my_model_views.xml           # List, Form, Search views     my_model_menuitem.xml        # Menu definitions        controllers/     main.py                      # Web controllers (if needed)        static/     description/       icon.png                   # Module icon        security/     ir_model_access.xml          # Record access rules        data/     my_model_data.xml            # Demo/base data        reports/     my_report.xml                # Report definitions        __openerp__.py or __manifest__.py

4. MODEL DEVELOPMENT STANDARDS
4.1 Class Definition
from odoo import models, fields, api from odoo.exceptions import ValidationError  class MyModel(models.Model):     """     Brief description of the model.          This class manages [business entity] with support for [key features].     """     _name = 'my.module.model'     _description = 'Model Name'     _order = 'name asc'     _sql_constraints = [         ('name_unique', 'UNIQUE(name)', 'Name must be unique'),     ]
Key Points:
Always provide meaningful docstring for the class
Use snake_case for _name (e.g., my.module.model)
Include _description for admin interface clarity
Define _sql_constraints for database integrity

4.2 Field Definitions
# Basic Fields name = fields.Char(     string='Name',     required=True,     help='Enter the unique name' )  description = fields.Text(     string='Description',     help='Provide detailed description' )  status = fields.Selection([     ('draft', 'Draft'),     ('confirmed', 'Confirmed'),     ('done', 'Done'), ], default='draft', string='Status')  # Relational Fields partner_id = fields.Many2one(     'res.partner',     string='Customer',     required=True,     ondelete='cascade' )  line_ids = fields.One2many(     'my.module.line',     'parent_id',     string='Lines' )  # Computed Fields with Caching total_amount = fields.Float(     string='Total',     compute='_compute_total',     store=True  # Store in DB for performance )  @api.depends('line_ids.amount') def _compute_total(self):     for record in self:         record.total_amount = sum(             line.amount for line in record.line_ids         )
Field Guidelines:
Always include string (label) and help text for clarity
Use store=True for computed fields used in filters/searches
Set ondelete='cascade' for dependent records
Define meaningful default values

4.3 Methods & Business Logic
@api.multi def action_confirm(self):     """     Confirm the record and trigger workflow.          Returns: True on success     Raises: ValidationError if preconditions not met     """     for record in self:         if not record.line_ids:             raise ValidationError(                 'Cannot confirm without line items'             )         record.status = 'confirmed'     return True  def _validate_data(self):     """Helper method: Validate data integrity."""     if self.amount <= 0:         raise ValidationError('Amount must be positive')     if self.date_end <= self.date_start:         raise ValidationError(             'End date must be after start date'         )  @api.onchange('partner_id') def _onchange_partner(self):     """Update fields when partner changes (client-side)."""     if self.partner_id:         self.partner_name = self.partner_id.name         self.partner_email = self.partner_id.email  @api.constrains('amount', 'quantity') def _check_amounts(self):     """Validate constraints on model save (server-side)."""     for record in self:         if record.amount < 0:             raise ValidationError(                 'Amount cannot be negative'             )
Method Guidelines:
Use @api.multi for operations on multiple records
Use @api.onchange for real-time field updates (UI)
Use @api.constrains for database-level validation
Always include docstrings explaining purpose and parameters
Keep methods under 30 lines; extract helper methods

5. VIEW DEVELOPMENT
5.1 Form View (UI/UX Best Practices)
<form string="My Model">   <!-- Header Section: Key Info & Actions -->   <header>     <button name="action_confirm" type="object"              string="Confirm" class="oe_highlight"             attrs="{'invisible': [('status', '!=', 'draft')]}"/>     <button name="action_reset" type="object"              string="Reset to Draft"             attrs="{'invisible': [('status', '!=', 'confirmed')]}"/>     <field name="status" widget="statusbar"             options="{'clickable': True}"/>   </header>      <!-- Main Content -->   <sheet>     <!-- Title Section -->     <div class="oe_title">       <h1>         <field name="name" placeholder="Enter name"/>       </h1>     </div>          <!-- Key Information -->     <group name="main" string="Main Information">       <field name="partner_id" required="1"/>       <field name="date_start"/>       <field name="date_end"/>     </group>          <!-- Additional Details -->     <group name="details" string="Additional Details">       <field name="description" nolabel="1"               colspan="2" placeholder="Description..."/>     </group>          <!-- Lines/Items (One2many) -->     <separator string="Items"/>     <field name="line_ids" nolabel="1">       <tree editable="bottom">         <field name="sequence" widget="handle"/>         <field name="product_id"/>         <field name="quantity"/>         <field name="amount" sum="Total"/>       </tree>     </field>          <!-- Summary -->     <group class="oe_subtotal_footer" name="summary">       <field name="total_amount" widget="monetary"/>     </group>   </sheet>      <!-- Notes/Chatter -->   <div class="oe_chatter">     <field name="message_follower_ids" widget="mail_followers"/>     <field name="message_ids" widget="mail_thread"/>   </div> </form>
Form View Guidelines:
Use header for status & action buttons (improves visibility)
Group related fields with <group string="Label"> for clarity
Use attrs="{'invisible': [...]}" to show/hide fields conditionally
Add placeholder text to guide users
Use statusbar widget for workflow visualization
Include chatter for collaboration & audit trail

5.2 List View
<tree string="My Models">   <field name="sequence" widget="handle"/>   <field name="name"/>   <field name="partner_id"/>   <field name="date_start"/>   <field name="total_amount" sum="Total Amount"/>   <field name="status" decoration-danger="status == 'draft'"          decoration-success="status == 'done'"/> </tree>  <!-- Grid View (Kanban) Alternative --> <kanban string="My Models" default_group_by="status">   <field name="status"/>   <templates>     <t t-name="kanban-box">       <div class="oe_kanban_card">         <div class="oe_kanban_content">           <h4><a type="open"><field name="name"/></a></h4>           <p><field name="partner_id"/></p>           <div class="oe_kanban_bottom_right">             <span class="oe_kanban_status">               <field name="status"/>             </span>           </div>         </div>       </div>     </t>   </templates> </kanban>
List View Guidelines:
Include key columns only; avoid crowding
Use decoration-* attributes for visual status indicators
Add sum aggregation for numeric fields
Provide kanban alternative for grouped data

5.3 Search View
<search string="My Model">   <field name="name" string="Name"          filter_domain="[('name', 'ilike', self)]"/>   <field name="partner_id"/>   <filter name="draft" string="Draft"           domain="[('status', '=', 'draft')]"/>   <filter name="confirmed" string="Confirmed"           domain="[('status', '=', 'confirmed')]"/>   <filter name="my_records" string="My Records"           domain="[('user_id', '=', uid)]"/>   <group expand="0" string="Group By">     <filter name="by_status" string="Status"             context="{'group_by': 'status'}"/>     <filter name="by_partner" string="Partner"             context="{'group_by': 'partner_id'}"/>   </group> </search>
Search View Guidelines:
Provide quick filters for common queries
Include grouping options for data analysis
Use clear filter names matching business language

6. CODING STANDARDS
6.1 Python Code Style
# ✓ Good: Clear, descriptive names def calculate_total_invoice_amount(invoice_lines):     """Calculate sum of all line amounts."""     return sum(line.amount for line in invoice_lines)  # ✗ Bad: Cryptic abbreviation def calc_tot(invs):     return sum(i.amt for i in invs)  # ✓ Good: Explicit error handling try:     result = risky_operation() except OperationError as e:     raise ValidationError(         f'Operation failed: {str(e)}'     )  # ✗ Bad: Silent failure result = risky_operation()  # May fail silently  # ✓ Good: Meaningful variable names for line in invoice.line_ids:     line_subtotal = line.quantity * line.unit_price     line.amount = line_subtotal  # ✗ Bad: Unclear variable names for x in inv.y:     z = x.q * x.p     x.a = z
Code Style Rules:
Follow PEP 8 guidelines
Use meaningful variable/function names (>3 characters)
Maximum line length: 120 characters
Use f-strings for string formatting
Always include docstrings for functions and classes

6.2 Common Patterns
# Pattern 1: Safe Dictionary Access values = record.get_values() name = values.get('name', 'Unknown')  # Safe default  # Pattern 2: List Comprehension (Pythonic) active_records = [r for r in records if r.active]  # Pattern 3: Context Manager (Resource Handling) with self.env.cr.savepoint():     # Operations here are atomic     record.write({'status': 'processing'})  # Pattern 4: Decorated Methods @api.multi @api.depends('amount', 'tax') def _compute_total(self):     for record in self:         record.total = record.amount + record.tax  # Pattern 5: Error Handling if not self.line_ids:     raise ValidationError(         'Cannot proceed without items'     )

7. COMMON MISTAKES TO AVOID
Mistake	Impact & Solution
Using global variables instead of model fields	Loss of data persistence. Use ORM fields instead.
N+1 Query Problem	Performance degradation. Use prefetch_related() or batch operations.
Missing error handling	Silent failures. Always wrap risky code in try/except blocks.
Hardcoded IDs/Names	Breaks on different environments. Use __manifest__.py references.
Duplicate code across modules	Maintenance nightmare. Extract to base model or utility module.
Missing documentation	Confusion for other developers. Include clear docstrings.

8. TESTING & DEBUGGING
8.1 Unit Testing
from odoo.tests.common import TransactionCase  class TestMyModel(TransactionCase):     """Test cases for MyModel."""          def setUp(self):         super().setUp()         self.model = self.env['my.module.model']          def test_compute_total(self):         """Test that total_amount computes correctly."""         record = self.model.create({             'name': 'Test',         })         self.assertEqual(record.total_amount, 0)          def test_validation_amount(self):         """Test validation rejects negative amounts."""         with self.assertRaises(ValidationError):             self.model.create({                 'name': 'Test',                 'amount': -10             })

8.2 Debugging Tips
Use logger for debugging instead of print():
from odoo import _logger  _logger.info('Processing record %s', record.id) _logger.warning('Unusual condition detected') _logger.error('Critical error: %s', str(e))
Check logs in Odoo server output or ~/logs/ directory
Use pdb for interactive debugging: import pdb; pdb.set_trace()

9. PERFORMANCE OPTIMIZATION
# ✓ Good: Optimized query with prefetch invoices = self.env['account.invoice'].search(     [('state', '=', 'draft')],     limit=100 ) # Access related data efficiently for inv in invoices:     print(inv.partner_id.name)  # Already prefetched  # ✗ Bad: N+1 Query Problem invoices = self.env['account.invoice'].search([]) for inv in invoices:     # Each loop iteration triggers separate query     partner_name = inv.partner_id.name  # ✓ Good: Batch operations records = [...] records.write({'status': 'done'})  # Single DB update  # ✗ Bad: Loop with individual writes for record in records:     record.write({'status': 'done'})  # Multiple DB updates  # ✓ Good: Store computed values @api.depends('line_ids.amount') def _compute_total(self):     self.total_amount = sum(l.amount for l in self.line_ids) # Add store=True to field definition  # ✗ Bad: Recompute every access @property def total_amount(self):     return sum(l.amount for l in self.line_ids)  # Recalculates each time

10. DOCUMENTATION & COMMENTS
# Good: Clear module docstring in __manifest__.py {     'name': 'Invoice Management',     'version': '12.0.1.0.0',     'summary': 'Manage sales and purchase invoices',     'description': '''         This module extends Odoo's invoicing capabilities with:         - Automated invoice numbering         - Payment reminders         - Tax calculation improvements     ''',     'author': 'Your Company', }  # Good: Function docstring with parameters def process_invoice(self, invoice, options=None):     """     Process an invoice and generate payment records.          Args:         invoice: account.invoice record to process         options (dict): Processing options             - skip_validation (bool): Skip amount validation             - batch_id (int): Associate with batch          Returns:         payment records created              Raises:         ValidationError: If invoice has errors     """     pass  # Good: Inline comments for complex logic # Calculate tax based on regional rules # EU: Include VAT in total if invoice.country_id.is_eu:     total_with_tax = amount * (1 + tax_rate) else:     # Non-EU: Tax applied separately     total_with_tax = amount

11. SECURITY CONSIDERATIONS
11.1 Access Control
<!-- security/ir_model_access.xml --> <?xml version="1.0" encoding="utf-8"?> <odoo>   <data noupdate="1">     <record model="ir.model.access" id="access_my_model_user">       <field name="name">MyModel User Access</field>       <field name="model_id" ref="model_my_module_model"/>       <field name="group_id" ref="base.group_user"/>       <field name="perm_read">1</field>       <field name="perm_write">1</field>       <field name="perm_create">1</field>       <field name="perm_unlink">0</field>  <!-- No delete -->     </record>   </data> </odoo>

11.2 Record Rules
<!-- Limit visibility to user's own records --> <record model="ir.rule" id="my_model_user_rule">   <field name="name">User Own Records</field>   <field name="model_id" ref="model_my_module_model"/>   <field name="groups" eval="[(4, ref('base.group_user'))]"/>   <field name="domain_force">[('user_id', '=', user.id)]</field> </record>

11.3 Secure Coding
Never trust user input - use ORM methods
# ✓ Safe: ORM escapes SQL partner = self.env['res.partner'].search([     ('name', 'ilike', user_input) ])  # ✗ Unsafe: SQL injection risk query = f"SELECT * FROM res_partner WHERE name LIKE '{user_input}'" self.env.cr.execute(query)
Always validate and sanitize inputs
Use ValidationError for user-facing validation

12. MANIFEST FILE TEMPLATE
{     'name': 'Module Display Name',     'version': '12.0.1.0.0',     'category': 'Category Name',     'summary': 'One-line description',     'description': '''         Detailed description of what the module does.         Can span multiple lines.     ''',     'author': 'Your Company',     'license': 'LGPL-3',     'depends': [         'base',         'sale',         'account',     ],     'data': [         # Security         'security/ir_model_access.xml',                  # Views         'views/my_model_views.xml',         'views/my_model_menuitem.xml',                  # Data         'data/my_model_data.xml',     ],     'demo': [         'data/my_model_demo.xml',     ],     'installable': True,     'auto_install': False,     'application': False, }

13. DEVELOPMENT CHECKLIST
☐ All models have proper docstrings
☐ All fields have string labels and help text
☐ Views follow UI/UX guidelines (grouped, labeled, clear)
☐ Error handling with ValidationError messages
☐ Security: Access rules and field-level permissions defined
☐ Code follows PEP 8 style guide
☐ No N+1 queries; optimization done where needed
☐ Unit tests written and passing
☐ Computed fields use @api.depends decorator
☐ Menu items properly defined and accessible
☐ Demo data included in data/
☐ Manifest file complete and correct
☐ Inline comments for complex business logic
☐ No hardcoded IDs; use XML references
☐ No duplicate code; DRY principle followed

14. QUICK REFERENCE
Function	Purpose
@api.multi	Operations on multiple records
@api.one	Operations on single record (deprecated)
@api.onchange	Real-time UI updates when field changes
@api.depends	Declare computed field dependencies
@api.constrains	Server-side validation on save
search()	Find records: search([('field', '=', value)])
create()	Create new record: create({'field': value})
write()	Update records: write({'field': new_value})
unlink()	Delete records: unlink()
mapped()	Extract values: records.mapped('field_name')
filtered()	Filter records: records.filtered(lambda r: r.active)
sorted()	Sort records: records.sorted(key='name')

15. RESOURCES & DOCUMENTATION
Official Odoo Documentation: https://www.odoo.com/documentation/12.0/
ORM API Reference: https://www.odoo.com/documentation/12.0/reference/orm.html
Field Types: https://www.odoo.com/documentation/12.0/reference/addons/orm.html#odoo.fields
View Architecture: https://www.odoo.com/documentation/12.0/reference/addons/views.html
Common ORM Methods: search(), create(), write(), unlink()
