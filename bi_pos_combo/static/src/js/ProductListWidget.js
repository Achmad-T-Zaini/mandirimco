// BiProductScreen js
odoo.define('bi_pos_combo.ProductListWidget', function(require) {
	"use strict";

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	const { useListener } = require('web.custom_hooks');
	const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
	const { useState } = owl.hooks;

	const ProductsWidget = require('point_of_sale.ProductsWidget');

	const ProductListWidget = (ProductsWidget) =>
		class extends ProductsWidget {
			constructor() {
				super(...arguments);
			}

			get productsToDisplay() {
				let self = this;
				let prods = super.productsToDisplay;
				let use_combo = self.env.pos.config.use_combo;
				if (this.searchWord !== '') {
	                let products =  this.env.pos.db.search_product_in_category(
	                    this.selectedCategoryId,
	                    this.searchWord
	                );
	                var product_list = []
		                for (let product in products){
		                	if(products[product].is_pack == true){
		                		if(use_combo){
		                			product_list.push(products[product])
		                		}

		                	}else{
		                		product_list.push(products[product])
		                	}

		                }
		               	return product_list
	            } else {
	               	let products =  this.env.pos.db.get_product_by_category(this.selectedCategoryId);
	            	
	                var product_list = []
		                for (let product in products){
		                	if(products[product].is_pack == true){
		                		if(use_combo){
		                			product_list.push(products[product])
		                		}

		                	}else{
		                		product_list.push(products[product])
		                	}

		                }
		               	return product_list
	            }
				
			}
		};

	Registries.Component.extend(ProductsWidget, ProductListWidget);

	return ProductsWidget;

});
