// WARNING: The code that follows may make you cry:
//          A Safety pig has been provided below for your benefit
//                         _
// _._ _..._ .-',     _.._(`))
// '-. `     '  /-._.-'    ',/
//   )         \            '.
//  / _    _    |             \
// |  a    a    /              |
// \   .-.                     ;  
//  '-('' ).-'       ,'       ;
//     '-;           |      .'
//        \           \    /
//        | 7  .__  _.-\   \
//        | |  |  ``/  /`  /
//       /,_|  |   /,_/   /
//          /,_/      '`-'


var isAdmin;

function AnimateButton(button) {
    button.addClass('btn-success');
    setInterval(RemoveClass, 1000);
    function RemoveClass() {
        button.removeClass('btn-success');
    };
};

function GetUserData() {
    var request = $.ajax({
        dataType: 'json',
        type: 'get',
        url: '/api/users/',
        headers: {
            "Authorization": "Token " + localStorage.getItem("token")
        },
    });
    return request
};

function GetActiveUserData() {
    var request = $.ajax({
        dataType: 'json',
        type: 'get',
        url: '/api/users/search?is_active=true',
        headers: {
            "Authorization": "Token " + localStorage.getItem("token")
        },
    });
    return request
};

function BuildTable() {
    var request = GetUserData();

    request.fail(function(data) {
        console.log(data.responseJSON);
    });
    request.done(function(data) {
        IsAdmin(data);
        var table = $('#example').DataTable( {
            'data': data,
            'columns': [
                {
                    "className": 'details-control',
                    "orderable": 'false',
                    "data": null,
                    "defaultContent": ''
                },
                {'data': 'first_name'},
                {'data': 'last_name'},
                {'data': 'username'},
                {'data': 'birthday'},
                {'data': 'email'}
            ]
         });
        $('#example tbody').on('click', 'td.details-control', function () {
            var tr = $(this).closest('tr');
            var row = table.row( tr );
            if (row.child.isShown() ) {
                row.child.hide();
                tr.removeClass('shown');
            }
            else {
                var rowChilds = isAdmin ? 
                        [ChangeUserForm(row.data(), row), PasswordChangeForm(row.data()), UpdateGroupsForm(row.data())] 
                        : 
                        [ChangeUserForm(row.data(), row), UpdateGroupsForm(row.data())]

                row.child( rowChilds ).show();
  
                tr.addClass('shown');

            }
        });
        if ( isAdmin ) {
            $('#createUser>div').append(
                $('<a>', {'class': 'btn btn-primary',
                        'data-toggle': 'collapse',
                        'href': '#createNew',
                        'aria-expanded': 'false',
                        'aria-controls': 'createNew',
                        'id': 'createNewButton'}).text('Create New User')
            );

            $('#createUserForm').unbind('submit').bind('submit', function (event) { 
                var form = $(this);
                $('.form-row>div>input.is-invalid').removeClass('is-invalid');
                $('.invalid-feedback').remove();
                submitCreateUserForm(form);
                event.preventDefault();
            });

            $('#example').closest('.container').prepend(
                $('<button>', {'id': 'activeFilter', 'class': 'btn btn-primary', 'type': 'button'}).text('Show only active users')
            );

            $('#activeFilter').on('click', function() {
                var button = $(this);
                if (! button.hasClass('filtered') ) {
                    var request = GetActiveUserData();
                    request.done(function(data) {
                        button.addClass('filtered')
                        table.clear();
                        table.rows.add(data).draw();
                        button.text('Show All Users')
                    });
                } else {
                    var request = GetUserData();
                    request.done(function(data) {
                        button.removeClass('filtered')
                        table.clear();
                        table.rows.add(data).draw();
                        button.text('Show only active users')
                        });
                    }
                });
        }
    });
};

$(document).ready(function() {
    var logOutLink = document.getElementById('logout');
    logOutLink.addEventListener('click', function(event) {
        event.preventDefault();
        localStorage.removeItem('token');
        localStorage.removeItem('is_admin');
        window.location.replace('/login/');
    });
    BuildTable();
});

