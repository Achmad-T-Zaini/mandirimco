// ProductCategoriesWidget
odoo.define('bi_pos_combo.ProductCategoriesWidget', function(require) {
	"use strict";

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	const { useListener } = require('web.custom_hooks');
	const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
	const { useState } = owl.hooks;

	const ProductsWidget = require('point_of_sale.ProductsWidget');

	const ProductCategoriesWidget = (ProductsWidget) =>
		class extends ProductsWidget {
			constructor() {
				super(...arguments);
			}

			_updateSearch(event) {
            	this.state.searchWord = event.detail;
            	// var products;
			// var self = this
			// if(searchWord){
			// 	products = this.pos.db.search_product_in_category(category.id,query);
			// 	if(buy_result && products.length === 1){
			// 		if(products[0].is_pack){
			// 			if(this.pos.config.use_combo){
			// 				var required_products = [];
			// 				var optional_products = [];
			// 				var combo_products = this.pos.pos_product_pack;
			// 				if(products)
			// 				{
			// 					for (var i = 0; i < combo_products.length; i++) {
			// 						if(combo_products[i]['bi_product_product'][0] == products[0].id)
			// 						{
			// 							if(combo_products[i]['is_required'])
			// 							{
			// 								combo_products[i]['product_ids'].forEach(function (prod) {
			// 									var sub_product = self.pos.db.get_product_by_id(prod);
			// 									required_products.push(sub_product)
			// 								});
			// 							}
			// 							else{
			// 								combo_products[i]['product_ids'].forEach(function (prod) {
			// 									var sub_product = self.pos.db.get_product_by_id(prod);
			// 									optional_products.push(sub_product)
			// 								});
			// 							}
			// 						}
			// 					}
			// 				}
			// 				self.gui.show_popup('select_combo_product_widget', {'product': products[0],'required_products':required_products,'optional_products':optional_products , 'update_line' :false });
			// 				this.clear_search();
			// 			}else{
			// 				this.gui.show_popup('error',{
			// 						'title': _t('Error: Could not Added Combo product in orderlines'),
			// 						'body': 'Product is combo, product not available for this session.',
			// 					});
			// 				this.clear_search();
			// 			}
			// 		}else{
			// 				this.pos.get_order().add_product(products[0]);
			// 				this.clear_search();
			// 		}       
			// 	}else{
			// 		this.product_list_widget.set_product_list(products, query);
			// 	}
			// }else{
			// 	products = this.pos.db.get_product_by_category(this.category.id);
			// 	this.product_list_widget.set_product_list(products, query);
			// }
			
        	}
		};

	Registries.Component.extend(ProductsWidget, ProductCategoriesWidget);

	return ProductsWidget;

});
