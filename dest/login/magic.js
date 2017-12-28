$(document).ready(function() {
    $('form').submit(function(event) {
        var formData = {
            'username' : $('input[name=username]').val(),
            'password': $('input[name=password]').val()
        };

        var request = $.ajax({
                          dataType: 'json',
                          type : 'post',
                          url: '/api/api-auth/',
                          data : formData,
                          encode: true
                      });

        request.fail(function (data) {
            var errors = data.responseJSON;
            for (var property in errors) {
                if (errors.hasOwnProperty(property)) {
                    $('#' + property).find('.invalid-feedback').append(errors[property][0])
                    $('input[name=' + property + ']').addClass('is-invalid');
                    if (property == 'non_field_errors') {
                        $('input[type=text]').addClass('is-invalid');
                        $('input[type=password]').addClass('is-invalid');
                    }
                }
            }
        });

        request.done(function(data) {
            var token = data.token;
            localStorage.setItem('token', token);
            window.location.replace('../');
        });
    event.preventDefault();
    });
});