odoo.define('ks_list_view_manager.controller', function (require) {

"use strict";

var core = require('web.core');
var _t = core._t;
var ListController = require('web.ListController');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');
var Dialog = require('web.Dialog');
var fieldUtils = require('web.field_utils');
var BasicModel = require('web.BasicModel');
var ks_session = require('web.session');
var QWeb = core.qweb;

    ListController.include({

    custom_events: _.extend({}, ListController.prototype.custom_events,{
        Ks_update_advance_search_renderer : "Ks_update_advance_search_controller",
        ks_remove_domain:"ks_remove_popup_domain",
        ks_update: "ks_update_columns",
    }),

    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);

        if(params.actionViews.length !== 0) {
            this.renderer.ksViewID = _.findWhere(params.actionViews, {type: 'list'}).viewID
        }

        this.ks_advance_search_refresh = false;
        this.ks_start_date = undefined;
        this.ks_end_date = undefined;
        this.ks_start_date_id = undefined;
        this.ks_end_date_id = undefined;
        this.ks_remove_popup_flag = false;
        this.ks_toggle = 0;
    },

    on_attach_callback: function () {
        if(ks_session.ks_header_color) {
            if($("tr[class='bg-primary']")){
                for(var i=0; i < $("tr[class='bg-primary']").length; i++) {
                    $("tr[class='bg-primary']")[i].style.setProperty("background-color",ks_session.ks_header_color,"important");
                }
            }
            if($("th[class='bg-primary']")){
                for(var i=0; i < $("th[class='bg-primary']").length; i++) {
                    $("th[class='bg-primary']")[i].style.setProperty("background-color",ks_session.ks_header_color,"important");
                }
            }
            if($("th[class='o_column_sortable bg-primary']")){
                for(var i=0; i < $("th[class='o_column_sortable bg-primary']").length; i++) {
                    $("th[class='o_column_sortable bg-primary']")[i].style.setProperty("background-color",ks_session.ks_header_color,"important");
                }
            }

            if($("th[class='o_list_record_selector bg-primary']")){
                for(var i=0; i < $("th[class='o_list_record_selector bg-primary']").length; i++) {
                    $("th[class='o_list_record_selector bg-primary']")[i].style.setProperty("background-color",ks_session.ks_header_color,"important");
                }
            }

            if($("th[class='o_list_record_delete bg-primary']")){
                for(var i=0; i < $("th[class='o_list_record_delete bg-primary']").length; i++) {
                    $("th[class='o_list_record_delete bg-primary']")[i].style.setProperty("background-color",ks_session.ks_header_color,"important");
                }
            }

            if($("th[class='o_column_sortable o-sort-down bg-primary']")){
                for(var i=0; i < $("th[class='o_column_sortable o-sort-down bg-primary']").length; i++) {
                    $("th[class='o_column_sortable o-sort-down bg-primary']")[i].style.setProperty("background-color",ks_session.ks_header_color,"important");
                }
            }

            if($("th[class='o-sort-up o_column_sortable bg-primary']")){
                for(var i=0; i < $("th[class=' o-sort-up o_column_sortable bg-primary']").length; i++) {
                    $("th[class='o-sort-up o_column_sortable bg-primary']")[i].style.setProperty("background-color",ks_session.ks_header_color,"important");
                }
            }

            var ks_header_search_children = $(this.$el.find("thead tr.hide-on-modal")).children()

            for(var i = 0; i < ks_header_search_children.length; i++) {
                ks_header_search_children[i].style.setProperty("background-color","#EEEEEE","important");
            }
        }

        this.renderer.on_attach_callback();
    },

    ks_remove_popup_domain: function(ks_options) {

            var ks_i;
            var key;
            var key_array;

            if(ks_options.data.ksDiv!==undefined) {
                key_array = ks_options.data.ksDiv.id.split("_value")
                key = key_array[0];
            } else {
                key = event.target.id;
            }

            if(this.renderer.ks_field_domain_dict[key]!==undefined){
                if(this.renderer.ks_field_domain_dict[key].length === 1 || ks_options.data.ksfieldtype === "date" || ks_options.data.ksfieldtype === "datetime") {
                     delete this.renderer.ks_field_domain_dict[key]
                     for(ks_i = 0;ks_i < this.renderer.ks_key_fields.length; ks_i++) {
                        if(key === this.renderer.ks_key_fields[ks_i]) {
                               break;
                        }
                }

            if(ks_options.data.ksDiv!==undefined) {
                    $("#"+ks_options.data.ksDiv.id).remove()
            } else {
                    $("#"+$(ks_options.data.event.target).parent().children()[$(ks_options.data.event.target).parent().children().length-2].id).remove();
            }

            this.renderer.ks_key_fields.splice(ks_i, 1);
            this.ks_remove_popup_flag = true;
            this.Ks_update_advance_search_controller(false);
            }
            else {
                for(var j = 0; j < this.renderer.ks_field_domain_dict[key].length; j++) {
                    if(this.renderer.ks_field_domain_dict[key][j] !== '|') {
                        if(ks_options.data.ksDiv!==undefined) {
                            if(this.renderer.ks_field_domain_dict[key][j][2] === ks_options.data.ksDiv.innerText) {
                               this.renderer.ks_field_domain_dict[key].splice(j,1)
                               this.renderer.ks_field_domain_dict[key].splice(0, 1);
                               break;
                            }
                        } else {
                                this.renderer.ks_field_domain_dict[key].splice(j,1)
                                this.renderer.ks_field_domain_dict[key].splice(0, 1);
                                break;
                        }
                    }
                }
                if(ks_options.data.ksDiv !== undefined) {
                    $("#"+ks_options.data.ksDiv.id).remove();
                } else {
                    $("#"+$(ks_options.data.event.target).parent().children()[$(ks_options.data.event.target).parent().children().length-2].id).remove();
                }
                this.ks_remove_popup_flag=true;
                this.Ks_update_advance_search_controller(false);
            }
        } else {
            this.ks_remove_popup_flag=true;
            this.Ks_update_advance_search_controller(false);
        }
    },

    Ks_update_advance_search_controller: function(ks_options) {

        if(this.ks_remove_popup_flag === true) {
            var ks_advance_search_params = {};
            ks_advance_search_params["modelName"] = this.renderer.state.model;
            ks_advance_search_params["context"] = this.renderer.state.context;
            ks_advance_search_params["ids"] = this.renderer.state.res_ids;
            ks_advance_search_params["offset"] = this.renderer.state.offset;
            ks_advance_search_params["currentId"] = this.renderer.state.res_id;
            ks_advance_search_params["selectRecords"] = this.renderer.selection
            ks_advance_search_params["groupBy"] = this.renderer.state.groupedBy
            this.renderer.ks_field_domain_list = [];

            for(var j = 0;j < this.renderer.ks_key_fields.length; j++) {
               this.renderer.ks_field_domain_list = this.renderer.ks_field_domain_list.concat(this.renderer.ks_field_domain_dict[this.renderer.ks_key_fields[j]]);
            }
            this.ks_remove_popup_flag=false;
            ks_advance_search_params["ksDomain"] = this.renderer.ks_field_domain_list;
            if(this.renderer.state.domain.length === 0) {
                this.renderer.ksBaseDomain = []
            }
            if(this.renderer.ksBaseDomain === null && (this.renderer.ksDomain ===null || this.renderer.ksDomain.length===0) && this.renderer.state.domain.length) {
                this.renderer.ksBaseDomain = this.renderer.state.domain
            }
            if(this.renderer.ksBaseDomain.length !== 0 || this.renderer.ks_field_domain_list.length !== 0 ) {
                ks_advance_search_params["domain"] = this.renderer.ksBaseDomain.concat(this.renderer.ks_field_domain_list)
            } else {
                ks_advance_search_params["domain"] = []
            }
            this.renderer.ksDomain = ks_advance_search_params["ksDomain"]
            this.update(ks_advance_search_params,undefined);
        }
        else {
                var ks_val_flag = false;
                if(ks_options.data.ks_val){
                   ks_val_flag = ks_options.data.ks_val.trim()!==0
                } else {
                   ks_val_flag = $('#'+ks_options.data.KsSearchId).val().trim() !== 0
                }

                if(Number(ks_val_flag)) {
                    this.ks_advance_search_refresh = true;
                    var ks_search_value = ks_options.data.ks_val || $('#'+ks_options.data.KsSearchId).val().trim();
                    var ks_advance_search_type = ks_options.data.ksfieldtype;
                    var ks_selection_values = [];
                    var ks_advance_search_params ={};
                    this.renderer.ks_field_domain_list=[];
                    this.ks_key_insert_flag = false;
                    var ks_data_insert_flag = false;
                    var ks_value = ks_options.data.KsSearchId.split("_lvm_start_date")
                    ks_advance_search_params["groupBy"] = this.renderer.state.groupedBy
                    ks_advance_search_params["modelName"] = this.renderer.state.model;
                    ks_advance_search_params["context"] = this.renderer.state.context;
                    ks_advance_search_params["ids"] = this.renderer.state.res_ids;
                    ks_advance_search_params["offset"] = this.renderer.state.offset;
                    ks_advance_search_params["currentId"] = this.renderer.state.res_id;
                    ks_advance_search_params["selectRecords"] = this.renderer.selection

                     if(ks_value.length === 1) {
                         ks_value = ks_options.data.KsSearchId.split("_lvm_end_date")
                         if(ks_value.length === 2)
                             ks_options.data.KsSearchId = ks_value[0];
                     }
                     else {
                         ks_options.data.KsSearchId = ks_value[0];
                     }

                     for(var ks_sel_check = 0; ks_sel_check < this.renderer.ks_key_fields.length; ks_sel_check++) {
                         if(ks_options.data.KsSearchId === this.renderer.ks_key_fields[ks_sel_check]) {
                               ks_data_insert_flag = true;
                         }
                     }

                     if((ks_data_insert_flag === false) || (ks_data_insert_flag === true && (ks_advance_search_type === "many2one" || ks_advance_search_type === "many2many"))) {
                           if(!(ks_advance_search_type === "datetime" || ks_advance_search_type === "date")) {
                                if(this.renderer.ks_key_fields.length === 0) {
                                   if(ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                                         try{
                                                var currency = this.getSession().get_currency(this.renderer.ks_list_view_data.currency_id);
                                                var formatted_value = fieldUtils.parse.float(ks_search_value || 0, {digits: currency && currency.digits});
                                                ks_search_value  =  formatted_value
                                                this.renderer.ks_key_fields.push(ks_options.data.KsSearchId);
                                            } catch {
                                                    this.do_notify(
                                                    _t("Please enter a valid Number")
                                                    );
                                            }
                                   } else {
                                            this.renderer.ks_key_fields.push(ks_options.data.KsSearchId);
                                   }
                                } else {
                                       for(var key_length = 0; key_length < this.renderer.ks_key_fields.length; key_length++) {
                                             if((this.renderer.ks_key_fields[key_length] === ks_options.data.KsSearchId)) {
                                                  this.ks_key_insert_flag=true;
                                                  break;
                                             }
                                        }
                                       if(!(this.ks_key_insert_flag)) {
                                             if(ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                                                 try{
                                                            var currency = this.getSession().get_currency(this.renderer.ks_list_view_data.currency_id);
                                                            var formatted_value = fieldUtils.parse.float(ks_search_value || 0, {digits: currency && currency.digits});
                                                            ks_search_value  =  formatted_value
                                                            this.renderer.ks_key_fields.push(ks_options.data.KsSearchId);
                                                        } catch {
                                                                this.do_notify(
                                                                _t("Please enter a valid Number")
                                                                );
                                                        }
                                             } else {
                                                this.renderer.ks_key_fields.push(ks_options.data.KsSearchId);
                                             }
                                       }
                               }
                           }

                     if(ks_advance_search_type === "datetime" || ks_advance_search_type === "date") {
                          if(ks_options.data.ksFieldIdentity === ks_options.data.KsSearchId + '_lvm_start_date lvm_start_date') {
                               this.ks_start_date = ks_search_value;
                               this.ks_start_date_id = ks_options.data.KsSearchId;
                          }else {
                                this.ks_end_date = ks_search_value;
                                this.ks_end_date_id=ks_options.data.KsSearchId
                          }

                          if(ks_advance_search_type==="datetime" || ks_advance_search_type==="date") {
                               if(ks_options.data.ksFieldIdentity === ks_options.data.KsSearchId+'_lvm_end_date lvm_end_date') {
                                    if(this.ks_start_date_id === this.ks_end_date_id) {
                                        this.renderer.ks_field_domain_dict[this.ks_start_date_id] = [[this.ks_start_date_id,'>=', this.ks_start_date], [this.ks_end_date_id,'<=', this.ks_end_date]]
                                        if(this.renderer.ks_key_fields.length === 0) {
                                            this.renderer.ks_key_fields.push(this.ks_start_date_id);
                                        }
                                        else {
                                             for(var key_length = 0;key_length < this.renderer.ks_key_fields.length; key_length++) {
                                                if(!(this.renderer.ks_key_fields[key_length] === ks_options.data.KsSearchId)) {
                                                    this.renderer.ks_key_fields.push(this.ks_start_date_id);
                                                    break;
                                                }
                                             }
                                        }
                                    }
                               }
                          }
                     } else if(ks_advance_search_type === 'selection') {
                          if(ks_search_value === "Select a Selection") {
                                 for(var j=0;j<this.renderer.ks_key_fields.length;j++) {
                                      this.renderer.ks_field_domain_list = this.renderer.ks_field_domain_list.concat(this.renderer.ks_field_domain_dict[this.renderer.ks_key_fields[j]]);
                                 }
                                ks_advance_search_params["ksDomain"] = this.renderer.ks_field_domain_list;
                                if(this.renderer.state.domain.length === 0) {
                                    this.renderer.ksBaseDomain = []
                                }
                                ks_advance_search_params["domain"] = this.renderer.ksBaseDomain.concat(this.renderer.ks_field_domain_list)
                                this.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                                this.update(ks_advance_search_params,undefined);
                          } else {

                                // obtaining values of selection
                                ks_selection_values = this.renderer.state.fields[ks_options.data.KsSearchId].selection;

                                //setting values for selection
                                for(var i = 0; i < ks_selection_values.length; i++) {
                                    if(ks_selection_values[i][1] === ks_search_value) {
                                        ks_search_value = ks_selection_values[i][0];
                                    }
                                }
                                this.renderer.ks_field_domain_dict[ks_options.data.KsSearchId] = [[ks_options.data.KsSearchId,'=', ks_search_value]]
                          }
                     } else if (ks_advance_search_type === "many2one" || ks_advance_search_type === "many2many") {
                            if(this.renderer.ks_field_domain_dict[ks_options.data.KsSearchId] === undefined)
                                 this.renderer.ks_field_domain_dict[ks_options.data.KsSearchId] = [[ks_options.data.KsSearchId, "ilike", ks_search_value]]
                            else
                                 this.renderer.ks_field_domain_dict[ks_options.data.KsSearchId].push([ks_options.data.KsSearchId, "ilike", ks_search_value])

                            if(this.renderer.ks_field_domain_dict[ks_options.data.KsSearchId].length>1) {
                                this.renderer.ks_field_domain_dict[ks_options.data.KsSearchId].unshift("|")
                            }
                            ks_advance_search_params["ids"] = this.initialState.res_id;
                     } else if(ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                              this.renderer.ks_field_domain_dict[ks_options.data.KsSearchId] = [[ks_options.data.KsSearchId,'=', ks_search_value]]
                     } else {
                            this.renderer.ks_field_domain_dict[ks_options.data.KsSearchId] = [[ks_options.data.KsSearchId, "ilike", ks_search_value]]
                     }

                    if(ks_advance_search_type === "datetime" || ks_advance_search_type === "date") {
                        if(ks_options.data.ksFieldIdentity === ks_options.data.KsSearchId+'_lvm_end_date lvm_end_date') {
                             for(var j=0; j < this.renderer.ks_key_fields.length; j++) {
                               this.renderer.ks_field_domain_list = this.renderer.ks_field_domain_list.concat(this.renderer.ks_field_domain_dict[this.renderer.ks_key_fields[j]]);
                        }
                        ks_advance_search_params["ksDomain"] = this.renderer.ks_field_domain_list;
                        if(this.renderer.state.domain.length === 0) {
                            this.renderer.ksBaseDomain = []
                        }
                        ks_advance_search_params["domain"] = this.renderer.ksBaseDomain.concat(this.renderer.ks_field_domain_list)
                        this.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                        this.update(ks_advance_search_params,undefined);
                        this.ks_start_date = undefined;
                        this.ks_end_date = undefined;
                        this.ks_start_date_id = undefined;
                        this.ks_end_date_id = undefined;
                    }
                }
                else {
                       if(ks_advance_search_type === 'monetary' || ks_advance_search_type === 'integer' || ks_advance_search_type === 'float') {
                            if(!(isNaN(ks_search_value))) {
                               for(var j = 0; j < this.renderer.ks_key_fields.length; j++) {
                                  this.renderer.ks_field_domain_list = this.renderer.ks_field_domain_list.concat(this.renderer.ks_field_domain_dict[this.renderer.ks_key_fields[j]]);
                               }
                            ks_advance_search_params["ksDomain"] = this.renderer.ks_field_domain_list;
                            if(this.renderer.state.domain.length === 0) {
                                  this.renderer.ksBaseDomain = []
                            }
                            ks_advance_search_params["domain"] = this.renderer.ksBaseDomain.concat(this.renderer.ks_field_domain_list)
                            this.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                            this.update(ks_advance_search_params,undefined);
                            }
                            else{
                                 if(this.renderer.state.domain.length === 0) {
                                        this.renderer.ksBaseDomain = []
                                    }
                                 ks_advance_search_params["domain"] = this.renderer.ksDomain || []
                                 this.update(ks_advance_search_params,undefined);
                            }
                       } else {
                            for(var j = 0; j < this.renderer.ks_key_fields.length; j++) {
                                  this.renderer.ks_field_domain_list = this.renderer.ks_field_domain_list.concat(this.renderer.ks_field_domain_dict[this.renderer.ks_key_fields[j]]);
                               }
                            ks_advance_search_params["ksDomain"] = this.renderer.ks_field_domain_list;
                            if(this.renderer.state.domain.length === 0) {
                                this.renderer.ksBaseDomain = []
                            }
                            ks_advance_search_params["domain"] = this.renderer.ksBaseDomain.concat(this.renderer.ks_field_domain_list)
                            this.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                            this.update(ks_advance_search_params,undefined);
                       }
                }
            } else {
                      for(var j=0;j<this.renderer.ks_key_fields.length;j++) {
                         this.renderer.ks_field_domain_list = this.renderer.ks_field_domain_list.concat(this.renderer.ks_field_domain_dict[this.renderer.ks_key_fields[j]]);
                      }
                      ks_advance_search_params["ksDomain"] = this.renderer.ks_field_domain_list;
                      if(this.renderer.state.domain.length === 0) {
                            this.renderer.ksBaseDomain = []
                      }
                      ks_advance_search_params["domain"] = this.renderer.ksBaseDomain.concat(this.renderer.ks_field_domain_list)
                      this.renderer.ksDomain = ks_advance_search_params["ksDomain"]
                      this.update(ks_advance_search_params,undefined);
                   }
            }
                 else {
                        this.ks_advance_search_refresh = true;
                        var ks_search_value = $('#'+ks_options.data.KsSearchId).val().trim();
                        var ks_advance_search_type = ks_options.data.ksfieldtype;
                        var ks_selection_values = [];
                        var ks_advance_search_params = {};
                        this.renderer.ks_field_domain_list = [];
                        this.ks_key_insert_flag = false;
                        var ks_data_insert_flag = false;
                        var ks_value = ks_options.data.KsSearchId.split("_lvm_start_date");

                        ks_advance_search_params["modelName"] = this.renderer.state.model;
                        ks_advance_search_params["context"] = this.renderer.state.context;
                        ks_advance_search_params["ids"] = this.renderer.state.res_ids;
                        ks_advance_search_params["offset"] = this.renderer.state.offset;
                        ks_advance_search_params["currentId"] = this.renderer.state.res_id;
                        ks_advance_search_params["selectRecords"] = this.renderer.selection
                        ks_advance_search_params["groupBy"] = []

                        for(var j=0;j<this.renderer.ks_key_fields.length;j++) {
                          this.renderer.ks_field_domain_list = this.renderer.ks_field_domain_list.concat(this.renderer.ks_field_domain_dict[this.renderer.ks_key_fields[j]]);
                        }
                        ks_advance_search_params["ksDomain"] = this.renderer.ks_field_domain_list;
                        if(this.renderer.state.domain.length === 0) {
                            this.renderer.ksBaseDomain = [];
                        }
                        ks_advance_search_params["domain"] = this.renderer.ksBaseDomain.concat(this.renderer.ks_field_domain_list);
                        this.renderer.ksDomain = ks_advance_search_params["ksDomain"];
                        this.update(ks_advance_search_params,undefined);
                   }
            }
    },

    ks_add_columns: function() {

         this.renderer.ks_duplicate_data = this.renderer.arch.children.slice(0);
         var self = this;
         $(".ks_columns_list").remove();
         $(".ks-text-center").remove();
         var ks_field_selection_list = QWeb.render("ks_list_view_fields_selection_list",{ks_field_list:this.renderer});
         $('.ks_columns').append($(ks_field_selection_list));
         $('.ks_columns_list').sortable();
         $( ".ks_columns_list" ).sortable({
                update: function( event, ui ) {
                    self.ks_update_columns();
                }
            });

         if(ks_session.ks_toggle_color) {
            $("input:checked + .ks_slider").css("background-color",ks_session.ks_toggle_color);
         }

         this.onBlur();
    },

    ks_update_width_method: function() {

         this.renderer.ks_duplicate_data = this.renderer.arch.children.slice(0);
         var self = this;
         $(".ks_columns_list").remove();
         $(".ks-text-center").remove();
         var ks_field_selection_list = QWeb.render("ks_list_view_fields_selection_list",{ks_field_list:this.renderer});
         $('.ks_columns').append($(ks_field_selection_list));
         $('.ks_columns_list').sortable();
         $( ".ks_columns_list" ).sortable({
                update: function( event, ui ) {
                    self.ks_update_columns();
                }
            });

         if(ks_session.ks_toggle_color) {
            $("input:checked + .ks_slider").css("background-color",ks_session.ks_toggle_color);
         }
    },

    ks_update_columns : function() {

        var ks_fieldsname = [];
        var ks_field;
        var ks_orders_id = [];
        var ks_array_order = [];
        var ks_columns_data=[];
        var ks_integer_order=[];
        var ks_hidden_list = [];
        var ks_column_string = [];
        var ks_intermediate_string_array = [];
        var ks_intermediate_string;
        var ks_name_id = [];
        var self = this;

        $('.ks_list_field_header .ks_list_field_container .ks_list_field_info .ks_hide_show_checkbox').each(function(){ ks_orders_id.push(this.id);});
        $('.ks_list_field_header .ks_list_field_container .ks_list_field_info span.ks_editable').each(function(){ ks_name_id.push(this.dataset.fieldId);});

        this.renderer.arch.children = this.renderer.ks_duplicate_data.slice(0);
        $("input:not(:checked) + .ks_slider").css("background-color","#CCCCCC");

        if(ks_session.ks_toggle_color) {
            $("input:checked + .ks_slider").css("background-color",ks_session.ks_toggle_color);
        } else{
            $("input:checked + .ks_slider").css("background-color","#7C7BAD");
        }

        for (var i = 0; i < $('.ks_list_field_header .ks_list_field_container .ks_list_field_info span.ks_editable').length; i++) {
             ks_field = this.renderer.arch.children[i];
             if(ks_field) {
                 if($('#inputid'+i).prop('checked')) {
                     ks_field.attrs.modifiers.column_invisible = false;
                     ks_field.attrs.invisible = "0";
                     if(ks_field.ks_not_standard_field && (this.renderer.state.fields[ks_field.attrs.name].type === "one2many" || this.renderer.state.fields[ks_field.attrs.name].type === "many2many" || this.renderer.state.fields[ks_field.attrs.name].type === "many2one")){
                        ks_field.attrs.modifiers.readonly = true
                     }
                 } else {
                        ks_field.attrs.modifiers.column_invisible = true;
                        ks_field.attrs.invisible = "1";
                        ks_hidden_list.push(ks_field.attrs.name);
                 }


                 ks_intermediate_string_array =  $('.ks_list_field_header .ks_list_field_container .ks_list_field_info span.ks_editable')[i].innerText.trim().split(" ")
                 ks_intermediate_string=""

                 for(var ks_col_iter = 0;ks_col_iter<ks_intermediate_string_array.length; ks_col_iter++) {
                    if(ks_col_iter === ks_intermediate_string_array.length-1) {
                        ks_intermediate_string += ks_intermediate_string_array[ks_col_iter]
                    }else {
                        ks_intermediate_string += ks_intermediate_string_array[ks_col_iter]+" "
                    }
                 }
                 ks_column_string[ks_name_id[i]] = ks_intermediate_string
                 this.renderer.arch.children[i] = ks_field;
                 this.renderer.arch.children[i].attrs["string"] = ks_column_string[i]
                 ks_integer_order = ks_orders_id[i].split("id");
                 ks_array_order[i] = Number(ks_integer_order[1]);
            }
        }

        ks_columns_data = this.renderer.arch.children.slice(0);

        var i = 2;

        if(!ks_session.ks_serial_number)
            i = 1;
        var ks_columns_width = {};

        var ks_table_width = this.$el.find("table").innerWidth();

        for(; i < self.$el.find("thead tr.bg-primary th").length/2; i++) {
            ks_columns_width[self.$el.find("thead tr.bg-primary th")[i].innerText] = Number(self.$el.find("thead tr.bg-primary th")[i].style.getPropertyValue("width").split("px")[0]/ self.$el.find(".table").width() * 100);
        }

         ks_table_width = (ks_table_width/ ($(window).width())) * 100;

        for(var i = 0; i < $('.ks_list_field_header .ks_list_field_container .ks_list_field_info span.ks_editable').length; i++) {
            if(this.renderer.arch.children[i].tag === "field") {
//                ks_field = this.renderer.arch.children[i];
                ks_columns_data[i] = this.renderer.arch.children[ks_array_order[i]];
                ks_columns_data[i].attrs["string"] = ks_column_string[ks_array_order[i]]
                ks_fieldsname.push({
                   fieldName: ks_columns_data[i].attrs.name,
                   ksShowField: $('#inputid'+ks_array_order[i]).prop('checked'),
                   ks_field_order: i,
//                   ks_readonly : ks_columns_data[i].attrs.modifiers["readonly"] || false,
//                   ks_required : ks_columns_data[i].attrs.modifiers["required"] || false,
                   ks_invisible: ks_columns_data[i].attrs["invisible"],
                   ks_Columns_name: ks_column_string[ks_array_order[i]],
                   ks_col_width: ks_columns_width[ks_column_string[ks_array_order[i]]] || 0,
                 });
                this.renderer.arch.children[ks_array_order[i]] = ks_columns_data[i];
            }
        }

        this.renderer.arch.children = ks_columns_data.slice(0);
        if(ks_session.ks_list_view_field_mode === "model_all_fields" || ks_session.ks_list_view_field_mode === false) {
            this._rpc({
                model: 'user.specific',
                method: 'updating_data',
                args: [this.modelName,ks_fieldsname,odoo.session_info.uid,this.renderer.ksViewID,ks_table_width],
            })
        } else {
            this._rpc({
                model: 'ks.user.standard.specific',
                method: 'updating_data',
                args: [this.modelName,ks_fieldsname,odoo.session_info.uid,this.renderer.ksViewID,ks_table_width],
            })
        }
        for(var i = 0;i <ks_hidden_list.length; i++) {
            for(var j = 0; j < Object.keys(this.renderer.ks_field_domain_dict).length; j++) {
                if(Object.keys(this.renderer.ks_field_domain_dict)[j] === ks_hidden_list[i]) {
                    delete this.renderer.ks_field_domain_dict[ks_hidden_list[i]]
                }
            }
        }
        for(var i = 0;i <ks_hidden_list.length; i++) {
            for(var j = 0; j < this.renderer.ks_key_fields.length; j++) {
                if(this.renderer.ks_key_fields[j] === ks_hidden_list[i]) {
                    this.renderer.ks_key_fields.splice(j,1)
                    j = j - 1;
                }
            }
        }
        this.ks_remove_popup_flag = true;
        $(".cancel_button").addClass("d-none");
        this.Ks_update_advance_search_controller(false);
    },

    ks_searchBar : function(e) {

        var ks_input, ks_filter, ks_ul, ks_li, ks_text, i, txtValue;
        ks_input = document.getElementById('myInput');
        ks_filter = ks_input.value.toUpperCase();
        ks_ul = document.getElementsByClassName("ks_columns")[0];
        ks_li = ks_ul.getElementsByClassName('ks_list_field_header');

        if(ks_li.length===this.renderer.arch.children["length"]) {
            for (i = 0; i < this.renderer.arch.children["length"]; i++) {
                ks_text = ks_li[i].getElementsByClassName('ks_list_field_info')[0].children[1];
                txtValue = ks_text.textContent || ks_text.innerText;

                if (txtValue.toUpperCase().indexOf(ks_filter) > -1) {
                        ks_li[i].style.display="";
                }
                else {
                        ks_li[i].style.display = "none";
                }
            }
        } else {
                var ks_other_count_type = 0
                for(var j = 0; j < this.renderer.arch.children["length"] ; j++) {
                    if(this.renderer.arch.children[j].tag !== 'field') {
                        ks_other_count_type ++;
                    }
                }

                for (i = 0; i < this.renderer.arch.children["length"] - ks_other_count_type ; i++) {
                    ks_text = ks_li[i].getElementsByClassName('ks_list_field_info')[0].children[1];
                    txtValue = ks_text.textContent || ks_text.innerText;

                    if (txtValue.toUpperCase().indexOf(ks_filter) > -1) {
                            ks_li[i].style.display="";
                    }
                    else {
                            ks_li[i].style.display = "none";
                    }
                }

        }
    },

    ks_refresh : function() {
        var self = this;
        if(ks_session.ks_list_view_field_mode === "model_all_fields" || ks_session.ks_list_view_field_mode === false){
                self._rpc({
            model: 'user.specific',
            method: 'check_user_exists',
            args: [self.modelName,odoo.session_info.uid,self.renderer.ksViewID],
        }).then(function(ks_user_table_result){
             self.renderer.ks_user_table_result = ks_user_table_result;
             if(self.ks_advance_search_refresh === true) {
                self.renderer.ks_field_domain_dict={};
                self.renderer.ks_key_fields=[];
                self.renderer.ks_field_domain_list=[];
                var ks_advance_search_refresh_params ={};

                ks_advance_search_refresh_params["modelName"]=self.renderer.state.model;
                ks_advance_search_refresh_params["context"]=self.renderer.state.context;
                ks_advance_search_refresh_params["ids"]=self.renderer.state.res_ids;
                ks_advance_search_refresh_params["offset"]=self.renderer.state.offset;
                ks_advance_search_refresh_params["currentId"]=self.renderer.state.res_id;
                ks_advance_search_refresh_params["selectRecords"]=self.renderer.selection
                ks_advance_search_refresh_params["groupBy"] = self.renderer.state.groupedBy
                ks_advance_search_refresh_params["domain"]=self.renderer.ksBaseDomain || []
                self.renderer.ksDomain = []
                self.update(ks_advance_search_refresh_params,undefined);
             }
             else {
                self.renderer.getParent().reload();
                if($('#myInput').val())
                     self.onBlur();
             }
             if(!self.ks_is_restore_flag)
                self.renderer.ks_refreshed = true;
             else
                self.ks_is_restore_flag = false;
        });
        }else {
                self._rpc({
            model: 'ks.user.standard.specific',
            method: 'check_user_exists',
            args: [self.modelName,odoo.session_info.uid,self.renderer.ksViewID],
        }).then(function(ks_user_table_result){
             self.renderer.ks_user_table_result = ks_user_table_result;
             if(self.ks_advance_search_refresh===true) {
                self.renderer.ks_field_domain_dict={};
                self.renderer.ks_key_fields=[];
                self.renderer.ks_field_domain_list=[];
                var ks_advance_search_refresh_params ={};

                ks_advance_search_refresh_params["modelName"]=self.renderer.state.model;
                ks_advance_search_refresh_params["context"]=self.renderer.state.context;
                ks_advance_search_refresh_params["ids"]=self.renderer.state.res_ids;
                ks_advance_search_refresh_params["offset"]=self.renderer.state.offset;
                ks_advance_search_refresh_params["currentId"]=self.renderer.state.res_id;
                ks_advance_search_refresh_params["selectRecords"]=self.renderer.selection
                ks_advance_search_refresh_params["groupBy"] = self.renderer.state.groupedBy
                ks_advance_search_refresh_params["domain"]=self.renderer.ksBaseDomain || []
                self.renderer.ksDomain = []
                self.update(ks_advance_search_refresh_params,undefined);
             }
             else {
                self.renderer.getParent().reload();
                if($('#myInput').val())
                     self.onBlur();
             }
             if(!self.ks_is_restore_flag)
                self.renderer.ks_refreshed = true;
             else
                self.ks_is_restore_flag = false;
        });
        }
    },

    ks_confirm_restoreData: function() {

        var self = this;
        var $container = $(event.currentTarget).parents('.oe_action:first');
        Dialog.confirm(this, _t("Are you sure you want to restore to Odoo default View?"), {
                confirm_callback: function () {
                $container.remove();
                self.ks_restoreData();
            }});
    },

    ks_restoreData: function() {
        var self = this;
        var ks_restore_data = [];
        ks_restore_data = self.renderer.arch.children.slice(0);
        self.ks_is_restore_flag = true;
        if(ks_session.ks_list_view_field_mode === "model_all_fields" || ks_session.ks_list_view_field_mode === false) {
            self._rpc({
                model: 'user.specific',
                method: 'restoring_to_default',
                args: [self.modelName,odoo.session_info.uid,self.renderer.ksViewID],
            }).then(function(){
                for(var i = 0; i < self.renderer.arch.children["length"]; i++) {
                    for(var j = 0; j <self.renderer.arch.children["length"]; j++) {

                        if(ks_restore_data[j].attrs.name === self.renderer.restoreName[i]) {
                            self.renderer.arch.children[i] = ks_restore_data[j]

                            if(self.renderer.arch.children[i].attrs.hasOwnProperty("ks_prev_string")){
                                self.renderer.arch.children[i].attrs.string = self.renderer.arch.children[i].attrs.ks_prev_string;
                            }

                            if(self.renderer.arch.children[i].attrs.hasOwnProperty("ks_prev_invisible")){
                                if(self.renderer.arch.children[i].attrs.ks_prev_invisible === "1" || self.renderer.arch.children[i].attrs.ks_prev_invisible === "0" || self.renderer.arch.children[i].attrs.ks_prev_invisible === undefined) {
                                    self.renderer.arch.children[i].attrs.invisible = self.renderer.arch.children[i].attrs.ks_prev_invisible;
                                    self.renderer.arch.children[i].attrs.modifiers.column_invisible = self.renderer.arch.children[i].attrs.ks_prev_invisible === "1" ? true : false;
                                } else{
                                    self.renderer.arch.children[i].attrs.invisible = self.renderer.arch.children[i].attrs.ks_prev_invisible === "True" ? true : false;
                                    self.renderer.arch.children[i].attrs.modifiers.column_invisible = self.renderer.arch.children[i].attrs.ks_prev_invisible === "True" ? true : false;
                                }
                            }
                        }
                    }
                }
                var ks_restore_order = self.renderer.arch.children;
                ks_restore_order.sort(function(x,y){return x.attrs.ks_sort_position - y.attrs.ks_sort_position});
                self.renderer.ks_group_by_width_flag = true;
                self.renderer.ks_user_table_result = false
                self.onBlur();
                self.ks_advance_search_refresh = true;
                self.ks_refresh();
                self.ks_cancelEdit();
                self.renderer.ks_previous_columns_length = false;
                self.renderer.ks_restore_flag = true;
            });
        } else {
            self._rpc({
                model: 'ks.user.standard.specific',
                method: 'restoring_to_default',
                args: [self.modelName,odoo.session_info.uid,self.renderer.ksViewID],
            }).then(function(){
                for(var i = 0; i < self.renderer.arch.children["length"]; i++) {
                    for(var j = 0; j <self.renderer.arch.children["length"]; j++) {

                        if(ks_restore_data[j].attrs.name === self.renderer.restoreName[i]) {
                            self.renderer.arch.children[i] = ks_restore_data[j]

                            if(self.renderer.arch.children[i].attrs.hasOwnProperty("ks_prev_string")){
                                self.renderer.arch.children[i].attrs.string = self.renderer.arch.children[i].attrs.ks_prev_string;
                            }

                            if(self.renderer.arch.children[i].attrs.hasOwnProperty("ks_prev_invisible")){
                                if(self.renderer.arch.children[i].attrs.ks_prev_invisible === "1" || self.renderer.arch.children[i].attrs.ks_prev_invisible === "0" || self.renderer.arch.children[i].attrs.ks_prev_invisible === undefined) {
                                    self.renderer.arch.children[i].attrs.invisible = self.renderer.arch.children[i].attrs.ks_prev_invisible;
                                    self.renderer.arch.children[i].attrs.modifiers.column_invisible = self.renderer.arch.children[i].attrs.ks_prev_invisible === "1" ? true : false;
                                } else{
                                    self.renderer.arch.children[i].attrs.invisible = self.renderer.arch.children[i].attrs.ks_prev_invisible === "True" ? true : false;
                                    self.renderer.arch.children[i].attrs.modifiers.column_invisible = self.renderer.arch.children[i].attrs.ks_prev_invisible === "True" ? true : false;
                                }
                            }
                        }
                    }
                }
                var ks_restore_order = self.renderer.arch.children;
                ks_restore_order.sort(function(x,y){return x.attrs.ks_sort_position - y.attrs.ks_sort_position});    self.renderer.ks_group_by_width_flag = true;
                self.renderer.ks_user_table_result = false
                self.onBlur();
                self.ks_advance_search_refresh = true;
                self.ks_refresh();
                self.ks_cancelEdit();
                self.renderer.ks_previous_columns_length = false;
                self.renderer.ks_restore_flag = true;
            });
        }
    },
    ks_copyRecord : function() {

        var self = this;
        var ks_id=this.getSelectedIds();
        var ks_model_name=this.modelName;

        if(ks_session.ks_list_view_field_mode === "model_all_fields" || ks_session.ks_list_view_field_mode === false) {
            this._rpc({
                model: 'user.specific',
                method: 'ks_duplicate_record',
                args: [ks_id,ks_model_name],
            }).then(function(result){
                self.renderer.getParent().reload();
                $('.copy_button').hide();
            });
        } else {
            this._rpc({
                model: 'ks.user.standard.specific',
                method: 'ks_duplicate_record',
                args: [ks_id,ks_model_name],
            }).then(function(result){
                self.renderer.getParent().reload();
                $('.copy_button').hide();
            });
        }
    },

    renderButtons: function($node) {
        this._super.apply(this, arguments);
        var self = this;
        if (self.$buttons) {
            self.$buttons.on('show.bs.dropdown', '#ks_dropdown',self.ks_add_columns.bind(self));
            self.$buttons.on('hide.bs.dropdown', '#ks_dropdown',function(e){
                if (!e.hasOwnProperty("clickEvent")) return e;
                return $(".ks_list_view_dropdown_container").has(e.clickEvent.target).length>0?false:e;
            });
            self.$buttons.on('blur',".ks_editable",function(event){
                 if(!$(event.relatedTarget).hasClass("cancel_button")) {
                    ("#"+$(event.target).children().remove());
                    var ks_input_value = $('input.ks_editable[data-field-id='+event.target.dataset.fieldId+']');
                    var ks_span_value = $('span.ks_editable[data-field-id='+event.target.dataset.fieldId+']');
                    ks_input_value.val().length === 0 ? ks_span_value.text(ks_span_value.text()) :ks_span_value.text (ks_input_value.val());
                    $(".cancel_button").addClass("d-none")
                    self.ks_update_columns();
                 }
            });
            self.$buttons.on("keyup",'#myInput',self.ks_searchBar.bind(self));
            self.$buttons.on("click",'.refresh_button',self.ks_refresh.bind(self));
            self.$buttons.on("click",'.restore_button',self.ks_confirm_restoreData.bind(self));
            self.$buttons.on("click",'.copy_button',self.ks_copyRecord.bind(self));
            self.$buttons.on("click",".mode_button",self.ks_modeToggle.bind(self));
            self.$buttons.on("click",".cancel_button",self.ks_cancelEdit.bind(self));
            self.$buttons.on("click",".ks_export_button",self._onExportData.bind(self));
        }
    },

    _onExportData: function() {
        var self = this;
        return this._super.apply(this, arguments);
    },

    ks_cancelEdit: function(event) {

         this.renderer.ks_duplicate_data = this.renderer.arch.children.slice(0);
         var self = this;
         var ks_field_selection_list = QWeb.render("ks_list_view_fields_selection_list_edit",{ks_field_list:this.renderer});
         $(".ks_columns_list").replaceWith($(ks_field_selection_list));
         $('.ks_columns_list').sortable();
         $( ".ks_columns_list" ).sortable({
                update: function( event, ui ) {
                    self.ks_update_columns();
                }
         });

         if(ks_session.ks_toggle_color) {
            $("input:checked + .ks_slider").css("background-color",ks_session.ks_toggle_color);
         }

         $(".cancel_button").addClass("d-none")
    },

    _onSelectionChanged: function (event) {
        this._super.apply(this,arguments);
        var ks_button = $('.copy_button');
        if(this.renderer.selection.length !== 0) {
             ks_button.show();
        }
        else {
             ks_button.hide();
        }
    },

    onBlur : function() {
        var ks_input, ks_filter, ks_ul, ks_li, ks_text, i, txtValue;
        $('#myInput').val('');
        ks_input = $('#myInput').val();
        ks_filter = ks_input.toUpperCase();
        ks_ul = document.getElementsByClassName("ks_columns")[0];
        ks_li = ks_ul.getElementsByClassName('ks_list_field_header');
        if(ks_li.length===this.renderer.arch.children["length"]) {
          for (i = 0; i < this.renderer.arch.children["length"]; i++) {
            ks_text = ks_li[i].getElementsByClassName('ks_list_field_info')[0].children[1];
            txtValue = ks_text.textContent || ks_text.innerText;

            if (txtValue.toUpperCase().indexOf(ks_filter) > -1) {
                ks_li[i].style.display="";
             }
          }
        }
    },

    ks_modeToggle: function() {
        if(this.ks_toggle===1) {
              if ($('#mode').prop('checked')===true) {
              this.renderer.editable = "top";
              this.editable = "top";
              this.renderer.is_ks_editable_on = true;
              this.mode="edit";
            } else {
               this.renderer.editable = false;
               this.editable = false;
               this.renderer.is_ks_editable_on = false;
               this.mode="readonly";
            }
            this._rpc({
               model: 'user.mode',
               method: 'updating_mode',
               args: [this.modelName,odoo.session_info.uid,this.renderer.editable,this.renderer.ksViewID],
            });
        }
        if(this.ks_toggle===1) {
            this.ks_toggle=0
        } else
        {
            this.ks_toggle++;
        }
    },

    ks_update_width_along_data: function() {
        var ks_fieldsname = [];
        var ks_field;
        var ks_orders_id = [];
        var ks_array_order = [];
        var ks_columns_data=[];
        var ks_integer_order=[];
        var ks_hidden_list = [];
        var ks_column_string = [];
        var ks_intermediate_string_array = [];
        var ks_intermediate_string;
        var ks_name_id=[];
        var self = this;
        $('.ks_list_field_header .ks_list_field_container .ks_list_field_info .ks_hide_show_checkbox').each(function(){ ks_orders_id.push(this.id);});
        $('.ks_list_field_header .ks_list_field_container .ks_list_field_info span.ks_editable').each(function(){ ks_name_id.push(this.dataset.fieldId);});
        this.renderer.arch.children = this.renderer.ks_duplicate_data.slice(0);
        if(ks_session.ks_toggle_color) {
            $("input:checked + .ks_slider").css("background-color",ks_session.ks_toggle_color);
         }

        $("input:not(:checked) + .ks_slider").css("background-color","#CCCCCC");

        for (var i = 0; i < $('.ks_list_field_header .ks_list_field_container .ks_list_field_info span.ks_editable').length; i++) {
             ks_field = this.renderer.arch.children[i];
             if(ks_field) {
                 if($('#inputid'+i).prop('checked')) {
                     ks_field.attrs.modifiers.column_invisible = false;
                     ks_field.attrs.invisible = "0";
                     if(ks_field.ks_not_standard_field && (this.renderer.state.fields[ks_field.attrs.name].type === "one2many" || this.renderer.state.fields[ks_field.attrs.name].type === "many2many" || this.renderer.state.fields[ks_field.attrs.name].type === "many2one")){
                        ks_field.attrs.modifiers.readonly = true;
                     }
                 } else {
                        ks_field.attrs.modifiers.column_invisible = true;
                        ks_field.attrs.invisible = "1";
                        ks_hidden_list.push(ks_field.attrs.name);
                 }

                 ks_intermediate_string_array =  $('.ks_list_field_header .ks_list_field_container .ks_list_field_info span.ks_editable')[i].innerText.trim().split(" ")
                 ks_intermediate_string=""
                 for(var ks_col_iter = 0;ks_col_iter<ks_intermediate_string_array.length; ks_col_iter++) {
                    if(ks_col_iter === ks_intermediate_string_array.length-1) {
                        ks_intermediate_string += ks_intermediate_string_array[ks_col_iter]
                    }else {
                        ks_intermediate_string += ks_intermediate_string_array[ks_col_iter]+" "
                    }
                 }
                 ks_column_string[ks_name_id[i]] = ks_intermediate_string
                 this.renderer.arch.children[i] = ks_field;
                 this.renderer.arch.children[i].attrs["string"] = ks_column_string[i]
                 ks_integer_order = ks_orders_id[i].split("id");
                 ks_array_order[i] = Number(ks_integer_order[1]);
            }
        }

        ks_columns_data = this.renderer.arch.children.slice(0);
        var ks_columns_width = {}
        var i = 2;

        if(!ks_session.ks_serial_number)
            i = 1;

        var ks_table_width = this.$el.find("table").innerWidth();

        for(; i < self.$el.find("thead tr.bg-primary th").length/2; i++) {
            ks_columns_width[self.$el.find("thead tr.bg-primary th")[i].innerText] = Number(self.$el.find("thead tr.bg-primary th")[i].style.getPropertyValue("width").split("px")[0] / self.$el.find(".table").width() * 100);
        }

        ks_table_width = (ks_table_width/ ($(window).width())) * 100;

        for(var i = 0; i < $('.ks_list_field_header .ks_list_field_container .ks_list_field_info span.ks_editable').length; i++) {
            if(this.renderer.arch.children[i].tag === "field") {
//                ks_field = this.renderer.arch.children[i];
                ks_columns_data[i] = this.renderer.arch.children[ks_array_order[i]];
                ks_columns_data[i].attrs["string"] = ks_column_string[ks_array_order[i]];
                ks_fieldsname.push({
                   fieldName: ks_columns_data[i].attrs.name,
                   ksShowField: $('#inputid'+ks_array_order[i]).prop('checked'),
                   ks_field_order: i,
//                   ks_readonly : ks_columns_data[i].attrs.modifiers["readonly"] || false,
//                   ks_required : ks_columns_data[i].attrs.modifiers["required"] || false,
                   ks_invisible: ks_columns_data[i].attrs["invisible"],
                   ks_Columns_name: ks_column_string[ks_array_order[i]],
                   ks_col_width: ks_columns_width[ks_column_string[ks_array_order[i]]] || 0,
                 });
            }
            this.renderer.arch.children[ks_array_order[i]] = ks_columns_data[i];
        }

        this.renderer.arch.children = ks_columns_data.slice(0);
        this.renderer.arch.children = ks_columns_data.slice(0);
        if(ks_session.ks_list_view_field_mode === "model_all_fields" || ks_session.ks_list_view_field_mode === false) {
            this._rpc({
                model: 'user.specific',
                method: 'updating_data',
                args: [this.modelName,ks_fieldsname,odoo.session_info.uid,this.renderer.ksViewID,ks_table_width],
            })
        } else {
            this._rpc({
                model: 'ks.user.standard.specific',
                method: 'updating_data',
                args: [this.modelName,ks_fieldsname,odoo.session_info.uid,this.renderer.ksViewID,ks_table_width],
            })
        }
    },

    });

});


