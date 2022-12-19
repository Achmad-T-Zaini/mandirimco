odoo.define('bi_pos_combo.ClientScreenExtend', function(require) {
	"use strict";

	const Registries = require('point_of_sale.Registries');
	const ClientScreen = require('point_of_sale.ClientListScreen'); 
	const NumberBuffer = require('point_of_sale.NumberBuffer');
	const { Gui } = require('point_of_sale.Gui');


	const deleteOrderline = (ClientScreen) =>
		class extends ClientScreen {
			constructor() {
				super(...arguments);
			}

			async clickNext() {

	            var orderlines = this.env.pos.get_order() ? this.env.pos.get_order().get_orderlines() : [];
	            const{Confirmed} = false;
	            if(this.env.pos.config.combo_pack_price== 'all_product' && orderlines.length > 0){
	                for (var line in orderlines)
	                {
	                    if(orderlines[line] && orderlines[line].product && orderlines[line].product.is_pack){
	                        const { confirmed } = await Gui.showPopup('ConfirmPopup', {
	                            title: this.env._t('Warning'),
	                            body: this.env._t('If you change customer then the price of the combo product will be changed.'),
	                        });

	                        if(confirmed){
					            this.state.selectedClient = this.nextButton.command === 'set' ? this.state.selectedClient : null;
					            this.confirm();
					            return
				            }
					        else{
					        	this.trigger('close-temp-screen');
					        	return
					        }

	                    }
	                }
	                
	            }
	            this.state.selectedClient = this.nextButton.command === 'set' ? this.state.selectedClient : null;
				this.confirm();

	        }
		};

	Registries.Component.extend(ClientScreen, deleteOrderline);

	return ClientScreen;

});