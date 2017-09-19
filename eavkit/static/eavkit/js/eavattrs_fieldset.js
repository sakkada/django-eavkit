(function ($) {
    // onload event
    $(function(){
        if ($('fieldset.eavattrs').length == 0) return;

        var get_option_from_label = function(label) {
            return '<option value="' + $(label).attr('for') + '">'
                   + $(label).text().replace(/(.+?):?$/, '$1')
                   + '</option>';
        }

        var eavattrs_empty = $('fieldset.eavattrs .form-row:has(input, select, textarea)' +
                                                          ':not(.field-eavattrs-add)' +
                                                          ':not(.errors):not(:has(label.required))').filter(function() {
            var result = [];
            $(this).find('> div').each(function() {
                $(this).prepend($('<div class="remove"><a href="$">Remove</a></div>'));
            })

            $(this).find('input, select, textarea').each(function() {
                if (this.tagName == 'SELECT'
                      && $(this).find('option').length == 3
                      && $(this).find('option:first').val() == "1") {
                    result.push($(this).val() != "1"); // NullBooleanField Select (3 options - 1, 2, 3, empty value is 1)
                } else if (this.tagName == 'SELECT' && $(this).attr('multiple')) {
                    result.push($(this).val() != null); // Multiple Select
                } else {
                    result.push($(this).val() != "");
                }
            })
            return result && result.indexOf(true) == -1;
        });

        $('fieldset.eavattrs div div.remove').css('float', 'right');
        $('fieldset.eavattrs div div.remove a').click(function() {
            // Hide row and erase field value
            $(this).parents('.form-row').hide();
            $(this).parents('.form-row').find('input, select').each(function() {
                if (this.tagName == 'SELECT'
                      && $(this).find('option').length == 3
                      && $(this).find('option:first').val() == "1") {
                    $(this).val("1"); // NullBooleanField Select (3 options - 1, 2, 3, empty value is 1)
                } else if (this.tagName == 'SELECT' && $(this).attr('multiple')) {
                    $(this).val(null); // Multiple Select
                } else {
                    $(this).val("");
                }
            })

            // Return option value to allow to add field again
            var label = $(this).parents('.form-row').find('label');
            $('.field-eavattrs-add select').append(get_option_from_label(label));
            return false;
        });

        var options = ['<option value="">------</option>'];
        eavattrs_empty.hide();
        eavattrs_empty.find('label').each(function() {
            options.push(get_option_from_label(this));
        });

        // add form-row with attrs enabler select
        $('fieldset.eavattrs h2').after($(
            '<div class="form-row field-eavattrs-add"><div>'
            + '<label for="id_eavattrs-add">Добавить атрибут:</label>'
            + '<select>' + options.join('') + '</select>'
            + '<p class="help">Выберите атрибут из выпадающего списка что бы добавиь его.</p>'
            + '</div></div>'
        ));

        $('.field-eavattrs-add select').change(function() {
            var value = $(this).val();
            if (value) {
                $(this).find('option[value="' + value + '"]').remove();
                $(this).parents('fieldset').find('#' + value).parents('.form-row').show();
                $(this).val('');
            }
            return false;
        });
    });

})(django.jQuery);
