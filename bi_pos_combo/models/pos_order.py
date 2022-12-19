# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError,Warning
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID
from functools import partial
from itertools import groupby



class ProductPack(models.Model):
	_name = 'product.pack'

	bi_product_template = fields.Many2one(comodel_name='product.template', string='Product pack')
	bi_product_product = fields.Many2one(comodel_name='product.product', string='Product pack',related='bi_product_template.product_variant_id')
	name = fields.Char(related='category_id.name', readonly="1")
	is_required = fields.Boolean('Required')
	category_id = fields.Many2one('pos.category','Category',required=True)
	product_ids = fields.Many2many(comodel_name='product.product', string='Product', required=True,domain="[('pos_categ_id','=', category_id)]")

class pos_config(models.Model):
	_inherit = 'pos.config'
	
	use_combo = fields.Boolean('Use combo in POS')
	combo_pack_price = fields.Selection([('all_product', "Total of all combo items "), ('main_product', "Take Price from the Main product")], string='Total Combo Price', default='all_product')


class ProductProduct(models.Model):
	_inherit = 'product.template'

	is_pack = fields.Boolean(string='Is Combo Product')
	pack_ids = fields.One2many(comodel_name='product.pack', inverse_name='bi_product_template', string='Product pack')


class pos_order_line(models.Model):
	_inherit = 'pos.order.line'

	combo_prod_ids = fields.Many2many("product.product",string="Combo Produts")
	is_pack = fields.Boolean(
		string='Pack',
	)
	
class pos_order(models.Model):
	_inherit = 'pos.order'


	def _get_order_lines(self, orders):
		
		order_lines = self.env['pos.order.line'].search_read(
				domain = [('order_id', 'in', [to['id'] for to in orders])],
				fields = self._get_fields_for_order_line())

		if order_lines != []:
			self._get_pack_lot_lines(order_lines)

		extended_order_lines = []
		for order_line in order_lines:
			order_line['product_id'] = order_line['product_id'][0]
			order_line['server_id'] = order_line['id']

			cstm = self.env['pos.order.line'].browse(order_line['id'])
			if cstm.combo_prod_ids:
				order_line['combo_prod_ids'] = cstm.combo_prod_ids.ids
			if cstm.combo_prod_ids:
				order_line['is_pack'] = cstm.is_pack

			del order_line['id']
			if not 'pack_lot_ids' in order_line:
				order_line['pack_lot_ids'] = []
			extended_order_lines.append([0, 0, order_line])

		for order_id, order_lines in groupby(extended_order_lines, key=lambda x:x[2]['order_id']):
			next(order for order in orders if order['id'] == order_id[0])['lines'] = list(order_lines)


class RelatedPosStock(models.Model):
	_inherit = 'stock.picking'

	def _prepare_stock_move_vals_for_sub_product(self,first_line,item,order_lines):
		return {
			'name': first_line.name,
			'product_uom': item.uom_id.id,
			'picking_id': self.id,
			'picking_type_id': self.picking_type_id.id,
			'product_id': item.id,
			'product_uom_qty': abs(sum(order_lines.mapped('qty'))* 1),
			'state': 'draft',
			'location_id': self.location_id.id,
			'location_dest_id': self.location_dest_id.id,
			'company_id': self.company_id.id,
		}

	
					
	def _create_move_from_pos_order_lines(self, lines):
		self.ensure_one()
		lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id), key=lambda l: l.product_id.id)
		for product, lines in lines_by_product:
			order_lines = self.env['pos.order.line'].concat(*lines)
			first_line = order_lines[0]
			current_move = self.env['stock.move'].create(
				self._prepare_stock_move_vals(first_line, order_lines)
			)

			if first_line.combo_prod_ids:
				for item in first_line.combo_prod_ids - first_line.product_id:
					current_move += current_move.create(
						self._prepare_stock_move_vals_for_sub_product(first_line,item, order_lines)
					)

			confirmed_moves = current_move._action_confirm()
			for move in confirmed_moves:
				if first_line.product_id == move.product_id and first_line.product_id.tracking != 'none':
					if self.picking_type_id.use_existing_lots or self.picking_type_id.use_create_lots:
						for line in order_lines:
							sum_of_lots = 0
							for lot in line.pack_lot_ids.filtered(lambda l: l.lot_name):
								if line.product_id.tracking == 'serial':
									qty = 1
								else:
									qty = abs(line.qty)
								ml_vals = move._prepare_move_line_vals()
								ml_vals.update({'qty_done':qty})
								if self.picking_type_id.use_existing_lots:
									existing_lot = self.env['stock.production.lot'].search([
										('company_id', '=', self.company_id.id),
										('product_id', '=', line.product_id.id),
										('name', '=', lot.lot_name)
									])
									if not existing_lot and self.picking_type_id.use_create_lots:
										existing_lot = self.env['stock.production.lot'].create({
											'company_id': self.company_id.id,
											'product_id': line.product_id.id,
											'name': lot.lot_name,
										})
									quant = existing_lot.quant_ids.filtered(lambda q: q.quantity > 0.0 and q.location_id.parent_path.startswith(move.location_id.parent_path))[-1:]
									ml_vals.update({
										'lot_id': existing_lot.id,
										'location_id': quant.location_id.id or move.location_id.id
									})
								else:
									ml_vals.update({
										'lot_name': lot.lot_name,
									})
								self.env['stock.move.line'].create(ml_vals)
								sum_of_lots += qty
							if abs(line.qty) != sum_of_lots:
								difference_qty = abs(line.qty) - sum_of_lots
								ml_vals = current_move._prepare_move_line_vals()
								if line.product_id.tracking == 'serial':
									ml_vals.update({'qty_done': 1})
									for i in range(int(difference_qty)):
										self.env['stock.move.line'].create(ml_vals)
								else:
									ml_vals.update({'qty_done': difference_qty})
									self.env['stock.move.line'].create(ml_vals)
					else:
						move._action_assign()
						for move_line in move.move_line_ids:
							move_line.qty_done = move_line.product_uom_qty
						if float_compare(move.product_uom_qty, move.quantity_done, precision_rounding=move.product_uom.rounding) > 0:
							remaining_qty = move.product_uom_qty - move.quantity_done
							ml_vals = move._prepare_move_line_vals()
							ml_vals.update({'qty_done':remaining_qty})
							self.env['stock.move.line'].create(ml_vals)

				else:
					if self.user_has_groups('stock.group_tracking_owner'):
						move._action_assign()
						for move_line in move.move_line_ids:
							move_line.qty_done = move_line.product_uom_qty
						if float_compare(move.product_uom_qty, move.quantity_done, precision_rounding=move.product_uom.rounding) > 0:
							remaining_qty = move.product_uom_qty - move.quantity_done
							ml_vals = move._prepare_move_line_vals()
							ml_vals.update({'qty_done':remaining_qty})
							self.env['stock.move.line'].create(ml_vals)
					move.quantity_done = move.product_uom_qty
	
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
