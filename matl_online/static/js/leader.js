/* jQuery / Bootstrap plugin for a basic leaderboard
 *
 * Copyright 2016, Jonathan Suever
 */

( function ( $ ) {

    var LeaderBoard = function(element, options) {
        this.$element = $(element);
        this.options = options;
        this.items = this.options.items;

        this.initialize();
        //this.key = options.default_key;

        var obj = this;

        $.each(this.items, function(index, item){
            var link = $('<a class="list-group-item leader-item"/>')
                .attr('target', '_blank')
                .data(item)
                .append('<span class="item-score pull-right"/>');


            if ( typeof obj.options.url == "function" ) {
                url = obj.options.url(item);
            } else {
                url = item[obj.options.url];
            }

            link.attr('href', url);

            if ( typeof obj.options.label == "string" ) {
                link.text(item[obj.options.label]);
            } else {
                link.append(obj.options.label(item));
            }

            link.appendTo(obj.$div);
        });

        // Do an initial sort
        this.sort(this.options.key);
    }

    DEFAULTS = {
        label: 'label',
        items: [],
        key: 'value',
        url: 'url'
    }

    LeaderBoard.prototype.initialize = function () {
        this.$div = $('<div/>').addClass('list-group leader-list');
        this.$element.append(this.$div);
    }

    LeaderBoard.prototype.sort = function(key) {



        this.$div.append(
            this.$div.find('.leader-item')
                .detach()
                .sort(function(a, b) {
                    var aval = parseFloat($(a).data(key));
                    var bval = parseFloat($(b).data(key));

                    return (aval > bval) ? -1 : (bval > aval) ? 1 : 0;
                })
        );

        this.$div.find('.item-score')
            .text(function(item){
                return $(this).closest('.leader-item').data(key);
            });
    }

    $.fn.leader = function (options) {

        options = $.extend({}, DEFAULTS, options);

        var obj = new LeaderBoard(this, options);

        $(this).data('.leader', obj);
        return obj;
    }

} ( jQuery ));

