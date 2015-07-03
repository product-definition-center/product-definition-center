(function () {
    "use strict";
    var createAddButton = function () {
        var txt =
            '<div class="btn-group">' +
            '  <button type="button" class="btn btn-success add btn-sm">' +
            '      <span class="glyphicon glyphicon-plus"></span>' +
            '  </button>' +
            '  <button type="button" class="btn btn-success btn-sm dropdown-toggle" data-toggle="dropdown">' +
            '      <span class="caret"></span>' +
            '      <span class="sr-only">Toggle Dropdown</span>' +
            '  </button>' +
            '  <ul class="dropdown-menu" role="menu">' +
            '      <li><a href="#" class="add-more" data-add-val="5">Add 5</a></li>' +
            '      <li><a href="#" class="add-more" data-add-val="10">Add 10</a></li>' +
            '  </ul>' +
            '</div>';
        return txt;
    };

    var removeHandler = function (event) {
        var that = $(event.target);
        var remaining = that.parents(".main-form").find(".remove");
        console.log(that.parents(".row"));
        that.parents(".main-form .row").remove();
        if (remaining.length <= 2) { /* NOTE: removed button is still counted */
            remaining.addClass('disabled');
        }
        return false;
    };

    var extractType = function (element) {
        return element.find('input').attr('name').split('-')[0];
    };

    var getAndUpdateTotal = function (type) {
        var total = parseInt($('#id_' + type + '-TOTAL_FORMS').val(), 10);
        $('#id_' + type + '-TOTAL_FORMS').val(total + 1);
        return total;
    };

    var setTotal = function (type, val) {
        return $('#id_' + type + '-TOTAL_FORMS').val(val);
    };

    var resetField = function (field, total) {
        var that = $(field);
        var name = that.attr('name').replace(/-\d+-/, '-' + total + '-');
        that.attr({'name': name, 'id': 'id_' + name});
        if (that.attr('type') !== 'hidden') {
            that.val('');
        }
    };

    var addHandler = function () {
        var newElement = $(this).parents(".row").find(".main-form .row:last-child").clone();
        var type = extractType(newElement);
        var total = getAndUpdateTotal(type);
        console.log(type);
        console.log(total);

        newElement.find('input').each(function () { resetField(this, total); });
        $(this).parents('.row').find('.main-form').append(newElement);
        newElement.find('.remove').on('click', removeHandler);
        $(this).parents(".row").find(".remove").removeClass("disabled");
    };

    var multiAddHandler = function (event) {
        for (var i = 0, n = $(this).data('add-val'); i < n; i++) {
            $(this).parents(".btn-group").find(".add").click();
        }
        event.preventDefault();
    };

    $(document).ready(function () {
        $(".btn-container").each(function () { $(this).append(createAddButton()); });
        $(".remove").on('click', removeHandler);
        $(".add").on('click', addHandler);
        $(".add-more").on('click', multiAddHandler);
        $("input[type=checkbox]").map(function (event) {
            var label = $('<span class="label label-primary">Changed</span>');
            $(this).after(label);
            var initial = $(this).parents(".center-align").data("init") == "True" ? true : false;
            if (initial == $(this).is(':checked')) {
                label.addClass('hidden');
            }
        });
        $("input[type=checkbox]").on('change', function (event) {
            var label = $(this).parents('.center-align').find('span.label');
            label.toggleClass('hidden');
        });

        $(".add-variant").click(function () {
            var variantTotal = getAndUpdateTotal('vararch');
            var form = $(".new-variant-pair").last().clone();
            console.log(variantTotal);
            console.log(form);

            var formTotal = getAndUpdateTotal('for_new_vararch');

            form.find(".main-form .form-row").slice(1).remove();
            form.find(".row.text-danger").remove();
            form.find(".row").removeClass("bg-danger");
            form.find(".header-form input").each(function () { resetField(this, variantTotal); });
            form.find(".body-form input").each(function () { resetField(this, formTotal); });
            form.find("input[name$=-new_variant]").val(variantTotal);

            form.find('.add').on('click', addHandler);
            form.find('.add-more').on('click', multiAddHandler);
            form.find('.remove').on('click', removeHandler).addClass('disabled');

            $("form > .btn-group").before(form);
        });
    });
})();
