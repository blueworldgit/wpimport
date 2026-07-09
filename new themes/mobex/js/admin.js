/* Helpers
----*/

    !function(a){"use strict";var e=a('.ocdi__button-container a[href*="page=one-click-demo-import&step=import&import=0"]');void 0!==e&&e.length&&(a("body").hasClass("demo-import-activation")?(e.addClass("disabled"),a(".custom-intro-text").replaceWith('<div class="activate-demo-import"><input type="text" placeholder="Paste your purchase code to activate demo data import" /><a target="_blank" href="//help.market.envato.com/hc/en-us/articles/202822600-Where-Is-My-Purchase-Code-">Where Is My Purchase Code?</a></div>'),a("body").on("input",".activate-demo-import > input",function(t){var s,d,i;s=this,void 0===(i=(d=a(s).removeClass("invalid")).val())||!i.length||d.hasClass("valid")||d.hasClass("disabled")||(d.addClass("disabled"),a.ajax({url:admin_opt.ajaxUrl,type:"post",data:{action:"wB_4QM_pd2zE_Hv9X_W",code:i},success:function(a){try{if(a)switch(a){case"valid":d.removeClass("disabled").addClass("valid").val("Purchase code validated successfully! You can now import demo data.").attr("disabled","disabled"),d.next("a").remove(),e.removeClass("disabled");break;case"invalid":alert("Purchase code not found"),d.addClass("invalid").removeClass("disabled");break;default:alert(a),d.removeClass("disabled")}else d.removeClass("disabled"),alert("No data retured")}catch(t){console.log(t)}},error:function(){alert(ajaxUrl.adminAJAXError)}}))}),e.on("click",function(e){a(this).hasClass("disabled")&&e.preventDefault()})):(e.attr("href",e.attr("href").replace("step=import","step=activate")),e.text("Active demo data import")))}(jQuery);

    function capitalizeFirstLetter(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

/* Megamenu
----*/

    (function($){

        "use strict";

        var mmo = $('.megamenu-options');

        mmo.each(function(){

            var $this = $(this),
                mms   = $this.find('.mms select'),
                mmc   = $this.find('.mmc');

            if ( mms.val() == "true") {
                mmc.show();
            }

            mms.on("change",function(){
                if ($(this).val() == "false") {
                    mmc.hide();
                } else {
                    mmc.show();
                }
            });

        });

        function megamenuWidth(selected){
            if ( selected == 100) {
                $('.megamenu-toggle').hide(0);
            } else {
                $('.megamenu-toggle').show(0);
            }
        }

        function megamenuTabStyles(tabChecked){
            if (tabChecked) {
                $('.custom-tab-styling').show(0);
            } else {
                $('.custom-tab-styling').hide(0);
            }
        }

        function megamenuSidebar(sidebarChecked){

            if (sidebarChecked) {
                $('.cmb-row:not(.cmb2-id-enovathemes-addons-sidebar)').hide(0);
            } else {
                $('.cmb-row:not(.cmb2-id-enovathemes-addons-sidebar)').show(0);

                if ($('select[name="enovathemes_addons_megamenu_width"] option:selected').val() == 100) {
                    $('.megamenu-toggle').hide(0);
                }

                if (!$('input[name="enovathemes_addons_tabbed"]').is(':checked')) {
                    $('.custom-tab-styling').hide(0);
                }

            }

        }

        var selected       = $('select[name="enovathemes_addons_megamenu_width"] option:selected').val();
        var tabChecked     = ($('input[name="enovathemes_addons_tabbed"]')).is(':checked') ? true : false;
        var sidebarChecked = ($('input[name="enovathemes_addons_sidebar"]')).is(':checked') ? true : false;

        megamenuWidth(selected);
        megamenuTabStyles(tabChecked);
        megamenuSidebar(sidebarChecked);

        $('select[name="enovathemes_addons_megamenu_width"]').on("change",function(){
            selected = $(this).val();
            megamenuWidth(selected);
        });

        $('input[name="enovathemes_addons_sidebar"]').on("change",function(){
            sidebarChecked = (this.checked) ? true: false;
            megamenuSidebar(sidebarChecked);
        });

        $('input[name="enovathemes_addons_tabbed"]').on("change",function(){
            tabChecked = (this.checked) ? true: false;
            megamenuTabStyles(tabChecked);
        });

        

    })(jQuery);

/* Colorpicker
----*/

    (function( $ ) {

        "use strict";

        $(function() {
            $('.enovathemes-color-picker').wpColorPicker();
            $('#mobex_enovathemes_label1_color').wpColorPicker();
            $('#mobex_enovathemes_label2_color').wpColorPicker();
        });

    })( jQuery );

/* Product index
----*/

    (function( $ ) {

        "use strict";

        function fetchProducts(offset = 0, limit = 500) {
            return new Promise((resolve, reject) => {
                $.ajax({
                    url: admin_opt.adminAjax,
                    type: 'POST',
                    data: {
                        action: 'et-woo-product-index',
                        'index-nonce': admin_opt.productIndexNonce,
                        offset: offset,
                        limit: limit
                    },
                    dataType: 'json',
                    success: function(response) {
                        if (response) {

                            console.log(response);

                            if (response.products && Object.keys(response.products).length > 0) {
                                resolve({
                                    products: response.products,
                                    hasMore: response.has_more, //  Fixed this line
                                    nextOffset: response.offset //  Fixed this line
                                });
                            } else {
                                resolve(null);
                            }
                        } else {
                            reject(response.products);
                        }
                    },
                    error: function(xhr, status, error) {
                        reject(error);
                    }
                });
            });
        }

        async function loadAllProducts() {
            let offset = 0;
            let allProducts = {};
            let hasMore = true;

            while (hasMore) {
                try {
                    let response = await fetchProducts(offset);
                    if (response && response.products) {
                        // Merge product data
                        Object.keys(response.products).forEach(lang => {
                            allProducts[lang] = allProducts[lang] || [];
                            allProducts[lang] = allProducts[lang].concat(response.products[lang]);
                        });

                        offset = response.nextOffset;
                        hasMore = response.hasMore;
                    } else {
                        hasMore = false;
                    }
                } catch (error) {
                    console.error("Error fetching products:", error);
                    hasMore = false;
                }
            }

            return {'products':allProducts,'offset':offset};
        }

        // Call function on form submit
        $('.et-woo-product-index').on('submit', function (e) {
            e.preventDefault();

            let $form = $(this);

            if (!$form.hasClass('loading')) {
                $form.addClass('loading');
                $form.find('button').attr('disabled', 'disabled').text(admin_opt.indexLabel);

                loadAllProducts().then($return => {

                    const options = { 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric', 
                    };

                    const currentDate = new Date().toLocaleDateString('en-US', options);

                    $form.find('.index-stats').html('Last index: '+$return.offset+' products at '+currentDate);

                    $form.removeClass('loading');
                    $form.find('button').removeAttr('disabled').text(admin_opt.reindexLabel);
                }).catch(error => {
                    console.error("Error loading products:", error);
                    $form.removeClass('loading');
                    $form.find('button').removeAttr('disabled').text(admin_opt.reindexLabel);
                });
            }
        });

        $('form[name="save_product_index_settings"]').on('submit', function(e) {
            e.preventDefault(); // Prevent default form submission

            var form     = $(this);
            var formData = form.serialize() + '&action=save_product_index_settings'; // Add the action parameter

            let originalText = form.find('.button').text();

            form.find('.button').attr('disabled','disabled').text(admin_opt.saving);

            $.ajax({
                url: admin_opt.adminAjax, // WordPress AJAX URL
                type: 'POST',
                data: formData,
                success: function(response) {

                    if (response) {
                        response = JSON.parse(response);

                        form.find('.button').removeAttr('disabled').text(originalText);

                        if (response.hasOwnProperty('output') && !form.find('.updated').length) {
                            $(response.output).insertAfter(form.find('.button'));
                            setTimeout(function(){
                                form.find('.updated').remove();
                            },1000);
                        }

                        console.log(response);
                    }
                },
                error: function(xhr, status, error) {
                    console.log(error); // Log any error if the request fails
                }
            });
        });


        $('#automage_product_index').on('click',function(){
            if ($(this).is(":checked")) {
                $('.form-field.interval').show();
            } else {
                $('.form-field.interval').hide();
            }
        });

        if ($('#automage_product_index').is(":checked")) {
            $('.form-field.interval').show();
        } else {
           $('.form-field.interval').hide();
        }


    })( jQuery );

/* Posts
----*/

    (function($){

        "use strict";

        function formatSwitch($value){
            if ($value == "link") {
                $('#_enovathemes_addons_post_options_metabox').show(0);
                $('#enovathemes_addons_post_options_metabox').show(0);
                $('.link-format').show(0);
                $('.post-data:not(.link-format)').hide(0);
            }else
            if ($value == "status") {
                $('#_enovathemes_addons_post_options_metabox').show(0);
                $('#enovathemes_addons_post_options_metabox').show(0);
                $('.status-format').show(0);
                $('.post-data:not(.status-format)').hide(0);
            }else
            if ($value == "quote") {
                $('#_enovathemes_addons_post_options_metabox').show(0);
                $('#enovathemes_addons_post_options_metabox').show(0);
                $('.quote-format').show(0);
                $('.post-data:not(.quote-format)').hide(0);
            }else
            if ($value == "gallery") {
                $('#_enovathemes_addons_post_options_metabox').show(0);
                $('#enovathemes_addons_post_options_metabox').show(0);
                $('.gallery-format').show(0);
                $('.post-data:not(.gallery-format)').hide(0);
            }else
            if ($value == "audio") {
                $('#_enovathemes_addons_post_options_metabox').show(0);
                $('#enovathemes_addons_post_options_metabox').show(0);
                $('.audio-format').show(0);
                $('.post-data:not(.audio-format)').hide(0);
            }else
            if ($value == "video") {
                $('#_enovathemes_addons_post_options_metabox').show(0);
                $('#enovathemes_addons_post_options_metabox').show(0);
                $('.video-format').show(0);
                $('.post-data:not(.video-format)').hide(0);
            }else {
                $('.post-data').hide(0);
                $('#_enovathemes_addons_post_options_metabox').hide(0);
                $('#enovathemes_addons_post_options_metabox').hide(0);
            }
        }

        $('#formatdiv input[type="radio"]').each(function(){
            var $this = $(this);

            $this.on('click', function(){
                formatSwitch($this.val());
            });

            if($this.is(":checked")){
                formatSwitch($this.val());
            }
        });

        setTimeout(function(){
            formatSwitch($('#post-format-selector-0').val());
        },1000);

        $('body').on('change','#post-format-selector-0',function(){
            formatSwitch($('#post-format-selector-0').val());
        });

    })(jQuery);

/* Sortable
----*/

    (function( $ ) {

        "use strict";

        var filterText = JSON.parse(admin_opt.filterText);

        function updateAttributes($this){

            $this.closest('form').find('input[name="savewidget"]').removeAttr('disabled');

            var atts = [];

            var attributes = $this.closest('.widget-product-filter').find('.sortable li');

            attributes.each(function(index){
                atts.push(JSON.parse($(this).attr('data-attribute')));
            });

            $this.closest('.widget-product-filter').find('input.atts').val(JSON.stringify(atts));
        }


        function removeAttribute($this){

            $this.find('.sortable li').each(function(){

                var li = $(this);

                li.find('.remove').on('click',function(){
                    li.remove();
                    updateAttributes($this);
                });
            });
        }

        function setAttributeOptions($this){
            $this.find('.sortable li').each(function(){
                var li = $(this);

                li.find('select.dis').on('change',function(){
                    var att = li.attr('data-attribute');
                    att = JSON.parse(att);

                    var val = $(this).val(),
                        col = $(this).parent().next('.image-on');

                    if (val == 'image') {
                       col.show(0);
                       att['column'] = col.find('select').val();
                    } else {
                        col.hide(0);
                        att['column'] = '2';
                    }

                    att['display'] = val;

                    li.attr('data-attribute',JSON.stringify(att));
                    updateAttributes($this);
                });

                li.find('.image-on select').on('change',function(){
                    li.find('select.dis').trigger('change');
                });

                li.find('select.cats').on('change',function(){

                    var att = li.attr('data-attribute');
                    att = JSON.parse(att);

                    var val = $(this).val(),
                        next = $(this).parent().next('.include');

                    var containsNonEmpty = val.some(function(element) {
                        return element !== '' && (Array.isArray(element) ? element.length > 0 : true);
                      });

                    if (containsNonEmpty) {
                       next.show(0);
                       att['category'] = val;
                    } else {
                       next.hide(0);
                       att['category'] = '';
                    }

                    li.attr('data-attribute',JSON.stringify(att));
                    updateAttributes($this);

                });

                li.find('select.cats-hide').on('change',function(){

                    var att = li.attr('data-attribute');
                    att = JSON.parse(att);

                    var val = $(this).val(),
                        next = $(this).parent().next('.include');

                    var containsNonEmpty = val.some(function(element) {
                        return element !== '' && (Array.isArray(element) ? element.length > 0 : true);
                      });

                    if (containsNonEmpty) {
                       next.show(0);
                       att['category-hide'] = val;
                    } else {
                       next.hide(0);
                       att['category-hide'] = '';
                    }

                    li.attr('data-attribute',JSON.stringify(att));
                    updateAttributes($this);

                });

                li.find('input[name="children"]').on('click',function(){

                    var att = li.attr('data-attribute');
                    att = JSON.parse(att);

                    if(this.checked) {
                        att['children'] = 'true';
                    } else {
                        att['children'] = 'false';
                    }

                    li.attr('data-attribute',JSON.stringify(att));
                    updateAttributes($this);

                });

                li.find('input[name="children-hide"]').on('click',function(){

                    var att = li.attr('data-attribute');
                    att = JSON.parse(att);

                    if(this.checked) {
                        att['children-hide'] = 'true';
                    } else {
                        att['children-hide'] = 'false';
                    }

                    li.attr('data-attribute',JSON.stringify(att));
                    updateAttributes($this);

                });

                li.find('input[name="lock"]').on('click',function(){

                    var att = li.attr('data-attribute');
                    att = JSON.parse(att);

                    if(this.checked) {
                        att['lock'] = 'true';
                    } else {
                        att['lock'] = 'false';
                    }

                    li.attr('data-attribute',JSON.stringify(att));
                    updateAttributes($this);

                });

            });
        }

        function toggleAttribute($this){

            $this.find('.sortable li').each(function(){

                var li = $(this);

                li.find('.display').on('click',function(e){
                    e.stopImmediatePropagation();
                    li.toggleClass('active');
                });

            });
        }

        function widgetSortableToggle($this){

            $this.find('.draggable li')
            .draggable({
                connectToSortable: $this.find('.sortable'),
                helper: "clone",
                revert: "invalid",
                start: function( event, ui ) {
                    $this.parent().find('.sortable').addClass('highlight');
                },
                stop: function( event, ui ) {
                    $this.parent().find('.sortable').removeClass('highlight');

                    var target = $(event.target).attr('data-title');
                    if ($this.find('.sortable li[data-title="'+target+'"]').length  > 1) {
                        $this.find('.sortable li[data-title="'+target+'"]:first(:not(:only))').remove();
                    }

                    updateAttributes($this);

                }
            })
            .disableSelection();

            $this.find('.sortable')
            .sortable({
                stop: function( event, ui ) {
                    toggleAttribute($this);
                    setAttributeOptions($this);
                    removeAttribute($this);
                    updateAttributes($this);
                }
            })
            .disableSelection();

        }


        function buildAttributes($this){

            var attributes = $this.find('input.atts').val();

            if (attributes.length) {

                attributes = JSON.parse(attributes);

                for (var i = 0; i < attributes.length; i++) {

                    var attributeObject = attributes[i];
                    
                    var li = '<li data-attribute=\''+JSON.stringify(attributeObject)+'\' data-title="'+attributeObject['label']+'" class="draggable-item">'+attributeObject['label'];
                        li += '<span class="remove" title="'+filterText['remove']+'"></span>';
                    if (attributeObject['attr'] != 'price' && attributeObject['attr'] != 'rating') {
                        li += '<span class="display" title="'+filterText['display']+'"></span>';
                        li += '<div>';
                            if (attributeObject['attr'] != 'cat') {
                                li += '<label>'+filterText['limit']+'<select class="cats" multiple><option value="">'+filterText['all']+'</option>'+admin_opt.categories+'</select></label><label class="include"><input name="children" type="checkbox" value="true" />'+filterText['include']+'</label><br/><br/>';
                                li += '<label>'+filterText['hide']+'<select class="cats-hide" multiple><option value="">'+filterText['all']+'</option>'+admin_opt.categories+'</select></label><label class="include-hide"><input name="children-hide" type="checkbox" value="true" />'+filterText['include']+'</label><br/><br/>';
                            }
                            li += '<label>'+filterText['display']+'';
                            li += '<select class="dis">';
                                li += '<option value="select">'+filterText['select']+'</option>';
                                li += '<option value="list">'+filterText['list']+'</option>';
                                li += '<option value="image">'+filterText['image']+'</option>';
                                if (attributeObject['attr'] == 'cat') {
                                    li += '<option value="image-list">'+filterText['image-list']+'</option>';
                                }
                                if (attributeObject['attr'] != 'cat') {
                                    li += '<option value="label">'+filterText['label']+'</option>';
                                    li += '<option value="col">'+filterText['color']+'</option>';
                                    li += '<option value="slider">'+filterText['slider']+'</option>';
                                }
                            li += '</select></label>';
                            li += '<label class="image-on">'+filterText['columns'];
                            li += '<select>';
                                li += '<option value="2">2</option>';
                            li += '</select></label>';
                            if (attributeObject['attr'] != 'cat') {
                                li += '<p>'+filterText['desc1']+'</p>';
                            } else {
                                li += '<p>'+filterText['desc2']+'</p>';
                            }
                            li += '<br><label class="lock"><input name="lock" type="checkbox" value="true">'+filterText['lock']+'</label>';
                            li += '<p>'+filterText['lock-desk']+'</p>';
                        li += '</div>';
                    }
                    li += '</li>';


                    $this.find('.sortable').append(li);

                    let list = $this.find('.sortable li');
                    list = $.unique( list );
                    $this.find('.sortable').html(list);

                    
                }

                $this.find('.sortable li').each(function(){

                    var $this           = $(this),
                        attributeObject = JSON.parse($this.attr('data-attribute')),
                        display         = (attributeObject['display']) ? attributeObject['display'] : '',
                        lock            = (attributeObject['lock']) ? attributeObject['lock'] : 'false',
                        column          = (attributeObject['column']) ? attributeObject['column'] : '2',
                        category        = (attributeObject['category']) ? attributeObject['category'] : '',
                        children        = (attributeObject['children']) ? attributeObject['children'] : 'false',
                        category_hide   = (attributeObject['category-hide']) ? attributeObject['category-hide'] : '',
                        children_hide   = (attributeObject['children-hide']) ? attributeObject['children-hide'] : 'false';

                    if (display) {
                        if (display == 'image') {
                            $this.find('.image-on').show(0);
                            $this.find('.image-on select option[value="'+column+'"]').attr("selected","selected");
                        } else {
                            $this.find('.image-on').hide(0);
                        }
                        $this.find('option[value="'+display+'"]').attr("selected","selected");
                    }

                    if (category) {
                        $this.find('label.include').show(0);
                        if (Array.isArray(category)) {
                            for (var i = 0; i <= category.length; i++) {
                                $this.find('select.cats').find('option[value="'+category[i]+'"]').attr("selected","selected");
                            }
                        } else {
                            $this.find('select.cats').find('option[value="'+category+'"]').attr("selected","selected");
                        }
                        if (children == 'true') {
                            $this.find('input[name="children"]').attr('checked','checked');
                        }
                    }

                    if (lock == 'true') {
                        $this.find('input[name="lock"]').attr('checked','checked');
                    }

                    if (category_hide) {

                        $this.find('label.include-hide').show(0);
                        if (Array.isArray(category_hide)) {
                            for (var i = 0; i <= category_hide.length; i++) {
                                $this.find('select.cats-hide').find('option[value="'+category_hide[i]+'"]').attr("selected","selected");
                            }
                        } else {
                           $this.find('select.cats-hide').find('option[value="'+category_hide+'"]').attr("selected","selected");
                        }
                        if (children_hide == 'true') {
                            $this.find('input[name="children-hide"]').attr('checked','checked');
                        }
                    }

                });

            }
        }

        function widgetSortable(){

            $('.widget-product-filter').each(function(){

                var $this = $(this);

                widgetSortableToggle($this);
                buildAttributes($this);
                toggleAttribute($this);
                setAttributeOptions($this);
                removeAttribute($this);

            });

        }

        widgetSortable();

        $( document ).ajaxComplete(function( event, xhr, settings ) {

            if (settings['type'] != 'POST') {return;}

            /* Prepare settings
            /*-------------*/

                var data = decodeURIComponent(settings['data']);

                data = data.split("&");

                var dataObj = [{}];

                for (var i = 0; i < data.length; i++) {
                    var property = data[i].split("=");
                    var key      = (property[0]);
                    var value    = (property[1]);
                    dataObj[key] = value;
                }

                if(dataObj['action'] == "save-widget" && dataObj['id_base'] == "product_filter_widget"){
                    widgetSortable();
                }

        });

    })( jQuery );

/* Header options
----*/

    (function($){

        "use strict";

        function toggleHeader(selected){
            switch(selected){
                case "sidebar":
                    $('.sidebar-off').hide(0);
                    $('.sidebar-on').show(0);
                break;
                case "desktop":
                    $('.sidebar-on').hide(0);
                    $('.sidebar-off').show(0);
                    $('.desktop-on').show(0);
                break;
                case "mobile":
                    $('.sidebar-off').show(0);
                    $('.sidebar-on').hide(0);
                    $('.desktop-on').hide(0);
                break;
            }
        }

        var selected = $('#enovathemes_addons_header_options_metabox select[name="enovathemes_addons_header_type"] option:selected').val();

        toggleHeader(selected)

        $('#enovathemes_addons_header_options_metabox select[name="enovathemes_addons_header_type"]').on('change', function(){

            selected = $(this).find("option:selected").val();

            toggleHeader(selected)

        });

        if ($('#enovathemes_addons_header_options_metabox select[name="enovathemes_addons_header_type"] option:selected').val() == 'desktop' || $('#enovathemes_addons_header_options_metabox select[name="enovathemes_addons_header_type"] option:selected').val() == 'sidebar') {
            $('#enovathemes_addons_header_options_metabox input[name="enovathemes_addons_desktop"]').attr('checked','checked');
        }

        if ($('#enovathemes_addons_header_options_metabox select[name="enovathemes_addons_header_type"] option:selected').val() == 'mobile') {
            $('#enovathemes_addons_header_options_metabox input[name="enovathemes_addons_desktop"]').removeAttr('checked','');
        }

        $('#enovathemes_addons_header_options_metabox select[name="enovathemes_addons_header_type"]').on('change',function(){
            if ($(this).val() == 'mobile') {
                $('#enovathemes_addons_header_options_metabox input[name="enovathemes_addons_desktop"]').removeAttr('checked','');
            } else
            if ($(this).val() == 'desktop' || $(this).val() == 'sidebar') {
                $('#enovathemes_addons_header_options_metabox input[name="enovathemes_addons_desktop"]').attr('checked','checked');
            }
        });

    })(jQuery);

/* Vehicles
----*/

    (function($){

        "use strict";

        function getParams() {

            var url = window.location.href;
                url = url.split('?');

            var query = url[1];
            var params = new Object;

            if (typeof(query) != 'undefined' && query != null) {
                var vars = query.split('&');
                for (var i = 0; i < vars.length; i++) {
                    var pair = vars[i].split('=');
                    params[pair[0]] = decodeURIComponent(pair[1]);
                }
                return (jQuery.isEmptyObject(params)) ? false : params;
            }

            return false;
        }

        /* Import
        ----*/

            $('.taxonomy-vehicles input[type="submit"]').on('click',function(){

                let vehicle_data = $('#vehicle_data');

                var vehicle = {};

                var vehicleDataInput = $('#cmb2-metabox-vehicle_data .cmb-td input').each(function(){
                    
                    var $this = $(this);
                    
                    if($this.val()){
                        var $name = $this.attr('name');
                        vehicle[$name.replace("vehicle_", '')] = $this.val();
                    }
                });

                if (!$.isEmptyObject(vehicle)) {
                    
                    if(vehicle.hasOwnProperty('year')){

                        let vehicleYear = vehicle['year'];
                        let years = [];

                        if (vehicleYear.includes('-')) {
                            var period = vehicleYear.split('-');
                            for (var i=period[0]; i <= period[1]; i++) {
                                years.push(i.toString());
                            }
                        // Comma used
                        } else if (vehicleYear.includes(',')) {
                            var period = vehicleYear.split(',');
                            for (var i = 0; i < period.length; i++) {
                                years.push(period[i].toString());
                            }
                        } else {
                            years.push(vehicleYear);
                        }

                        years.sort();

                        if (years.length) {
                            $('#vehicle_year_formated').val(JSON.stringify(years));
                        }
                        
                    }

                    vehicle_data.val(JSON.stringify(vehicle));

                    let vehicleValues = Object.keys(vehicle).map(val => vehicle[val]);

                    $('#tag-name').val(vehicleValues.join(', '));
                    
                }
            });


            function isCSV(url) {
              return /\.(csv)$/.test(url);
            }

            function rebuildDisabledOptions() {
                // collect chosen (non-empty) values
                const chosen = new Set();
                $('section.csv-map select[name="map_to"]').each(function () {
                  const v = $(this).val();
                  if (v) chosen.add(v);
                });

                // for every select, disable options chosen elsewhere, keep its own selection enabled
                $('section.csv-map select[name="map_to"]').each(function () {
                  const $sel = $(this);
                  const myVal = $sel.val();

                  $sel.find('option').each(function(){
                    const val = $(this).attr('value') || '';
                    if (!val) { // keep empty option always enabled
                      $(this).prop('disabled', false);
                      return;
                    }
                    // disable if chosen by someone else
                    if (chosen.has(val) && val !== myVal) {
                      $(this).prop('disabled', true);
                    } else {
                      $(this).prop('disabled', false);
                    }
                  });
                });
            }

            // initial run + on change
            rebuildDisabledOptions();
            $('body').on('change','section.csv-map select[name="map_to"]', rebuildDisabledOptions);

            $('.import-vehicles').on('submit',function(e){

                e.preventDefault();

                let $form = $(this),form = this;

                if ($form.find('section.csv-import').length) {

                    let csv  = $form.find('#csv').val();

                    if (csv.length && isCSV(csv)) {

                        $form.addClass('loading');

                        $.ajax({
                            type: 'POST',
                            url: admin_opt.ajaxUrl,
                            contentType: false,
                            processData: false,
                            data: new FormData(this),
                            success: function(data) {
                                data = JSON.parse(data);

                                $form.removeClass('loading');

                                if (data['html']) {
                                    $form.html(data['html']);
                                    $form.parents().find('.wc-progress-steps li:first-child').removeClass('active').addClass('done');
                                    $form.parents().find('.wc-progress-steps li:nth-child(2)').addClass('active');
                                }
                            },
                            error: function(data) {
                                alert(admin_opt.adminAJAXError);
                            }
                        });

                    } else {
                        alert(admin_opt.csvError);
                    }
                } else if($form.find('section.csv-map').length) {

                    let map = {};

                    $form.find('tr').each(function(){
                        let tr = $(this);
                        if (tr.find('select[name="map_to"]').val()) {
                            map[tr.find('td:first-child').attr('data-column')] = tr.find('select[name="map_to"]').val();
                        }
                    });

                    if (!$.isEmptyObject(map)) {
                        $form.find('#map').val(JSON.stringify(map));

                        $form.parents().find('.wc-progress-steps li:nth-child(2)').removeClass('active').addClass('done');
                        $form.parents().find('.wc-progress-steps li:nth-child(3)').addClass('active');

                        $.ajax({
                            type: 'POST',
                            url: admin_opt.ajaxUrl,
                            contentType: false,
                            cache:false,
                            processData: false,
                            data: new FormData(this),
                            beforeSend: function(){
                                $form.find('.import-actions').hide();
                                $form.find('header h2').html(admin_opt.importTitle);
                                $form.find('header p').html(admin_opt.importDescription);
                                $form.find('section').html('<div class="progress"></div>');
                            },
                            success: function(data) {

                                $form.parents().find('.wc-progress-steps li:nth-child(3)').removeClass('active').addClass('done');
                                $form.parents().find('.wc-progress-steps li:nth-child(4)').addClass('active');

                                data = JSON.parse(data);

                                let header = '<h2>'+ admin_opt.importComplete + '</h2>',
                                    done = data['done'],
                                    vehiclesCount = (parseInt(done) <= 1) ? '1 vehicle imported' : done + ' vehicles imported';

                                    $form.find('header').html(header);
                                    $form.find('.import-actions').html(data['taxonomy-link']);
                                    $form.find('.import-actions').show();
                                    $form.find('section').html('<div class="import-complete"></div><p>'+ vehiclesCount + '</p>');

                            },
                            error: function(data) {
                                alert(admin_opt.adminAJAXError);
                            }
                        });

                    } else {
                        alert(admin_opt.mapError)
                    }

                }


            });
        
        /* Single product
        ----*/


            function clearResults(inside){
                inside.removeClass('loading');
                inside.find('.search-results').empty().addClass('empty');
                inside.find('.table-wrapper').removeClass('active');
                inside.find('.vehicle-reset').remove();
            }

            function clearFilter(inside){
                inside.find('select').val('').trigger('change.select2');
                inside.find('.vehicle-reset').remove();
            }

            function actionVisibility(inside){
                if (inside.find('input[type="checkbox"]:checked').length) {
                    inside.find('tfoot').removeClass('hidden');
                } else {
                    inside.find('tfoot').addClass('hidden');
                }
            }

            function toggleVehiclesMetabox(universal,inside){
                if (universal) {

                    $('#enovathemes_addons_products_vehicles_metabox').addClass("hidden");

                    clearResults(inside);
                    clearFilter(inside);

                } else {
                    $('#enovathemes_addons_products_vehicles_metabox').removeClass("hidden");
                }
            }

            function vehicleSearch(inside,data){

                let postData = {};

                postData['action'] = 'fetch_product_vehicles';
                postData['attributes'] = JSON.stringify(data);

                $.ajax({
                    type: 'POST',
                    url: admin_opt.ajaxUrl,
                    data: postData,
                    success: function(output) {

                        if (output) {

                            output = JSON.parse(output);

                            console.log(output);

                            if (!inside.find('.search-results').hasClass('empty')) {

                                inside.removeClass('loading');
                                if (!inside.find('a.vehicle-reset').length) {
                                    inside.prepend('<a href="" class="vehicle-reset">'+admin_opt.vehicleReset+'</a><span class="et-clearfix"></span>');
                                }
                                if (output['html']) {
                                    inside.find('.table-wrapper').addClass('active');
                                    inside.find('.search-results').html(output['html']);
                                } else {
                                    inside.find('.search-results').html('<tr><td class="no-results">'+admin_opt.noVehicles+'</td></tr>');
                                }

                                actionVisibility(inside);

                            }

                            
                            if (output['next']) {

                                if (inside.find('select[name="'+data['next']+'"]').length) {
                                    inside.find('select[name="'+data['next']+'"]').html(output['next']);
                                } else if(inside.find('select[name="'+data['next']+'[]"]')){
                                    inside.find('select[name="'+data['next']+'[]"]').html(output['next']);
                                }

                            }

                            // if (output['dev']) {
                            //     console.log(output['dev']);
                            // }

                        } else {
                            clearResults(inside);
                        }

                    },
                    error: function(data) {
                        alert(admin_opt.adminAJAXError);
                    }
                });
            }

            function fetchFilterData(inside,post_id) {
                    $.ajax({
                    type: 'POST',
                    url: admin_opt.ajaxUrl,
                    data: {
                        'action':'fetch_vehicles_params',
                        'post_id':post_id,
                    },
                    success: function(data) {

                        let output = JSON.parse(data);

                        if (!$('#enovathemes_addons_products_vehicles_metabox .inside input.vehicle-param').length && output['form']) {

                            $('#enovathemes_addons_products_vehicles_metabox .inside .vehicle-admin-filter').remove();
                            $('#enovathemes_addons_products_vehicles_metabox .inside .vehicle-reset').remove();
                            $('#enovathemes_addons_products_vehicles_metabox .inside .et-clearfix').remove();
                            $('#enovathemes_addons_products_vehicles_metabox .inside .vehicle-product-inactive').remove();
                            
                            $('#enovathemes_addons_products_vehicles_metabox .inside')
                            .prepend(output['form']);

                            $('#enovathemes_addons_products_vehicles_metabox select').each(function(){
                                let placeholder = $(this).attr('data-placeholder');
                                if ($(this).eq(0)) {
                                    $(this).select2({
                                        placeholder:placeholder,
                                        allowClear: true
                                    });
                                } else {
                                    $(this).select2({
                                        multiple: true,
                                        placeholder:placeholder,
                                        allowClear: true
                                    });
                                }
                            });
                        }

                        if (output['html']) {
                            inside.find('.table-wrapper').addClass('active');
                            inside.find('.search-results').html(output['html']);
                        } else {
                            clearResults(inside);
                        }

                        inside.removeClass('loading');

                        actionVisibility(inside);

                    },
                    error: function(data) {
                        alert(admin_opt.adminAJAXError);
                    }
                });
            }

            function vehicleAssign(inside,data){

                inside.addClass('loading');

                data['action'] = 'assign_product_vehicles';

                $.ajax({
                    type: 'POST',
                    url: admin_opt.ajaxUrl,
                    data: data,
                    success: function(output) {

                        let activeParams = getParams();
                        if (activeParams['post']) {
                            fetchFilterData(inside,activeParams['post']);
                        } else if($('.vehicle-bulk-assign').length){
                            fetchFilterDataBulk($('.vehicle-bulk-assign'),true,data['products']);
                        }

                    },
                    error: function(data) {
                        alert(admin_opt.adminAJAXError);
                    }
                });
            }


            if($('#enovathemes_addons_products_vehicles_metabox').length){

                let activeParams = getParams();

                $('#enovathemes_addons_products_vehicles_metabox .inside')
                .append('<div class="table-wrapper"><table class="search-results" /></div>');

                let inside = $('#enovathemes_addons_products_vehicles_metabox .inside');

                if (activeParams['post']) {
                    fetchFilterData(inside,activeParams['post']);
                } else {
                    inside.append('<div class="vehicle-product-inactive">'+admin_opt.inactiveProductVehicle+'</div>')
                }

                // Filter param on change

                $(document).on('change', "select.vehicle-param", function(e){

                    inside.find('.table-wrapper').removeClass('active');
                    inside.find('.search-results').html('');
                    inside.find('.search-results').removeClass('empty');
                    inside.addClass('loading');

                    let $this = $(this),
                        data = {},
                        next = $this.parents('.select-wrapper').next().find('select').attr('name').replace(/\[\]$/, '');

                    data['post_id'] = activeParams['post'];

                    if (typeof(next) != 'undefined' && next != null) {
                        data['next'] = next;
                    }

                    if ($this.parent().is(':first-child')) {
                        $this.parents('.vehicle-admin-filter').find('select').not($this).val('').trigger('change.select2');
                    }

                    $this.parent().nextAll().find('select').val('').trigger('change.select2');


                    $this.parents('.vehicle-admin-filter').find('select').each(function(){

                        let val = $(this).val();

                        if (Array.isArray(val)) {
                          // Remove empty strings and trim spaces
                          val = val.map(v => v.trim()).filter(v => v !== '');
                          
                          // If it becomes empty array, treat as null
                          if (val.length === 0) {
                            val = null;
                          }
                        } else {
                          // Single value field
                          val = (val || '').trim();
                          if (val === '') val = null;
                        }

                        if (val) {
                            data[$(this).attr('name').replace(/\[\]$/, '')] = val;
                        }

                    });


                    if(!$.isEmptyObject(data)){
                        vehicleSearch(inside,data);
                    } else {
                       clearResults(inside);
                    }

                });

                // Vehicle assign action

                $(document).on('click', ".vehicle-assign-action", function(e){

                    e.preventDefault();

                    let $this  = $(this),
                        data   = {},
                        assign = [],
                        unsign = [];

                    data['nonce'] = $this.parent().find('input[name="assign-nonce"]').val();
                    data['post_id'] = activeParams['post'];

                    inside.find('.search-results tbody input[type="checkbox"]:checked').each(function(){
                        assign.push($(this).val());
                    });

                    inside.find('.search-results tbody input[type="checkbox"]:not(:checked)').each(function(){
                        unsign.push($(this).val());
                    });

                    if (assign.length) {
                        data['assign'] = JSON.stringify(assign);
                    }

                    if (unsign.length) {
                        data['unsign'] = JSON.stringify(unsign);
                    }

                    vehicleAssign(inside,data);


                });

            
                // Reset

                $(document).on('click', ".vehicle-reset", function(e){
                    e.preventDefault();

                    inside.find('.table-wrapper').removeClass('active');
                    inside.find('.search-results').html('');
                    inside.find('.search-results').removeClass('empty');
                    inside.addClass('loading');

                    inside.find('select').val('').trigger('change.select2');

                    clearResults(inside);

                    $(this).remove();
                });


                // Checkboxes click

                $(document).on('click', 'input[name="all"]', function(){
                    inside.find('.search-results tbody input[type="checkbox"]').prop('checked',this.checked);
                });

                $(document).on('click', '.search-results input[type="checkbox"]', function(){

                    if (!$(this).is(':checked')) {
                        inside.find('.search-results input[name="all"]').prop('checked',false);
                    }

                    actionVisibility(inside);
                    

                });
                
                $('#enovathemes_addons_universal').on('click',function(){
                    toggleVehiclesMetabox(this.checked,inside);
                });

                if($('#enovathemes_addons_universal:checked').length){
                    toggleVehiclesMetabox(true,inside);
                }
            }

        /* Bulk vehicles assgn
        ----*/


            function fetchFilterDataBulk(inside,assign = false,products) {
                    $.ajax({
                    type: 'POST',
                    url: admin_opt.ajaxUrl,
                    data: {
                        'action':'fetch_vehicles_params',
                        'products':products,
                        'form':1,
                    },
                    success: function(data) {

                        let output = JSON.parse(data);

                        if (output['form']) {

                            inside
                            .removeClass('loading')
                            .addClass('full');

                            inside.find('form.vehicle-admin-filter').remove();
                            inside.find('.vehicle-reset').remove();
                            inside.find('.table-wrapper').remove();
                            inside.find('.et-clearfix').remove();

                            if (inside.find('.assigned').length) {
                                inside.find('.assigned').remove();
                            }
                            if (!inside.find('form').length) {
                                inside.prepend(output['form']);
                                inside.append('<div class="table-wrapper"><table class="search-results" /></div>');
                            }

                            if (output['html']) {
                                inside.find('.search-results').prepend(output['html']);

                                if (inside.find('.vehicle-tr').length) {
                                    inside.find('thead').removeClass('hidden');

                                    if (inside.find('input[type="checkbox"]:checked').length) {
                                        inside.find('tfoot').removeClass('hidden');
                                    } else {
                                        inside.find('tfoot').addClass('hidden');
                                    }
                                }
                            }

                            inside.find('select').each(function(){
                                let placeholder = $(this).attr('data-placeholder');
                                if ($(this).eq(0)) {
                                    $(this).select2({
                                        placeholder:placeholder,
                                        allowClear: true
                                    });
                                } else {
                                    $(this).select2({
                                        multiple: true,
                                        placeholder:placeholder,
                                        allowClear: true
                                    });
                                }
                            });

                        }

                    },
                    error: function(data) {
                        alert(admin_opt.adminAJAXError);
                    }
                });
            }


            function vehicleBulkAssign(inside,products){

                // Filter param on change
                $(document).on('change', "select.vehicle-param", function(e){

                    inside.find('.table-wrapper').removeClass('active');
                    inside.find('.search-results').html('');
                    inside.find('.search-results').removeClass('empty');
                    inside.addClass('loading');

                    let $this = $(this),
                        data = {},
                        next = $this.parents('.select-wrapper').next().find('select').attr('name').replace(/\[\]$/, '');

                    if (typeof(next) != 'undefined' && next != null) {
                        data['next'] = next;
                    }

                    if ($this.parent().is(':first-child')) {
                        $this.parents('.vehicle-admin-filter').find('select').not($this).val('').trigger('change.select2');
                    }

                    $this.parent().nextAll().find('select').val('').trigger('change.select2');


                    $this.parents('.vehicle-admin-filter').find('select').each(function(){

                        let val = $(this).val();

                        if (Array.isArray(val)) {
                          // Remove empty strings and trim spaces
                          val = val.map(v => v.trim()).filter(v => v !== '');
                          
                          // If it becomes empty array, treat as null
                          if (val.length === 0) {
                            val = null;
                          }
                        } else {
                          // Single value field
                          val = (val || '').trim();
                          if (val === '') val = null;
                        }

                        if (val) {
                            data[$(this).attr('name').replace(/\[\]$/, '')] = val;
                        }

                    });


                    if(!$.isEmptyObject(data)){
                        vehicleSearch(inside,data);
                    } else {
                       clearResults(inside);
                    }

                });

                // Vehicle assign action

                $(document).on('click', ".vehicle-assign-action", function(e){

                    e.preventDefault();

                    let $this  = $(this),
                        data   = {},
                        assign = [],
                        unsign = [];

                    data['nonce'] = $this.parent().find('input[name="assign-nonce"]').val();
                    data['products'] = products;

                    inside.find('.search-results tbody input[type="checkbox"]:checked').each(function(){
                        assign.push($(this).val());
                    });

                    inside.find('.search-results tbody input[type="checkbox"]:not(:checked)').each(function(){
                        unsign.push($(this).val());
                    });

                    if (assign.length) {
                        data['assign'] = JSON.stringify(assign);
                    }

                    if (unsign.length) {
                        data['unsign'] = JSON.stringify(unsign);
                    }

                    vehicleAssign(inside,data);


                });

            
                // Reset

                $(document).on('click', ".vehicle-reset", function(e){
                    e.preventDefault();

                    inside.find('.table-wrapper').removeClass('active');
                    inside.find('.search-results').html('');
                    inside.find('.search-results').removeClass('empty');
                    inside.addClass('loading');

                    inside.find('select').val('').trigger('change.select2');

                    clearResults(inside);

                    $(this).remove();
                });


                // Checkboxes click

                $(document).on('click', 'input[name="all"]', function(){
                    inside.find('.search-results tbody input[type="checkbox"]').prop('checked',this.checked);
                });

                $(document).on('click', '.search-results input[type="checkbox"]', function(){

                    if (!$(this).is(':checked')) {
                        inside.find('.search-results input[name="all"]').prop('checked',false);
                    }

                    actionVisibility(inside);
                    

                });
            }

            function bulkVehicleAssign(products){
                $('body').prepend('<div class="vehicle-bulk-assign-wrapper"><div class="vehicle-bulk-assign loading"><div class="vehicle-bulk-assign-close"></div></div></div>');
                fetchFilterDataBulk($('.vehicle-bulk-assign'),false,products);
                vehicleBulkAssign($('.vehicle-bulk-assign'),products);
            };

            $('body').on('click', '.vehicle-bulk-assign-close', function () {
                $('.vehicle-bulk-assign-wrapper').fadeOut(100, function () {
                    $(this).remove();
                });
            });

            if (   $('body').hasClass('edit-php') && $('body').hasClass('post-type-product') &&
                $('.wp-list-table tr').length
            ) {
                $('<option value="bulk-vehicle-assign" class="hide-if-no-js">'+admin_opt.BulkVehicleAssign+'</option>').insertAfter($('#bulk-action-selector-top option[value="edit"]'));

                $('#doaction').on('click',function(e){
                    if ($('#bulk-action-selector-top').val() == 'bulk-vehicle-assign') {
                        e.preventDefault();

                        var products = [];

                        $('.wp-list-table tbody .check-column > input[type="checkbox"]:checked').each(function(){
                            products.push($(this).val());
                        });

                        if (products.length) {
                            bulkVehicleAssign(products);
                        }
                    }
                });
            }

    })(jQuery);

    /* Sortable widget-product-vehicle-filter
    ----*/

        (function( $ ) {

            "use strict";

            var filterText = JSON.parse(admin_opt.filterText);

            function updateAttributes($this){

                $this.closest('form').find('input[name="savewidget"]').removeAttr('disabled');

                var atts = [];

                var attributes = $this.closest('.widget-product-vehicle-filter').find('.sortable li');

                attributes.each(function(index){

                    var label    = $(this).find('input').val(),
                        dataAttr = false;

                    if (label.length) {
                        dataAttr = $(this).attr('data-attribute');
                        dataAttr = JSON.parse(dataAttr);

                        dataAttr['label'] = label;

                        dataAttr = JSON.stringify(dataAttr);

                    } else {
                        dataAttr = $(this).attr('data-attribute')
                    }

                    if (dataAttr) {
                        atts.push(JSON.parse(dataAttr));
                    }

                });

                $this.closest('.widget-product-vehicle-filter').find('input.atts').val(JSON.stringify(atts));
            }


            function removeAttribute($this){

                $this.find('.sortable li').each(function(){

                    var li = $(this);

                    li.find('.remove').on('click',function(){
                        li.remove();
                        updateAttributes($this);
                    });
                });
            }

            function widgetSortableToggle($this){

                $this.find('.draggable li')
                .draggable({
                    connectToSortable: $this.find('.sortable'),
                    helper: "clone",
                    revert: "invalid",
                    start: function( event, ui ) {
                        $this.parent().find('.sortable').addClass('highlight');
                    },
                    stop: function( event, ui ) {
                        $this.parent().find('.sortable').removeClass('highlight');

                        var target = $(event.target).attr('data-title');
                        if ($this.find('.sortable li[data-title="'+target+'"]').length  > 1) {
                            $this.find('.sortable li[data-title="'+target+'"]:first(:not(:only))').remove();
                        }

                        updateAttributes($this);

                    }
                })
                .disableSelection();

                $this.find('.sortable')
                .sortable({
                    stop: function( event, ui ) {
                        removeAttribute($this);
                        updateAttributes($this);
                    }
                })
                .disableSelection();

            }

            function buildAttributes($this){

                var attributes = $this.find('input.atts').val();

                if (attributes.length) {

                    attributes = JSON.parse(attributes);

                    for (var i = 0; i < attributes.length; i++) {

                        var attributeObject = attributes[i];
                        
                        var li = '<li data-attribute=\''+JSON.stringify(attributeObject)+'\' data-title="'+attributeObject['label']+'" class="draggable-item">'+capitalizeFirstLetter(attributeObject['attr']);
                            li += '<span class="remove" title="'+filterText['remove']+'"></span>';
                            li += '<input type="text" name="label" value="'+attributeObject['label']+'" placeholder="'+filterText['label']+'">';
                            li += '</li>';

                        $this.find('.sortable').append(li);

                        let list = $this.find('.sortable li');
                        list = $.unique( list );
                        $this.find('.sortable').html(list);
                        
                    }
                }
            }

            function widgetColumns($this){
                let type = $this.find('.type').val();

                if (type == 'vertical') {
                    $this.find('.column option:not(.col1):not(.col2)').attr('disabled','disabled');
                } else {
                    $this.find('.column option').removeAttr('disabled');
                }
            }

            function widgetSortable(){

                $('body').on('keyup','.widget-product-vehicle-filter input[name="label"]',function(){

                    $(this).closest('form').find('input[name="savewidget"]').removeAttr('disabled');

                    var atts = [];

                    var attributes = $(this).closest('.widget-product-vehicle-filter').find('.sortable li');

                    attributes.each(function(index){

                        var label    = $(this).find('input').val(),
                            dataAttr = false;

                        if (label.length) {
                            dataAttr = $(this).attr('data-attribute');
                            dataAttr = JSON.parse(dataAttr);

                            dataAttr['label'] = label;

                            dataAttr = JSON.stringify(dataAttr);

                        } else {
                            dataAttr = $(this).attr('data-attribute')
                        }

                        if (dataAttr) {
                            atts.push(JSON.parse(dataAttr));
                        }

                    });

                    $(this).closest('.widget-product-vehicle-filter').find('input.atts').val(JSON.stringify(atts));

                });

                $('.widget-product-vehicle-filter').each(function(){

                    var $this = $(this);

                    $this.find('.type').on('change',function(){
                        widgetColumns($this);
                    });

                    widgetColumns($this);
                    widgetSortableToggle($this);
                    buildAttributes($this);
                    removeAttribute($this);

                });

            }

            widgetSortable();

            $( document ).ajaxComplete(function( event, xhr, settings ) {

                if (settings['type'] != 'POST') {return;}

                /* Prepare settings
                /*-------------*/

                    var data = decodeURIComponent(settings['data']);

                    data = data.split("&");

                    var dataObj = [{}];

                    for (var i = 0; i < data.length; i++) {
                        var property = data[i].split("=");
                        var key      = (property[0]);
                        var value    = (property[1]);
                        dataObj[key] = value;
                    }

                    if(dataObj['action'] == "save-widget" && dataObj['id_base'] == "product_vehicle_filter_widget"){
                        widgetSortable();
                    }

            });

        })( jQuery );

    /* Sortable widget-user-vehicle-filter
    ----*/

        (function( $ ) {

            "use strict";

            var filterText = JSON.parse(admin_opt.filterText);

            function updateAttributes($this){

                $this.closest('form').find('input[name="savewidget"]').removeAttr('disabled');

                var atts = [];

                var attributes = $this.closest('.widget-user-vehicle-filter').find('.sortable li');

                attributes.each(function(index){

                    var label    = $(this).find('input').val(),
                        dataAttr = false;

                    if (label.length) {
                        dataAttr = $(this).attr('data-attribute');
                        dataAttr = JSON.parse(dataAttr);

                        dataAttr['label'] = label;

                        dataAttr = JSON.stringify(dataAttr);

                    } else {
                        dataAttr = $(this).attr('data-attribute')
                    }

                    if (dataAttr) {
                        atts.push(JSON.parse(dataAttr));
                    }

                });

                $this.closest('.widget-user-vehicle-filter').find('input.atts').val(JSON.stringify(atts));
            }


            function removeAttribute($this){

                $this.find('.sortable li').each(function(){

                    var li = $(this);

                    li.find('.remove').on('click',function(){
                        li.remove();
                        updateAttributes($this);
                    });
                });
            }

            function widgetSortableToggle($this){

                $this.find('.draggable li')
                .draggable({
                    connectToSortable: $this.find('.sortable'),
                    helper: "clone",
                    revert: "invalid",
                    start: function( event, ui ) {
                        $this.parent().find('.sortable').addClass('highlight');
                    },
                    stop: function( event, ui ) {
                        $this.parent().find('.sortable').removeClass('highlight');

                        var target = $(event.target).attr('data-title');
                        if ($this.find('.sortable li[data-title="'+target+'"]').length  > 1) {
                            $this.find('.sortable li[data-title="'+target+'"]:first(:not(:only))').remove();
                        }

                        updateAttributes($this);

                    }
                })
                .disableSelection();

                $this.find('.sortable')
                .sortable({
                    stop: function( event, ui ) {
                        removeAttribute($this);
                        updateAttributes($this);
                    }
                })
                .disableSelection();

            }

            function buildAttributes($this){

                var attributes = $this.find('input.atts').val();

                if (attributes.length) {

                    attributes = JSON.parse(attributes);

                    for (var i = 0; i < attributes.length; i++) {

                        var attributeObject = attributes[i];
                        
                        var li = '<li data-attribute=\''+JSON.stringify(attributeObject)+'\' data-title="'+attributeObject['label']+'" class="draggable-item">'+capitalizeFirstLetter(attributeObject['attr']);
                            li += '<span class="remove" title="'+filterText['remove']+'"></span>';
                            li += '<input type="text" name="label" value="'+attributeObject['label']+'" placeholder="'+filterText['label']+'">';
                            li += '</li>';

                        $this.find('.sortable').append(li);

                        let list = $this.find('.sortable li');
                        list = $.unique( list );
                        $this.find('.sortable').html(list);
                        
                    }
                }
            }

            function widgetColumns($this){
                let type = $this.find('.type').val();

                if (type == 'vertical') {
                    $this.find('.column option:not(.col1):not(.col2)').attr('disabled','disabled');
                } else {
                    $this.find('.column option').removeAttr('disabled');
                }
            }

            function widgetSortable(){

                $('body').on('keyup','.widget-user-vehicle-filter input[name="label"]',function(){

                    $(this).closest('form').find('input[name="savewidget"]').removeAttr('disabled');

                    var atts = [];

                    var attributes = $(this).closest('.widget-user-vehicle-filter').find('.sortable li');

                    attributes.each(function(index){

                        var label    = $(this).find('input').val(),
                            dataAttr = false;

                        if (label.length) {
                            dataAttr = $(this).attr('data-attribute');
                            dataAttr = JSON.parse(dataAttr);

                            dataAttr['label'] = label;

                            dataAttr = JSON.stringify(dataAttr);

                        } else {
                            dataAttr = $(this).attr('data-attribute')
                        }

                        if (dataAttr) {
                            atts.push(JSON.parse(dataAttr));
                        }

                    });

                    $(this).closest('.widget-user-vehicle-filter').find('input.atts').val(JSON.stringify(atts));

                });

                $('.widget-user-vehicle-filter').each(function(){

                    var $this = $(this);

                    $this.find('.type').on('change',function(){
                        widgetColumns($this);
                    });

                    widgetColumns($this);
                    widgetSortableToggle($this);
                    buildAttributes($this);
                    removeAttribute($this);

                });

            }

            widgetSortable();

            $( document ).ajaxComplete(function( event, xhr, settings ) {

                if (settings['type'] != 'POST') {return;}

                /* Prepare settings
                /*-------------*/

                    var data = decodeURIComponent(settings['data']);

                    data = data.split("&");

                    var dataObj = [{}];

                    for (var i = 0; i < data.length; i++) {
                        var property = data[i].split("=");
                        var key      = (property[0]);
                        var value    = (property[1]);
                        dataObj[key] = value;
                    }

                    if(dataObj['action'] == "save-widget" && dataObj['id_base'] == "user_vehicle_filter_widget"){
                        widgetSortable();
                    }

            });

        })( jQuery );