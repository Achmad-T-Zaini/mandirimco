odoo.define('bi_pos_combo.OrderWidgetExtended', function(require){
	'use strict';

	const OrderWidget = require('point_of_sale.Orderline');
	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	const { Component } = owl;

	const OrderWidgetExtended = (OrderWidget) =>
		class extends OrderWidget {
			constructor() {
				super(...arguments);
			}

			get addedClasses() {	
	            return {
	                selected: this.props.line.selected,
	            	};
        	}


        	on_click(){
	            var product = this.props.line.product
				var required_products = [];
				var optional_products = [];
				var combo_products = product.pos.pos_product_pack;

	            if(product){
					for (var i = 0; i < combo_products.length; i++) {
						if(combo_products[i]['bi_product_product'][0] == product['id'])
						{
							if(combo_products[i]['is_required'])
							{
								combo_products[i]['product_ids'].forEach(function (prod) {
									var sub_product = product.pos.db.get_product_by_id(prod);
									required_products.push(sub_product)
								});
							}
							else{
								combo_products[i]['product_ids'].forEach(function (prod) {
									var sub_product = product.pos.db.get_product_by_id(prod);
									optional_products.push(sub_product)
								});
							}
						}
					}
				}
				this.showPopup('SelectComboProductPopupWidget', {'product': product,'required_products':required_products,'optional_products':optional_products , 'update_line' : true });
        	}


        	selectLine() {
            this.trigger('select-line', { orderline: this.props.line });
	        }

	        lotIconClicked() {
	            this.trigger('edit-pack-lot-lines', { orderline: this.props.line });
	        }

	};

	Registries.Component.extend(OrderWidget, OrderWidgetExtended);

	return OrderWidget;

});