var formProperties = {
    'username': ['Username', 'text'],
    'first_name': ['First Name', 'text'],
    'last_name': ['Last Name', 'text'],
    'email': ['E-mail', 'email'],
    'password': ['Password', 'password'],
    'birthday': ['Birthday', 'date'],
    'city': ['City', 'text'],
    'country': ['Country', 'text'],
    'district': ['District', 'text'],
    'street': ['Street', 'text'],
    'zip_code': ['Zip-code', 'text'],
    'date_joined': ['Date Joined', 'text'],
    'last_update': ['Last Updated', 'text'],
    'is_active': ['Is Active', 'checkbox']
};

var alwaysReadonly = ['date_joined', 'last_update']

function ChangeUserForm(data, row) {
    var tmpl = $('<div>', {'class': 'card'}).append(
        $('<div>', {'class': 'card-body'}).append('<form>', 'userInfo')
    );
    var form = tmpl.find('form')
    data = unpackObj(data);
    for ( var property in data ) {
        if ( formProperties.hasOwnProperty(property) ) {
            var formGroup = $('<div>', {'class': 'form-group row'}).append(
                $('<label>', {'for': property, 'class': 'col-sm-2 col-form-label'}).text(formProperties[property][0]),
                $('<div>', {'class': 'col-sm-10'}).append(
                    $('<input>', {'type': formProperties[property][1], 'class': 'form-control', 'id': property, 'placeholder': formProperties[property][0], 'value': data[property]})
                )
            );
            if ( ! isAdmin ) {
                formGroup.find('input').attr('readonly', 'readonly');
            } else if ( alwaysReadonly.includes(property) ) {
                formGroup.find('input').attr('readonly', 'readonly');
            }
            if (property == 'is_active' && data[property]) {
                formGroup.find('input').attr('checked', 'checked');
            }
            form.append(formGroup);
        }
    }
    if ( isAdmin ) {
        form.append($('<button>', {'class': 'btn btn-primary', 'type': 'submit'}).text('Update User'));
    }

    $(form).unbind('submit').bind('submit', function(event) {
        console.log(event);
        event.preventDefault();
        $('.form-group.row>div>input.is-invalid').removeClass('is-invalid');
        $('.invalid-feedback').remove();
        var form = $(this)
        var username = row.data().username
        var formData = GatherFormData(form);
        var request = $.ajax({
            dataType: 'json',
            type: 'patch',
            url: '/api/users/'+username+'/',
            headers: {
                "Authorization": "Token " + localStorage.getItem("token"),
                "Content-Type": "application/json; charset=utf-8"
            },
            data: JSON.stringify(formData),
        });

        request.fail( function (data) {
            var errors = data.responseJSON;
            console.log(errors);
            for ( var property in errors ) {
                if ( property == 'detail' ) {
                    $(form).append('<div class="invalid-feedback">' + errors[property]+ '</div>')
                }
                else if ( property == 'address') {
                    for (var addressProperty in errors[property]) {
                        if ( errors[property].hasOwnProperty(addressProperty) ) {
                            $('input[id='+addressProperty+']').addClass('is-invalid');
                            $('#'+addressProperty).parent().append('<div class="invalid-feedback">' + errors[property][addressProperty] + '</div>');
                        }
                    }
                }
                else if ( errors.hasOwnProperty(property) ) {
                    $('input[id='+property+']').addClass('is-invalid');
                    $('#'+property).parent().append('<div class="invalid-feedback">' + errors[property][0] + '</div>');
                }
            }
        });
        request.done( function (data) {
            var button = form.find($('button[type=submit]'))
            AnimateButton(button);
            row.data(data);
            form.find('input[id=last_update]').val(data.last_update);
        });
    });

    return form;
};

