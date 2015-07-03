(function () {
    "use strict";
    var fill_data = function (data) {
        $.each(data, function (key, value) {
            var elem = $("#" + key);
            if (typeof(value) == 'string') {
                elem.text(value);
            }
            else if (typeof(value) == 'boolean') {
                elem.text(value ? "yes" : "no");
            }
            else if (value instanceof Array) {
                if (value.length === 0) {
                    elem.html('<p><em>Empty</em></p>');
                } else {
                    elem.html('');
                    var lst = $('<ul></ul>');
                    $.each(value, function (i) { lst.append('<li>'+value[i]+'</li>'); });
                    elem.append(lst);
                }
            }
        });
    };

    $("form").submit(function () {
        var form = $(this);
        var btn = form.find("button");
        var spinner = $('<div class="spinner"></div>');
        btn.find("span").hide();
        btn.addClass("disabled").append(spinner).blur();
        $.ajax({
            type: "POST",
            url: form.attr("action"),
            data: form.serialize(),
            success: function (data) {
                fill_data(data);
            },
            error: function (data, _status, reason) {
                btn.after('<div class="alert alert-danger">' +
                          '  <span class="pficon-layered">' +
                          '    <span class="pficon pficon-error-octagon"></span>' +
                          '    <span class="pficon pficon-error-exclamation"></span>' +
                          '  </span>' +
                          '  <strong>' + reason + '</strong>' +
                          '</div>');
            },
            complete: function (data) {
                spinner.remove();
                btn.removeClass("disabled").show().find("span").show();
            }
        });
        return false;
    });
})();
