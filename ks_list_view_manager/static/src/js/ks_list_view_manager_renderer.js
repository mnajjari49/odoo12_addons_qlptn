odoo.define('ks_list_view_manager.renderer', function (require) {

"use strict";

var core = require('web.core');
var _t = core._t;
var ListRenderer = require('web.ListRenderer');
var config = require('web.config');
var pyUtils = require('web.py_utils');
var ks_session = require('web.session');
var AbstractView = require('web.AbstractView');
var QWeb = core.qweb;
var BasicController = require('web.BasicController');
var datepicker = require("web.datepicker");
var fieldUtils = require('web.field_utils');
var ks_basic_view = require('web.BasicView');

    ListRenderer.include({

        events: _.extend({}, ListRenderer.prototype.events, {
            "keyup .custom-control-searchbar-advance" : "ks_advance_searchbar",
            "change .custom-control-searchbar-change" : "ks_change_event",
            "click .ks_remove_popup" : "ks_remove_popup_domain",
            'hide.datetimepicker' : function(event){

                if($(event.target).hasClass("ks_btn_middle_child")){
                    if(event.date._i) {
                        this.trigger_up("Ks_update_advance_search_renderer",{
                            ksFieldName:    event.target.parentElement.dataset.ksField,
                            KsSearchId:     event.target.parentElement.id,
                            ksfieldtype:    event.target.parentElement.dataset.fieldType,
                            ksFieldIdentity:event.target.parentElement.dataset.fieldIdentity,
                            ks_val:          event.date.toISOString()
                        });

                        if(!(event.target.parentElement.id.indexOf("_lvm_end_date") > 0)) {
                            $($('#'+event.target.parentElement.id).parent()).parent().addClass("ks_date_inner");
                            $($('#'+event.target.parentElement.id).parent().parent().children()[1]).addClass("ks_date_inner");
                            $($($(event.target).parents()[3]).children()[1]).removeClass("d-none");
                            $($($($(event.target).parents()[3]).children()[1]).children()[0]).removeClass("d-none");
                            $($($(event.target).parents()[3]).children()[1]).addClass("ks_date_inner");
                        }
                    }
                }
            }
        }),

        init: function (parent, state, params) {
            var self = this;

            self.restoreInVisibility = [];
            self.restoreName = [];
            self.restoreColumnsDescription = [];
            self.ks_duplicate_data = [];
            self.ks_call_flag=1;
            self.ks_datepicker_flag=0;
            self._super.apply(this,arguments);
            self.ks_user_table_result = null;
            self.ks_list_view_data = null;
            self.ks_field_domain_dict={}
            self.ks_key_fields=[]
            self.ks_field_domain_list=[]
            self.ksDomain=null;
            self.ksBaseDomain=null
            self.ks_allow_search = true;
            self.ksbaseFlag=false;
            self.ks_trigger_up_flag=false;
            self.ks_focus_flag = false;
            self.ks_blur_flag  = true;
            self.ks_restore_data = false;
            self.is_ks_editable_on = false;
            self.ks_autocomplete_data = {};
            self.ks_autocomplete_data_result = {}
            self.ks_refreshed = false;
            self.ks_previous_columns_length;
            self.ks_is_resizer = false;
            self.is_ks_sort_column = false;
            self.ks_styles = [];
        },

        willStart: function () {
            core.bus.on('click', this, this._onWindowClicked.bind(this));
            this.ks_count = 0;
            this.ks_mode_count=0;
            var self = this;
            var def1 = this._super.apply(this, arguments);
            var def2;
            var def3 = self._rpc({
                    model: 'user.mode',
                    method: 'check_user_mode',
                    args: [self.state.model,odoo.session_info.uid,self.ksViewID],
                }).then(function(ks_list_view_data){
                    self.userMode = ks_list_view_data['list_view_data'];
                    self.ks_list_view_data = ks_list_view_data;
                    self.ks_settingMode();
                }.bind(self));

            if(ks_session.ks_list_view_field_mode === "model_all_fields" || ks_session.ks_list_view_field_mode === false) {
                def2 = self._rpc({
                    model: 'user.specific',
                    method: 'check_user_exists',
                    args: [self.state.model,odoo.session_info.uid,self.ksViewID],
                }).then(function(ks_user_table_result){
                     self.ks_user_table_result = ks_user_table_result;
                     if(self.ks_user_table_result) {
                        self._processColumns({});
                    }

                }.bind(self));
            } else {
                 def2 = self._rpc({
                    model: 'ks.user.standard.specific',
                    method: 'check_user_exists',
                    args: [self.state.model,odoo.session_info.uid,self.ksViewID],
                }).then(function(ks_user_table_result){
                     self.ks_user_table_result = ks_user_table_result;
                     if(self.ks_user_table_result) {
                        self._processColumns({});
                    }

                }.bind(self));
            }

            return $.when(def1,def2,def3);
        },

        _processColumns: function (columnInvisibleFields){
            var self = this;
            var ks_load_data = [];
            var ks_name;
            var ks_fields;
            var ks_description;
            self.handleField = null;
            if(self.restoreInVisibility.length === 0) {
                for(var i = 0; i<self.arch.children["length"]; i++) {
                    if(self.arch.children[i].tag === 'field') {
                        ks_name = self.arch.children[i].attrs.name;
                        ks_fields = self.state.fields[ks_name];
                        if (self.arch.children[i].attrs.widget) {
                                ks_description = self.state.fieldsInfo.list[ks_name].Widget.prototype.description;
                            }
                        if(ks_fields) {
                            if (ks_description === undefined) {
                                ks_description = self.arch.children[i].attrs.string || ks_fields.string;
                            }
                        }

                        if (!self.arch.children[i].attrs.hasOwnProperty('ks_old_data_stored')){
                            self.arch.children[i].attrs['ks_prev_string'] = ks_description;
                            self.arch.children[i].attrs['ks_prev_name'] = self.arch.children[i].attrs.name;
                            self.arch.children[i].attrs['ks_prev_invisible'] = self.arch.children[i].attrs.invisible;
                            self.arch.children[i].attrs['ks_sort_position'] = i;
                            self.arch.children[i].attrs['ks_old_data_stored'] = true;
                        }


                        self.restoreName.push(self.arch.children[i].attrs.name);
                        ks_description=undefined
                        if(self.arch.children[i].attrs.invisible === "1")
                            self.restoreInVisibility.push(false);
                        else
                            self.restoreInVisibility.push(true);

                    }
                }
            }


            if(self.ks_list_view_data !== null && self.ks_list_view_data !== undefined && self.ks_user_table_result && self.ks_user_table_result.length !== 0 && Object.keys(self.ks_user_table_result[0])[1] !== "ks_table_width" && self.ks_list_view_data.ks_dynamic_list_show === true && self.ks_user_table_result && self.ks_count == 0) {
                ks_load_data = this.arch.children.slice(0);
                if(self.arch.children.length === self.ks_user_table_result["length"]-1) {
                    for(var i = 0; i < this.ks_user_table_result["length"]; i++) {
                    for(var j = 0;j < this.ks_user_table_result["length"]; j++) {
                        if(ks_load_data[j]) {
                            if(ks_load_data[j].attrs.name === this.ks_user_table_result[i].field_name) {
                                this.arch.children[i] = ks_load_data[j];

                                if(!this.ks_user_table_result[i].ksShowField) {
                                    this.arch.children[i].attrs.modifiers.column_invisible = true;
                                    this.arch.children[i].attrs.invisible = "1";
                                } else {
                                    this.arch.children[i].attrs.modifiers.column_invisible = false;
                                    this.arch.children[i].attrs.invisible = "0";
                                }
                                this.arch.children[i].attrs["string"] =  this.ks_user_table_result[i].ks_columns_name;
                            }
                        }
                    }
                }
                    this.ks_count++;
                }
            }
            return  this._super.apply(this,arguments);
        },

        _onRowClicked: function(event) {
            if(!window.getSelection().toString() || this._isEditable()) {
                this._super.apply(this, arguments);
            }
        },

        on_attach_callback: function () {
            var self = this;
            if($(".modal").length === 0) {
                if(self.ks_list_view_data.ks_can_edit === true) {
                   if(self.ks_mode_count === 0) {
                      if(self.userMode.length === 1) {
                         if(self.userMode[0].editable === "top") {
                              $('#mode').prop('checked', true);
                               self.is_ks_editable_on = true;
                               self.editable = "top";
                               self.getParent().editable="top";
                         }
                         else {
                             $('#mode').prop('checked', false);
                             self.is_ks_editable_on = false;
                             self.getParent().editable = false;
                         }
                      }
                      if(self.editable === 'top' || self.editable === 'bottom') {
                             $('#mode').prop('checked',true);
                              self.is_ks_editable_on = true;
                      }
                     self.ks_mode_count++;
                   }
                } else {
                     $('.mode_button').hide();
                }
                if(self.ks_list_view_data.ks_dynamic_list_show === false) {
                      $('.toggle_button').hide();
                }
            }else{
                if(self.is_ks_editable_on){
                    self.editable = ''
                }
            }

            if(this.ks_list_view_data.ks_dynamic_list_show === false) {
                     $('.toggle_button').hide();
            }
            var ks_header_children = $(self.$el.find("thead tr.bg-primary")).children();

            //setting header color
            if(this.$el.parents().find(".o_modal_header").length === 0) {
                if(ks_session.ks_header_color) {
                    if(!(this.getParent().$el.hasClass("o_field_one2many")|| this.getParent().$el.hasClass("o_field_many2many"))) {
                        for (var i = 0; i < ks_header_children.length; i++) {
                            ks_header_children[i].style.setProperty("background-color",ks_session.ks_header_color,"important");
                        }
                        var ks_header_search_children = self.$el.find(".ks_advance_search_row")

                        for(var i = 0; i < ks_header_search_children.length; i++) {
                            ks_header_search_children[i].style.setProperty("background-color","#EEEEEE","important");
                        }
                    }
                }
                self.ks_set_width_according_to_result();
            } else {
                $(this.$el.find("thead tr.bg-primary")).removeClass("bg-primary");
                for(var i =0; i < this.$el.find("thead th.bg-primary").length; i++) {
                    $($(this.$el.find("thead th.bg-primary"))[i]).css("background-color","")
                }
            }
        },

        ks_settingMode: function() {
            if(this.ks_list_view_data.ks_can_edit === true) {
                if(this.userMode.length === 1) {
                    if(this.userMode[0].editable === "top") {
                        this.editable = "top";
                        this.getParent().mode = "edit";
                    } else {
                        this.editable = false;
                        this.getParent().mode = "readonly"
                    }
                }
            }
        },

        _getNumberOfCols: function () {
            var ks_columns = this._super();
            ks_columns +=1;

            return ks_columns;
        },

        ks_fetch_autocomplete_data: function (field,type,value,ks_one2many_relation) {
            var self = this;

            return self._rpc({
                model: 'user.mode',
                method: 'ks_get_autocomplete_values',
                args: [self.state.model,field,type,value,ks_one2many_relation],
            })
        },

        _renderHeader: function (isGrouped) {
            var self = this;
            var $ks_header = self._super(isGrouped);
            self.ks_allow_search = true;
            self.ks_field_popup = {};
            if(self.ksDomain!=null) {
                for(var i=0; i < self.ksDomain.length; i++) {
                    if(!(self.ksDomain[i] === '|')) {
                        if(self.ks_field_popup[self.ksDomain[i][0]] === undefined) {
                            self.ks_field_popup[self.ksDomain[i][0]]=[self.ksDomain[i][2]]
                        } else {
                            self.ks_field_popup[self.ksDomain[i][0]].push(self.ksDomain[i][2])
                        }
                    }
                }
            }
            if(!(this.getParent().$el.hasClass("o_field_one2many")|| this.getParent().$el.hasClass("o_field_many2many")))
                if(this.$el.parents().find(".o_modal_header").length === 0) {
                    for(var ks_colour = 0 ; ks_colour < $ks_header[0].children[0].children.length; ks_colour++) {
                        $($ks_header[0].children[0].children[ks_colour]).addClass("bg-primary")
                    }
                }


            self.ks_call_flag=1;
            if(ks_session.ks_serial_number) {
                var $th = $('<th>').css("width","1");
                $th.addClass("bg-primary")
            }

            if (self.mode !== 'edit') {
                if(ks_session.ks_serial_number) {
                    if(!(this.getParent().$el.hasClass("o_field_one2many")|| this.getParent().$el.hasClass("o_field_many2many")))
                        if(this.$el.parents().find(".o_modal_header").length === 0) {
                            $ks_header.find("tr").prepend($th.html('S.No'));
                        }
                }

                if(!(this.getParent().$el.hasClass("o_field_one2many")|| this.getParent().$el.hasClass("o_field_many2many")))
                    if(this.$el.parents().find(".o_modal_header").length === 0) {
                        $ks_header.find("tr").addClass("bg-primary");
                    }
            }

            if(self.ks_list_view_data.ks_can_advanced_search === true && self.$el.parents(".o_field_one2many").length === 0 ) {
                var $tr = $('<tr>')
                .append(_.map(self.columns, self.ks_textBox.bind(self)));

                if (self.hasSelectors) {
                    $tr.prepend($('<th>'));
                }
                $tr.addClass('hide-on-modal')

                if(ks_session.ks_serial_number) {
                    $tr.prepend($('<th>'));
                }
            }

            self.ks_field_popup = {}
            return $ks_header.append($tr);

        },

        ks_textBox: function(node) {
            var self = this;
            if(node.tag==="field") {
                if(this.state.fields[node.attrs.name].store === true && !(this.state.fields[node.attrs.name].type === "one2many" || this.state.fields[node.attrs.name].type === "many2many")) {
                    var ks_name = node.attrs.name;
                    var ks_fields = this.state.fields[ks_name];
                    var ks_selection_values = []
                    var ks_description;
                    var ks_field_type;
                    var $ks_from;
                    var ks_field_identity;
                    var ks_identity_flag=false;
                    var ks_field_id=ks_name;
                    var ks_is_hide = true;
                    var ks_widget_flag = true;

                    if (node.attrs.widget) {
                        ks_description = this.state.fieldsInfo.list[ks_name].Widget.prototype.description;
                    }
                    if(ks_fields) {
                        ks_field_type = this.state.fields[ks_name].type;

                        if(ks_field_type === "selection") {
                            ks_selection_values = this.state.fields[ks_name].selection;
                        }
                        if (ks_description === undefined) {
                            ks_description = node.attrs.string || ks_fields.string;
                        }
                    }

                    var $th = $('<th>').addClass("ks_advance_search_row ");
                    if(ks_field_type === "date" || ks_field_type === "datetime"){
                        if(this.ks_call_flag>1){
                            $th.addClass("ks_fix_width")

                        }
                    }
                    if(ks_field_type === "date" || ks_field_type === "datetime"){
                         if(!(this.ks_call_flag>1)) {
                               this.ks_call_flag += 1;
                               $ks_from = this.ks_textBox(node);
                               ks_identity_flag = true
                        }
                        if(this.ks_call_flag == 2 && ks_identity_flag == false) {
                               ks_field_id = ks_name+"_lvm_end_date"
                               ks_field_identity = ks_field_id+" lvm_end_date"
                        } else {
                               ks_field_id = ks_name+"_lvm_start_date"
                               ks_field_identity = ks_field_id+" lvm_start_date"
                        }
                    }

                    var $input =$(QWeb.render("ks_list_view_advance_search", {
                        ks_id : ks_field_id,
                        ks_description : ks_description,
                        ks_type:ks_field_type,
                        ks_field_identifier : ks_field_identity,
                        ks_selection: ks_selection_values
                    }));

                    if((ks_field_type==="date" || ks_field_type==="datetime" ) && (this.ks_call_flag==2 && ks_identity_flag==false)) {
                        if(this.state.domain.length === 0){
                            $input.addClass("d-none")
                            $th.addClass("ks_date_inner")

                        }
                        if(!(this.state.domain.length === 0 )) {
                            if(Object.values(this.ks_field_popup)!== undefined){
                                for(var ks_hide = 0; ks_hide < Object.keys(this.ks_field_popup).length; ks_hide++) {
                                    if((Object.keys(this.ks_field_popup)[ks_hide] === ks_name)){
                                            ks_is_hide=false
                                            break
                                    }
                                }
                                if(ks_is_hide===true) {
                                    $input.addClass("d-none");
                                    $th.addClass("d-none");
                                } else{
                                    $th.addClass("ks_date_inner");
                                }

                            }
                        }
                    }

                    if(this.ksDomain!=null && this.ksDomain.length) {
                        if(this.ksDomain[this.ksDomain.length-1]===this.state.domain[this.state.domain.length-1]) {
                            if(ks_field_type === "date" || ks_field_type === "datetime") {
                                for(var ks_add_span=0;ks_add_span<Object.keys(this.ks_field_popup).length;ks_add_span++) {
                                    if(Object.keys(this.ks_field_popup)[ks_add_span]===ks_name) {
                                        for(var ks_add_span_inner=0;ks_add_span_inner<Object.values(this.ks_field_popup)[ks_add_span].length-1;ks_add_span_inner++) {

                                            var $div = $('<div>').addClass("ks_inner_search")
                                            $div.attr('id',ks_name+'_value'+ks_add_span_inner)

                                            var $span = $('<span>');

                                            if(ks_field_type === "datetime") {
                                              $span = $span.addClass("ks_date_chip_ellipsis");
                                            }

                                            $span.attr('id',ks_name+'_ks_span'+ks_add_span_inner)

                                            var $i = $('<i>').addClass("fa fa-times")
                                            $i.addClass('ks_remove_popup');

                                            if(this.ks_call_flag == 2 && ks_identity_flag==false) {
                                                $span.text(Object.values(this.ks_field_popup)[ks_add_span][1]);
                                                $span.attr('title',Object.values(this.ks_field_popup)[ks_add_span][1]);
                                                $($input.find(".d-flex")[1]).prepend($div);
                                                $input.find("#"+Object.keys(this.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($i);
                                                $input.find("#"+Object.keys(this.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($span)
                                            } else {
                                                $input.addClass("ks_date_inner")
                                                $span.text(Object.values(this.ks_field_popup)[ks_add_span][0]);
                                                $span.attr('title',Object.values(this.ks_field_popup)[ks_add_span][0]);
                                                $($input.find(".d-flex")[1]).prepend($div);
                                                $input.find("#"+Object.keys(this.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($i);
                                                $input.find("#"+Object.keys(this.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($span)
                                            }
                                            $input.find('input').removeAttr('placeholder');
                                        }
                                    }
                                }
                            }
                            else if(ks_field_type === "selection") {
                                for(var ks_add_span = 0; ks_add_span < Object.keys(this.ks_field_popup).length; ks_add_span++) {
                                    if(Object.keys(this.ks_field_popup)[ks_add_span] === ks_name) {
                                        for(var ks_add_span_inner = 0; ks_add_span_inner < Object.values(this.ks_field_popup)[ks_add_span].length; ks_add_span_inner++) {
                                            var value;
                                            var $div = $('<div>').addClass("ks_inner_search")
                                            $div.attr('id',ks_name+'_value'+ks_add_span_inner)

                                            var $span = $('<span>').addClass("ks_advance_chip");
                                            $span.attr('id',ks_name+'_ks_span'+ks_add_span_inner)
                                            $span.addClass("ks_advance_chip_ellipsis");

                                            var $i = $('<i>').addClass("fa fa-times")
                                            $i.addClass('ks_remove_popup');

                                            for(var sel=0; sel < ks_selection_values.length; sel++) {
                                                if(ks_selection_values[sel][0] === Object.values(this.ks_field_popup)[ks_add_span][ks_add_span_inner]) {
                                                    value = ks_selection_values[sel][1];
                                                }
                                            }

                                            $span.text(value);
                                            $span.attr("title",value);
                                            $($input.find(".d-flex")[1]).prepend($div);
                                            $input.find("#"+Object.keys(this.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($i);
                                            $input.find("#"+Object.keys(this.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($span)
                                        }
                                    }
                                }
                            } else {
                                   for(var ks_add_span=0; ks_add_span < Object.keys(this.ks_field_popup).length; ks_add_span++) {
                                        if(Object.keys(this.ks_field_popup)[ks_add_span] === ks_name) {
                                            for(var ks_add_span_inner=0;ks_add_span_inner<Object.values(this.ks_field_popup)[ks_add_span].length;ks_add_span_inner++) {

                                                var $div = $('<div>').addClass("ks_inner_search")
                                                $div.attr('id',ks_name+'_value'+ks_add_span_inner)

                                                var $span = $('<span>').addClass("ks_advance_chip");

                                                if(!(ks_field_type === "date" || ks_field_type === "datetime")) {
                                                    $span.addClass("ks_advance_chip_ellipsis");
                                                }


                                                $span.attr('id',ks_name+'_ks_span'+ks_add_span_inner)
                                                var $i = $('<i>').addClass("fa fa-times")

                                                $i.addClass('ks_remove_popup');
                                                if(ks_field_type === 'monetary' || ks_field_type === 'integer' || ks_field_type === 'float') {
                                                    var currency = this.getSession().get_currency(this.ks_list_view_data.currency_id);
                                                    var formatted_value = fieldUtils.format.float(Object.values(this.ks_field_popup)[ks_add_span][ks_add_span_inner] || 0, {digits: currency && currency.digits});
                                                    $span.text(formatted_value);
                                                    $span.attr("title",formatted_value);

                                                } else {
                                                    $span.text(Object.values(this.ks_field_popup)[ks_add_span][ks_add_span_inner]);
                                                    $span.attr("title",Object.values(this.ks_field_popup)[ks_add_span][ks_add_span_inner]);
                                                }
                                                 if(!(ks_field_type === 'many2one'|| ks_field_type === 'many2many' || ks_field_type === 'one2many'))
                                                    $input.find('input').removeAttr('placeholder');

                                                    $($input.find(".d-flex")[1]).prepend($div);
                                                    $input.find("#"+Object.keys(this.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($i);
                                                    $input.find("#"+Object.keys(this.ks_field_popup)[ks_add_span]+"_value"+ks_add_span_inner).prepend($span)
                                            }
                                        }
                                   }
                            }
                        }
                    }

                    if(this.ksDomain!=null && this.ksDomain.length) {
                          if(!(this.ksDomain[this.ksDomain.length-1]===this.state.domain[this.state.domain.length-1])) {
                                delete this.ks_field_domain_dict
                                delete this.ksDomain
                                this.ksBaseDomain = []
                                this.ks_field_domain_dict = {}
                                this.ks_key_fields.splice(0,this.ks_key_fields.length)
                                this.ks_field_domain_list.splice(0,this.ks_field_domain_list.length)
                          }
                      }

                    if(ks_field_type === "date" || ks_field_type === "datetime") {
                        for(var i = 0; i < this.state.domain.length; i++) {
                            if(ks_field_identity.split("_lvm_end_date")[0] === this.state.domain[i][0] || ks_field_identity.split("_lvm_start_date")[0] === this.state.domain[i][0]){
                                ks_widget_flag = false
                                break;
                            }
                        }
                    }

                    if(ks_widget_flag && ks_field_type==="date") {
                        this["ksStartDatePickerWidget" + ks_field_identity] = new (datepicker.DateWidget)(this);
                        this["ksStartDatePickerWidget" + ks_field_identity].appendTo($input.find('.custom-control-searchbar-change')).then((function () {
                            this["ksStartDatePickerWidget" + ks_field_identity].$el.addClass("ks_btn_middle_child o_input");
                            this["ksStartDatePickerWidget" + ks_field_identity].$el.find("input").attr("placeholder", "Search");
                        }).bind(this));
                    }

                    if(ks_widget_flag && ks_field_type==="datetime") {
                        this["ksStartDateTimePickerWidget" + ks_field_identity] = new (datepicker.DateTimeWidget)(this);
                        this["ksStartDateTimePickerWidget" + ks_field_identity].appendTo($input.find('.custom-control-searchbar-change')).then((function () {
                            this["ksStartDateTimePickerWidget" + ks_field_identity].$el.addClass("ks_btn_middle_child o_input");
                            this["ksStartDateTimePickerWidget" + ks_field_identity].$el.find("input").attr("placeholder", "Search");
                        }).bind(this));
                    }
                        if(this.ksDomain!=null && this.ksDomain.length) {
                            if(this.ksDomain.length === this.state.domain.length) {
                                for(var i = 0; i <this.state.domain.length; i++) {
                                    if(!(this.state.domain[i] === this.ksDomain[i])) {
                                        this.ksbaseFlag = true
                                    }
                                }
                            }
                            if(this.ksbaseFlag === true) {
                                this.ksBaseDomain = this.state.domain
                                this.ksbaseFlag=false
                            }
                        }
                        if((this.ksDomain === null || this.ksDomain ===undefined || this.ksDomain.length === 0) && this.state.domain.length) {
                            this.ksBaseDomain = this.state.domain
                        }
                        if((this.ksDomain === null || this.ksDomain === undefined || this.ksDomain.length === 0) && this.state.domain.length === 0) {
                            this.ksBaseDomain = this.state.domain
                        }

                        $th.append($input);
                        if(this.ks_call_flag == 2) {
                            $th.append($ks_from);
                            this.ks_datepicker_flag+=1;
                        }
                        if(this.ks_datepicker_flag == 2) {
                            this.ks_call_flag = 1;
                            this.ks_datepicker_flag = 0;
                        }
                    }
                else {
                      var $th = $('<th>').addClass("ks_advance_search_row ");
                }
                return $th;
            }
        },

        _renderView: function () {
            var self = this;
            if(self.ks_list_view_data.ks_can_advanced_search === true && self.$el.parents(".o_field_one2many").length === 0) {
                self.noContentHelp = ''
            }
            self.ks_styles = [];
            self.$el.find('thead th').each(function () {
               self.ks_styles.push($(this).attr('style'));
            });

            var ks_result = self._super.apply(self, arguments);
            self.ks_restore_data = false;
            return ks_result;
        },

        _renderFooter: function (isGrouped) {
            var $ks_footer = this._super(isGrouped);
            if(ks_session.ks_serial_number) {
                if(!(this.getParent().$el.hasClass("o_field_one2many")|| this.getParent().$el.hasClass("o_field_many2many")))
                        if(this.$el.parents().find(".o_modal_header").length === 0) {
                            $ks_footer.find("tr").prepend($('<td>'));
                        }
            }
            return $ks_footer;
        },
        _renderGroupRow: function (group, groupLevel) {
           var $ks_row =  this._super(group, groupLevel);

           if (this.mode !== 'edit' || this.hasSelectors) {
                if(ks_session.ks_serial_number) {
                    $ks_row.find("th.o_group_name").after($('<td>'));
                }
                $ks_row.find("th.o_group_name").after($('<td>'));
           }

           return $ks_row;
        },

        _renderGroups: function (data, groupLevel) {

            var self = this;
            var _self = this;
            var result = [];

            groupLevel = groupLevel || 0;

            var $tbody = $('<tbody>');
            _.each(data, function (group) {
                 if (!$tbody) {
                    $tbody = $('<tbody>');
                 }
                 $tbody.append(self._renderGroupRow(group, groupLevel));
                 if (group.data.length) {
                    result.push($tbody);

                    // render an opened group
                    if (group.groupedBy.length) {
                        // the opened group contains subgroups
                        result = result.concat(self._renderGroups(group.data, groupLevel + 1));
                    } else{
                        // the opened group contains records
                        var $ks_records = _.map(group.data, function (ks_record,index) {
                        //the opened group contains records
                            if (_self.mode !== 'edit' || _self.hasSelectors) {
                                if(ks_session.ks_serial_number) {
                                    if(!(self.getParent().$el.hasClass("o_field_one2many") || self.getParent().$el.hasClass("o_field_many2many")))
                                        return self._renderRow(ks_record).prepend($('<th>').html(index+1));
                                } else {
                                    return self._renderRow(ks_record);
                                }
                            } else {
                                return self._renderRow(ks_record);
                            }

                        });
                        result.push($('<tbody>').append($ks_records));
                    }
                    $tbody = null;
                 }
            });
            if ($tbody) {
                result.push($tbody);
            }

            return result;
        },

        _renderRow: function (record) {
            var $ks_row = this._super(record);

            if(ks_session.ks_serial_number) {
                if (this.mode !== 'edit' && this.state.groupedBy.length === 0) {

                    var ks_index = this.state.data.findIndex(function(event) {
                        return record.id === event.id
                    })

                    if (ks_index !== -1) {
                        if(!(this.getParent().$el.hasClass("o_field_one2many")|| this.getParent().$el.hasClass("o_field_many2many")))
                            if(this.$el.parents().find(".o_modal_header").length === 0) {
                                $ks_row.prepend($('<th>').html(ks_index+1));
                            }
                    }
                }
            }
            return $ks_row;
        },

        _renderBodyCell: function (record, node, colIndex, options) {
            var ks_td_cell = this._super.apply(this, arguments);
            return ks_td_cell.addClass("ks_word_break");
        },

        _onSelectRecord: function (event) {
            this._super.apply(this, arguments);
            var checkbox = $(event.currentTarget).find('input');
            var $selectedRow = $(checkbox).closest('tr')

            if($(checkbox).prop('checked')) {
                $selectedRow.addClass('ks_highlight_row');
            }
            else {
                $selectedRow.removeClass('ks_highlight_row')
            }
        },

        _onToggleSelection: function (event) {

           this._super.apply(this, arguments);
           var ks_is_checked = $(event.currentTarget).prop('checked') || false;
           if(ks_is_checked) {
                this.$('tbody .o_list_record_selector').closest('tr').addClass('ks_highlight_row')
           } else {
                this.$('tbody .o_list_record_selector').closest('tr').removeClass('ks_highlight_row')
           }
        },

        ks_advance_searchbar: function(e) {
            // block of code for Autocomplete
            var self = this;
            var ks_field_type = e.currentTarget.dataset.fieldType;
            var ks_one2many_relation;

            if((!(e.keyCode == 8 || e.keyCode ==13)) && $(e.currentTarget).val().length) {

                if(ks_field_type === "one2many") {
                    ks_one2many_relation = self.state.fields[e.currentTarget.id].relation
                }


                self.ks_fetch_autocomplete_data(e.currentTarget.id,ks_field_type,$(e.currentTarget).val(),ks_one2many_relation)
                .then(function(ks_auto_Data){

                    self.ks_autocomplete_data_result = ks_auto_Data

                    if(!(ks_field_type === "date" || ks_field_type === "datetime" || ks_field_type === "selection")) {
                        var ks_unique_data = {}
                        self.ks_autocomplete_data[e.currentTarget.id] = [];

                        if(ks_field_type === 'one2many') {
                            for(var i = 0; i < self.ks_autocomplete_data_result.length; i++) {

                                if(!(ks_unique_data[self.ks_autocomplete_data_result[i]])){
                                    self.ks_autocomplete_data[e.currentTarget.id].push(String(self.ks_autocomplete_data_result[i]));
                                    ks_unique_data[self.ks_autocomplete_data_result[i]] = true;
                                }
                            }
                        } else if(ks_field_type === 'many2many' || ks_field_type === 'many2one'){
                            for(var i = 0; i < self.ks_autocomplete_data_result.length; i++) {

                                if(!(ks_unique_data[self.ks_autocomplete_data_result[i][e.currentTarget.id][1]])){
                                    self.ks_autocomplete_data[e.currentTarget.id].push(String(self.ks_autocomplete_data_result[i][e.currentTarget.id][1]));
                                    ks_unique_data[self.ks_autocomplete_data_result[i][e.currentTarget.id][1]] = true;
                                }
                            }
                        } else {
                            for(var i = 0; i < self.ks_autocomplete_data_result.length; i++) {

                                if(!(ks_unique_data[self.ks_autocomplete_data_result[i][e.currentTarget.id]])){
                                    self.ks_autocomplete_data[e.currentTarget.id].push(String(self.ks_autocomplete_data_result[i][e.currentTarget.id]));
                                    ks_unique_data[self.ks_autocomplete_data_result[i][e.currentTarget.id]] = true;
                                }
                            }
                        }


                        $("#"+e.currentTarget.id).autocomplete({
                            source: self.ks_autocomplete_data[e.currentTarget.id]
                        });
                    }
                });
            }
            if(e.keyCode == 8 && this.ks_allow_search) {
                if(event.target.parentNode.children.length!==1) {
                    this.trigger_up("ks_remove_domain",{"event":e})
                    this.ks_allow_search = false;
                }
            }
            if(e.keyCode == 13 && this.ks_allow_search) {
                this.trigger_up("Ks_update_advance_search_renderer",{ksFieldName: e.currentTarget.dataset.ksField,KsSearchId:e.currentTarget.id,ksfieldtype:e.currentTarget.dataset.fieldType});
                this.ks_allow_search = false;
            }
        },

        ks_change_event: function(e) {
            if(e.currentTarget.dataset.fieldType !== "datetime" && e.currentTarget.dataset.fieldType !== 'date') {
                this.trigger_up("Ks_update_advance_search_renderer",{ksFieldName: e.currentTarget.dataset.ksField,KsSearchId:e.currentTarget.id,ksfieldtype:e.currentTarget.dataset.fieldType,ksFieldIdentity:e.currentTarget.dataset.fieldIdentity});
            }
        },

        ks_remove_popup_domain:function(e) {
            var self = this;
            var div = e.currentTarget.closest('.ks_inner_search')
            self.trigger_up("ks_remove_domain",{ksDiv: div,ksfieldtype:$($(e.target).parents()[2]).children()[$($(e.target).parents()[2]).children().length - 1].dataset.fieldType,});
            var i;
            if(e.currentTarget.parentElement.parentElement!==null) {
                if($($(e.currentTarget).parents()[2]).children()[1].id.indexOf("_lvm_start_date")>0) {
                    $(e.currentTarget.parentElement.parentElement.children[1]).addClass("d-none");
                    $(e.currentTarget.parentElement.parentElement.children[1].parentElement.parentElement.children[1].children[0]).addClass("d-none");
                }
                else {
                    $($(e.currentTarget).parents()[3]).addClass("d-none");
                }
                var field = (e.currentTarget.parentElement.id).split("_value")
                delete self.ks_field_popup[field[0]];
            }
        },

        _onWindowClicked: function (event) {
            this._super.apply(this, arguments);
            var self = this

            function sticky(){
                self.$el.find("table.o_list_view").each(function () {
                        $(this).stickyTableHeaders({scrollableArea:  $(".o_content")[0], fixedOffset: 0.1});
                   });
               }

            function fix_body(position){
                 $("body").css({
                   'position': position,
                });
            }

            if(this.$el){
                if(this.$el.parents('.o_field_one2many').length===0){
                        sticky();
                        fix_body("fixed");
                        $(window).unbind('resize', sticky).bind('resize', sticky);
                        this.$el.css("overflow-x","visible");
                }else{
                    fix_body("relative");
                }
            }
            var self = this
            $("div[class='o_sub_menu']").css("z-index",4);

            var self = this

            if(event.target.className === "ks_hide_show_checkbox") {
                if(typeof self.getParent().ks_update_columns === 'function'){
                            self.getParent().ks_update_columns();
                }
            }
            if(event.target.className === "ks_editable") {
                var $field_span_el = $('span.ks_editable[data-field-id='+event.target.dataset.fieldId+']');
                var $field_input_el = $('input.ks_editable[data-field-id='+event.target.dataset.fieldId+']');
                var name = $field_span_el.text().trim();
                $field_input_el.val(name);
                $field_span_el.hide();
                $field_input_el.removeClass("d-none");
                $field_input_el.focus();
                $(".cancel_button").removeClass("d-none");
            }
        },

        _onSortColumn: function (event) {
            var self = this;
            if ($(event.target).is('.resizer')) {
                if(typeof self.getParent().ks_update_columns === 'function') {
                    self.getParent().ks_update_width_method();
                    self.getParent().ks_update_width_along_data();
                    self.ks_is_resizer = true;
                    self.is_ks_sort_column = false;
                    return;
                }
            }

            self.is_ks_sort_column = true;
            self._super.apply(self, arguments);

        },

        // setting size of columns
        ks_set_width_according_to_result: function() {
            var self = this;
            if(self.ks_user_table_result && self.ks_user_table_result.length !== 0  && Object.keys(self.ks_user_table_result[0])[1] !=="ks_table_width"  && self.ks_user_table_result[self.ks_user_table_result.length-1].ks_table_width > 0){
                if($('.table').offset()) {
                    var ks_fields_name = [];
                    var ks_serial_no_iter = 0;
                    var ks_header_length = self.$el.find("thead .bg-primary th").length/2;
                    if(self.ks_user_table_result && self.ks_user_table_result.length !== 0  && Object.keys(self.ks_user_table_result[0])[1] !=="ks_table_width"  && self.ks_user_table_result[self.ks_user_table_result.length-1].ks_table_width > 0) {
                        self.$el.find("table").innerWidth((self.ks_user_table_result[self.ks_user_table_result.length-1].ks_table_width/100) * $(window).width());
                    }

                    for(var i = 2; i <= ks_header_length; i++) {
                        ks_fields_name.push(self.$el.find("thead .bg-primary th")[i - ks_serial_no_iter].innerText);
                        ks_fields_name[i-2] = ks_fields_name[i-2].trim();
                    }

                    var ks_fields_length = ks_fields_name.length;
                    if(ks_session.ks_serial_number === "True")
                        ks_fields_length = ks_fields_length - 1;

                    var ks_table_percent = self.ks_user_table_result[self.ks_user_table_result.length-1].ks_table_width;
                    var ks_table_pixel = (ks_table_percent/100) * $(window).width();
                    for(var i = 0 ; i < ks_fields_length; i++) {
                        for(var j = 0; j < self.ks_user_table_result.length - 1;j++){
                            if(ks_fields_name[i] === self.ks_user_table_result[j]["ks_columns_name"]) {
                                self.$el.find("thead .bg-primary th")[i-ks_serial_no_iter+2].style.setProperty("position","relative")
                                if(Number(self.ks_user_table_result[j]["ks_width"])) {
                                    var ks_dif = self.$el.find("thead .bg-primary th").length/2;
                                    var ks_dup_row_dif = ks_dif - (i-ks_serial_no_iter+2);
                                    var ks_dup_row_index = ((i-ks_serial_no_iter+2)*2) + ks_dup_row_dif;
                                    self.$el.find("thead .bg-primary th")[i-ks_serial_no_iter+2].style.setProperty("width",String((self.ks_user_table_result[j]["ks_width"]/100) * ks_table_pixel)+"px");
                                    if(self.$el.find("thead .bg-primary th")[ks_dup_row_index])
                                        self.$el.find("thead .bg-primary th")[ks_dup_row_index].style.setProperty("width",String((self.ks_user_table_result[j]["ks_width"]/100) * ks_table_pixel)+"px");
                                    break;
                                }
                            }
                        }
                    }
                }

                for(var i = 0; i < $(".ks_advance_search_row").length; i++) {
                    if(self.$el.find(".ks_advance_search_row")[i]){
                        self.$el.find(".ks_advance_search_row")[i].style.setProperty("width","")
                    }
                }

                if(typeof self.getParent().ks_update_columns === 'function') {
                    self.getParent().ks_update_width_method();
                    self.getParent().ks_update_width_along_data();
                }


                if(self.ks_one_2many){
                    self.ks_one_2many = false;
                }
            }
        },
    });

    ks_basic_view.include({

        _processField: function (viewType, field, attrs) {
            var self = this;
            attrs.Widget = this._getFieldWidgetClass(viewType, field, attrs);

            // process decoration attributes
            _.each(attrs, function (value, key) {
                var splitKey = key.split('-');
                if (splitKey[0] === 'decoration') {
                    attrs.decorations = attrs.decorations || [];
                    attrs.decorations.push({
                        className: 'text-' + splitKey[1],
                        expression: pyUtils._getPyJSAST(value),
                    });
                }
            });

            if (!_.isObject(attrs.options)) { // parent arch could have already been processed (TODO this should not happen)
                attrs.options = attrs.options ? pyUtils.py_eval(attrs.options) : {};
            }

            if (attrs.on_change && attrs.on_change !== "0" && !field.onChange) {
                field.onChange = "1";
            }

            // the relational data of invisible relational fields should not be
            // fetched (e.g. name_gets of invisible many2ones), at least those that
            // are always invisible.
            // the invisible attribute of a field is supposed to be static ("1" in
            // general), but not totally as it may use keys of the context
            // ("context.get('some_key')"). It is evaluated server-side, and the
            // result is put inside the modifiers as a value of the '(column_)invisible'
            // key, and the raw value is left in the invisible attribute (it is used
            // in debug mode for informational purposes).
            // this should change, for instance the server might set the evaluated
            // value in invisible, which could then be seen as static by the client,
            // and add another key in debug mode containing the raw value.
            // for now, we look inside the modifiers and consider the value only if
            // it is static (=== true),
            if (attrs.modifiers.invisible === true || attrs.modifiers.column_invisible === true) {
                attrs.__no_fetch = true;
            }

            if (!_.isEmpty(field.views)) {
                // process the inner fields_view as well to find the fields they use.
                // register those fields' description directly on the view.
                // for those inner views, the list of all fields isn't necessary, so
                // basically the field_names will be the keys of the fields obj.
                // don't use _ to iterate on fields in case there is a 'length' field,
                // as _ doesn't behave correctly when there is a length key in the object
                attrs.views = {};
                var ks_field_type = field.type;
                _.each(field.views, function (innerFieldsView, viewType) {
                    viewType = viewType === 'tree' ? 'list' : viewType;
                    innerFieldsView.ks_inner_view_type = ks_field_type;
                    attrs.views[viewType] = self._processFieldsView(innerFieldsView, viewType);
                });
            }

            if (field.type === 'one2many' || field.type === 'many2many') {
                if (attrs.Widget.prototype.useSubview) {
                    if (!attrs.views) {
                        attrs.views = {};
                    }
                    var mode = attrs.mode;
                    if (!mode) {
                        if (attrs.views.tree && attrs.views.kanban) {
                            mode = 'tree';
                        } else if (!attrs.views.tree && attrs.views.kanban) {
                            mode = 'kanban';
                        } else {
                            mode = 'tree,kanban';
                        }
                    }
                    if (mode.indexOf(',') !== -1) {
                        mode = config.device.isMobile ? 'kanban' : 'tree';
                    }
                    if (mode === 'tree') {
                        mode = 'list';
                        if (!attrs.views.list && attrs.views.tree) {
                            attrs.views.list = attrs.views.tree;
                        }
                    }
                    attrs.mode = mode;
                    if (mode in attrs.views) {
                        var view = attrs.views[mode];
                        this._processSubViewAttrs(view, attrs);
                    }
                }
                if (attrs.Widget.prototype.fieldsToFetch) {
                    attrs.viewType = 'default';
                    attrs.relatedFields = _.extend({}, attrs.Widget.prototype.fieldsToFetch);
                    attrs.fieldsInfo = {
                        default: _.mapObject(attrs.Widget.prototype.fieldsToFetch, function () {
                            return {};
                        }),
                    };
                    if (attrs.options.color_field) {
                        // used by m2m tags
                        attrs.relatedFields[attrs.options.color_field] = { type: 'integer' };
                        attrs.fieldsInfo.default[attrs.options.color_field] = {};
                    }
                }
            }

            if (attrs.Widget.prototype.fieldDependencies) {
                attrs.fieldDependencies = attrs.Widget.prototype.fieldDependencies;
            }

            return attrs;
        },
    });

    AbstractView.include({

        _processFieldsView: function (fieldsView, viewType) {
            var fv = this._super.apply(this, arguments);
            if(ks_session.ks_list_view_field_mode === "model_all_fields"  || ks_session.ks_list_view_field_mode === false) {
                var ks_is_value_present = false;
                if(fv.type === 'tree' && !(fieldsView.ks_inner_view_type ==="one2many" || fieldsView.ks_inner_view_type ==="many2many")) {
                    fv.arch["ks_readonly_true"] = []
                     // Adding fields to arch children
                    for(var ks_fields = 0; ks_fields < Object.keys(fv.fields).length; ks_fields++) {
                        ks_is_value_present = false
                        for(var ks_arch_children = 0 ; ks_arch_children < fv.arch.children.length ; ks_arch_children++) {
                            if(Object.keys(fv.fields)[ks_fields] === fv.arch.children[ks_arch_children].attrs.name) {
                                    ks_is_value_present =true
                                    break;
                            }
                        }
                        if(!ks_is_value_present) {
                               var a = {}
                               a["tag"] = "field"
                               a["attrs"] = {}
                               a["attrs"]["name"] = Object.keys(fv.fields)[ks_fields]
                               a["attrs"]["string"] = Object.values(fv.fields)[ks_fields].string
                               a["attrs"]["invisible"] ="1"
                               a["attrs"]["modifiers"] = {}
                               if(Object.values(fv.fields)[ks_fields].type ==="many2many" || Object.values(fv.fields)[ks_fields].type ==="many2one" || Object.values(fv.fields)[ks_fields].type ==="one2many" ) {
                                    fv.arch["ks_readonly_true"].push(Object.keys(fv.fields)[ks_fields])
                               }
                               a["attrs"]["modifiers"]["readonly"] = Object.values(fv.fields)[ks_fields].readonly
                               a["attrs"]["modifiers"]["required"] = Object.values(fv.fields)[ks_fields].required
                               a["attrs"]["modifiers"]["column_invisible"] = true
                               a["attrs"]["modifiers"] = JSON.stringify(a["attrs"]["modifiers"])
                               a["children"] = []
                               a["ks_not_standard_field"] = true;
                               fv.arch.children.push(a)

                        }
                    }
                }
            }
            return fv;
        },
    });

    BasicController.include({

        init: function(parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.ks_def_flag = 0;
        },

        canBeSaved: function (recordID) {
            var fieldNames = this.renderer.canBeSaved(recordID || this.handle);

            if(this.renderer.arch.ks_readonly_true) {
                for(var i = 0; i < fieldNames.length;i++){
                    for(var j = 0; j < this.renderer.arch.ks_readonly_true.length;j++){
                        if(fieldNames[i] === this.renderer.arch.ks_readonly_true[j]) {
                            fieldNames.splice(i,1);
                            break;
                        }
                    }
                }
            }
            if (fieldNames.length) {
                this._notifyInvalidFields(fieldNames);

                return false;
            }
            return true;
        },
        _saveRecord: function (recordID, options) {
            recordID = recordID || this.handle;
            options = _.defaults(options || {}, {
                stayInEdit: false,
                reload: true,
                savePoint: false,
            });

            // Check if the view is in a valid state for saving
            // Note: it is the model's job to do nothing if there is nothing to save
            if (this.canBeSaved(recordID)) {
                var self = this;
                var saveDef = this.model.save(recordID, { // Save then leave edit mode
                    reload: options.reload,
                    savePoint: options.savePoint,
                    viewType: options.viewType,
                });
                if (!options.stayInEdit) {
                    saveDef = saveDef.then(function (fieldNames) {
                        var def = fieldNames.length ? self._confirmSave(recordID) : self._setMode('readonly', recordID);
                        return def.then(function () {
                            return fieldNames;
                        });
                    });
                }
                return saveDef;
            } else {
                if(this.ks_def_flag === 1) {
                    this._discardChanges(recordID);
                    this.ks_def_flag = 0;
                } else {
                    this.ks_def_flag = this.ks_def_flag + 1
                }
                return $.Deferred().reject(); // Cannot be saved
            }
        }
    });

    fieldUtils.format['many2many'] = function(value){
       if (value.count === 0) {
           return _t('No records');
        } else if (value.count === 1) {
            return _t('1 record');
        } else {
            return value.count + _t(' records');
        }
    };

    fieldUtils.format['one2many'] = function(value){
       if (value.count === 0) {
           return _t('No records');
       } else if (value.count === 1) {
            return _t('1 record');
       } else {
            return value.count + _t(' records');
       }
    };

});



