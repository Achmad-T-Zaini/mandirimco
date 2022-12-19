odoo.define('bi_pos_combo.SubmitOrderButton', function(require) {
   'use strict';

   const SubmitOrderButton = require('point_of_sale.SubmitOrderButton');
   const Registries = require('point_of_sale.Registries');
   const { useListener } = require('web.custom_hooks');
   const { useState, useRef } = owl.hooks;
   var config = require('web.config');

   var core = require('web.core');
   var QWeb = core.qweb;
   var _t = core._t;

   const PosOrderWidget = SubmitOrderButton =>
       class extends SubmitOrderButton {
           constructor() {
               super(...arguments);
//               useListener('click', this.onClick);
           }
           async onClick() {
                console.log("***********")
                if (order.hasChangesToPrint()) {
                    const isPrintSuccessful = await order.printChanges();
                    if (isPrintSuccessful) {
                        order.saveChanges();
                    }
                }
           }
       };
   Registries.Component.extend(SubmitOrderButton, PosOrderWidget);

   return SubmitOrderButton;
});
