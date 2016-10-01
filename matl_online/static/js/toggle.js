/* Plugin for a basic toggle complete with events
 *
 * Copyright 2016, Jonathan Suever */

( function ( $ ) {

    var ToggleButton = function(element, options) {
        this.$element = element;
        this.options = options;
        this.items = options.items;

        this.initialize();
    }

    DEFAULTS = {
        items: {}
    }

    ToggleButton.prototype.initialize = function() {
        this.$div = $('<div/>').addClass('btn-group');
        this.$button = $('<button/>').addClass('btn btn-default btn-xs dropdown-toggle')
            .attr('data-toggle', 'dropdown');

        this.$label = $('<span/>').addClass('dropdown-label')
            .text(this.items[0].label)

        this.$button.append(this.$label);
        this.$button.append('<span class="caret"></span>')

        this.$list = $('<ul/>').addClass('dropdown-menu pull-right')
            .attr('role', 'menu');

        var obj = this;

        $.each(this.items, function(index, item){
            var link = $('<a/>').text(item.label).data(item);
            var listitem = $('<li/>').append(link);
            obj.$list.append(listitem);
        });

        this.$div.append(this.$button)
        this.$div.append(this.$list);

        this.$element.append(this.$div);

        var obj = this;

        this.$element.find('.dropdown-menu li a').click(function(){
            obj.$label.text($(this).text());

            // Fire an event about the change
            obj.$label.trigger('toggleButton.select', $(this).data());
        });
    }

    $.fn.toggleButton = function(options) {
        options = $.extend({}, DEFAULTS, options);

        var obj = new ToggleButton(this, options);

        $(this).data('.toggle', obj);
        return $(this);
    }

} ( jQuery ));