function UpdateGroupsForm(rowData) {

    var groupsData = rowData.groups;
    var main_block = $('<form>', {'id': 'userGroupsForm'});

    var userGroups = $('<div>', {'class': 'user-groups'}).append(
        $('<h5>', {'class': 'text-center'}).text('User Groups'),
        $('<select>', {'id': 'userGroupsSelect', 'class': 'form-control', 'multiple': 'multiple'})
    ).appendTo(main_block);
    if ( isAdmin ) {
        var controls = $('<div>', {'class': 'control-arrows text-center'}).append(
            $('<input>', {'type': 'button', 'id': 'buttonAllRight', 'value': '>>', 'class': 'btn btn-default'}),$('<br/>'),
            $('<input>', {'type': 'button', 'id': 'buttonRight', 'value': '>', 'class': 'btn btn-default'}),$('<br/>'),
            $('<input>', {'type': 'button', 'id': 'buttonLeft', 'value': '<', 'class': 'btn btn-default'}),$('<br/>'),
            $('<input>', {'type': 'button', 'id': 'buttonAllLeft', 'value': '<<', 'class': 'btn btn-default'})
        ).appendTo(main_block)

        var availableGroups = $('<div>', {'class': 'available-groups'}).append(
            $('<h5>', {'class': 'text-center'}).text('Available Groups'),
            $('<select>', {'id': 'availableGroupsSelect', 'class': 'form-control', 'multiple': 'multiple'})
        ).appendTo(main_block)
    }
    var all_groups = [];

    var request = $.ajax({
                    dataType: 'json',
                    type: 'get',
                    url: '/api/groups/',
                    headers: {
                        "Authorization": "Token " + localStorage.getItem("token")
                    },
                    encode: true,
            });

    request.done(function(data) {
        $.each(data, function(i, group) {
            all_groups.push(group.name);
        });
        var diff = $(all_groups).not(groupsData).get();
        for ( var i = 0; i< groupsData.length; i++ ) {
            userGroups.find('select').append(
                $('<option>', {'value': groupsData[i]}).text(groupsData[i])
            )
        }
        if ( isAdmin ) {
            for ( var i = 0; i < diff.length; i++ ) {
                availableGroups.find('select').append(
                    $('<option>', {'value': diff[i]}).text(diff[i])
                )
            }
            main_block.append($('<button>', {'class': 'btn btn-primary', 'type': 'submit', 'id': 'updateGroups'}).text('Update Groups'));

            $('#buttonRight').click(function( event ) {
                var selectedOpts = $('#userGroupsSelect option:selected');
                $('#availableGroupsSelect').append($(selectedOpts).clone());
                $(selectedOpts).remove();
                event.preventDefault();
            });

            $('#buttonAllRight').click(function( event ) {
                var selectedOpts = $('#userGroupsSelect option');
                $('#availableGroupsSelect').append($(selectedOpts).clone());
                $(selectedOpts).remove();
                event.preventDefault();
            });

            $('#buttonLeft').click(function( event ) {
                var selectedOpts = $('#availableGroupsSelect option:selected');
                $('#userGroupsSelect').append($(selectedOpts).clone());
                $(selectedOpts).remove();
                event.preventDefault();
            });

            $('#buttonAllLeft').click(function( event ) {
                var selectedOpts = $('#availableGroupsSelect option');
                $('#userGroupsSelect').append($(selectedOpts).clone());
                $(selectedOpts).remove();
                event.preventDefault();
            });

            $(main_block).unbind('submit').bind('submit', function(event) {
                main_block.find('.invalid-feedback').remove();
                var groups = userGroups.find('select').children();
                var groupNames = [];
                $.each(groups, function(i, group) {
                    groupNames.push($(group).val());
                });
                
                var username = rowData.username;
                var request = $.ajax({
                    dataType: 'json',
                    type: 'put',
                    url: '/api/users/'+username+'/groups/',
                    headers: {
                        "Authorization": "Token " + localStorage.getItem("token"),
                        "Content-Type": "application/json; charset=utf-8"
                    },
                    data: JSON.stringify({'groups': groupNames}),
                });
            
                request.fail( function (data) {
                    $(mainblock).prepend('<div class="invalid-feedback">' + data.responseJSON['groups'] + '</div>')
                    console.log(data.responseJSON);
                });
                request.done( function (data) {
                    AnimateButton($('#updateGroups'));
                });
            event.preventDefault();
            });
        }
    });

    return main_block
};

function IsAdmin(data) {
    var userObject = data[0];
    if ( userObject.hasOwnProperty('date_joined') ) {
        localStorage.setItem('is_admin', true)
        isAdmin = true;
    } else {
        localStorage.setItem('is_admin', false)
        isAdmin = false;
    }
};

