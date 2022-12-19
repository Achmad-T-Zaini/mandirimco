
// BiProductScreen js
odoo.define('bi_pos_combo.BiProductScreen', function(require) {
	"use strict";

	const models = require('point_of_sale.models');
	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');
	const Session = require('web.Session');
	const chrome = require('point_of_sale.Chrome');
	const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
	const NumberBuffer = require('point_of_sale.NumberBuffer');
	const { useListener } = require('web.custom_hooks');
	const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
	const { useState } = owl.hooks;

	const ProductScreen = require('point_of_sale.ProductScreen'); 

	const BiProductScreen = (ProductScreen) =>
		class extends ProductScreen {
			constructor() {
				super(...arguments);
			}
			async _clickProduct(event) {
				var self = this;
				const product = event.detail;
				let order = this.env.pos.get_order();
				if(product.to_weight && this.env.pos.config.iface_electronic_scale){
					this.gui.show_screen('scale',{product: product});
				}else{
					if(product.is_pack){
						var required_products = [];
						var optional_products = [];
						var combo_products = self.env.pos.pos_product_pack;
						if(product)
						{
							for (var i = 0; i < combo_products.length; i++) {
								if(combo_products[i]['bi_product_product'][0] == product['id'])
								{
									if(combo_products[i]['is_required'])
									{
										combo_products[i]['product_ids'].forEach(function (prod) {
											var sub_product = self.env.pos.db.get_product_by_id(prod);
											required_products.push(sub_product)
										});
									}
									else{
										combo_products[i]['product_ids'].forEach(function (prod) {
											var sub_product = self.env.pos.db.get_product_by_id(prod);
											optional_products.push(sub_product)
										});
									}
								}
							}
						}
						self.showPopup('SelectComboProductPopupWidget', {'product': product,'required_products':required_products,'optional_products':optional_products , 'update_line' : false });

					}
					else{
						this.env.pos.get_order().add_product(product);
					}
				}
			}

			_setValue(val){
				let self = this;
				let order = this.currentOrder;
				if(this.currentOrder.get_selected_orderline()){
					if(this.currentOrder.get_selected_orderline().product.is_pack){
						if(this.state.numpadMode==='quantity'){
							var orderline = order.get_selected_orderline()
	                    	orderline.set_quantity(val,'keep_price')

						}else{
							super._setValue(val)
						}
					}	
					else{
						super._setValue(val)
					}
				}
				
			}
		};

	Registries.Component.extend(ProductScreen, BiProductScreen);

	return ProductScreen;

});
