$(document).ready(function() {
    $('form').submit(function(event) {
        var formData = {
            'name' : $('input[name=name]').val(),
            'password': $('input[name=password]').val()
        };

        $.ajax({
            type : 'post',
            url: 'http://127.0.0.1:8000/api-auth/',
            data : formData,
            encode: true
        }).done(function(data) {
            console.log(data);
        });
        
        event.preventDefault();
    });
});