function unpackObj(obj, user={}) {
    for ( var property in obj ) {
        if ( obj.hasOwnProperty(property) ) {
            if (typeof obj[property] === 'object' && ! Array.isArray(obj[property])) {
                user = unpackObj(obj[property], user);
            } else {
                user[property] = obj[property]
            }
        }
    }
    return user
}

function GatherFormData(form) {

    var addressData = {
        'city': form.find($('#city')).val(),
        'country': form.find($('#country')).val(),
        'district': form.find($('#district')).val(),
        'street': form.find($('#street')).val(),
        'zip_code': form.find($('#zip_code')).val(),
    };
    var formData = {
        'address': addressData,
        'username': form.find($('#username')).val(),
        'first_name': form.find($('#first_name')).val(),
        'last_name': form.find($('#last_name')).val(),
        'email': form.find($('#email')).val(),
        'birthday': form.find($('#birthday')).val(),
        'is_active': form.find($('#is_active')).is(':checked')
    };
    return formData;
};

function submitCreateUserForm(form) {
    var formData = GatherFormData(form);
    var username = formData.username;
    var password = form.find($('#password')).val()
    formData['password'] = password;
    // because we use GatherFormData for updates and creation we need to manualy set
    // is_active to True on new user creation because this field is not present
    // in form for new user creatin thus it's allways will be false.
    formData['is_active'] = true
    var request = $.ajax({
        dataType: 'json',
        type: 'post',
        url: '/api/users/',
        headers: {
            "Authorization": "Token " + localStorage.getItem("token"),
            "Content-Type": "application/json; charset=utf-8"
        },
        data: JSON.stringify(formData),
    });

    request.fail( function (data) {
        var errors = data.responseJSON;
        console.log(errors);
        for ( var property in errors ) {
            if ( property == 'detail' ) {
                $(form).append('<div class="invalid-feedback">' + errors[property]+ '</div>')
            }
            else if ( property == 'address') {
                for (var addressProperty in errors[property]) {
                    if ( errors[property].hasOwnProperty(addressProperty) ) {
                        $('input[id='+addressProperty+']').addClass('is-invalid');
                        $('#'+addressProperty).parent().append('<div class="invalid-feedback">' + errors[property][addressProperty] + '</div>');
                    }
                }
            }
            else if ( errors.hasOwnProperty(property) ) {
                $('input[id='+property+']').addClass('is-invalid');
                $('#'+property).parent().append('<div class="invalid-feedback">' + errors[property][0] + '</div>');
            }
        }
    });
    request.done( function (data) {
        var table = $('#example').DataTable()
        table.row.add(data).draw();
        AnimateButton($('#CreateUser'));
        form[0].reset();
    });
};


function PasswordChangeForm(Rowdata) {
    var username = Rowdata.username;
    var form = $('<form>', {'id': 'passwordChangeForm'});
    var passwordBlock = $('<div>', {'class': 'form-group row'}).append(
        $('<label>', {'for': 'password', 'class': 'col-sm-2 col-form-label'}).text('Password'),
            $('<div>', {'class': 'col-sm-10'}).append(
                $('<input>', {'type': 'password',
                            'class': 'form-control',
                            'id': 'password',
                            'placeholder': '********'})
            )
        ).appendTo(form)

    var button = $('<button>', {'type': 'submit', 'id': 'changePassword', 'class': 'btn btn-primary'}).text('Change Password').appendTo(form);

    $(form).unbind('submit').bind('submit', function(event) {
        var requestPasswordChange = $.ajax({
                    dataType: 'json',
                    type: 'patch',
                    url: '/api/users/'+username+'/',
                    headers: {
                        "Authorization": "Token " + localStorage.getItem("token"),
                        "Content-Type": "application/json; charset=utf-8"
                    },
                    data: JSON.stringify({'password': $('input[id=password]').val()})
        });
        requestPasswordChange.fail(function(data) {
            console.log(data.responseJSON);
        });

        requestPasswordChange.done(function(data) {
            AnimateButton(button);
            $('input[id=last_update]').val(data.last_update);
        });
        event.preventDefault();
    });
    return form
}   