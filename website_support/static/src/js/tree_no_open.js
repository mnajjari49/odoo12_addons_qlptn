odoo.define('website_support.tree_no_open', function (require) {"use strict";
	debugger;
	var core = require('web.core');
	var List = require('web.ListRenderer');
	List.include({
		_onRowClicked:function(e){if(!this.el.classList.contains('tree_no_open')){this._super.apply(this,arguments);}}
		});
});



