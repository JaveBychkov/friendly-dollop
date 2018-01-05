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

var isAdmin = JSON.parse(localStorage.getItem('is_admin'))

function AnimateButton(button) {
    button.addClass('btn-success');
    setInterval(RemoveClass, 1000);
    function RemoveClass() {
        button.removeClass('btn-success');
    };
};

$(document).ready(function() {
    var logOutLink = document.getElementById('logout');
    logOutLink.addEventListener('click', function(event) {
        event.preventDefault();
        localStorage.removeItem('token');
        window.location.replace('../login/');
    });
    $('#createGroupForm').unbind('submit').bind('submit', function(event) {
        var form = $(this);
        var formData = {'name': form.find('input[id=groupName]').val()}

        var request = $.ajax({
            dataType: 'json',
            type: 'post',
            url: '../api/groups/',
            headers: {
                "Authorization": "Token " + localStorage.getItem("token"),
                "Content-Type": "application/json; charset=utf-8"
            },
            data: JSON.stringify(formData),
        });

        request.fail( function (data) {
            console.log(data.responseJSON);
        });
        request.done( function (data) {
            var table = $('#example').DataTable();
            table.row.add(data).draw();
            AnimateButton($('#createNewGroup'));
        });

        event.preventDefault();
    });

    var requestGroups = $.ajax({
        dataType: 'json',
        type: 'get',
        url: '/api/groups/',
        headers: {
            "Authorization": "Token " + localStorage.getItem("token")
        },
    });

    requestGroups.fail(function(data) {
        console.log(data.responseJSON)
    });

    requestGroups.done( function (data) {
        var table = $('#example').DataTable( {
            'data': data,
            'columns': [
                {
                    "className": 'details-control',
                    "orderable": 'false',
                    "data": null,
                    "defaultContent": ''
                },
                {'data': 'name'},
                {'data': 'users_count'},
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
                row.child( [groupInfo(row.data(), row), ChangeGroupUsers(row.data(), row), DeleteGroup(row.data(), row)] ).show();
                tr.addClass('shown');
            }
        });

        if ( isAdmin ) {
            $('#createGroup').append(
                $('<a>', {'class': 'btn btn-primary',
                          'data-toggle': 'collapse',
                          'href': '#createNew', 
                          'aria-expanded': 'false',
                          'aria-controls': 'createNew',
                          'id': 'createNewButton'
                        }
                ).text('Create New Group')
            );
        }
    }); // end ajax
});

function DeleteGroup(data, row) {
    var button = $('<button>', {'class': 'btn btn-danger', 'type': 'button', 'id': 'deleteGroup'}).text('Delete Group');
    $(button).on('click', function() {
        button.parent().find('.invalid-feedback').remove();
        var request = $.ajax({
            dataType: 'json',
            type: 'delete',
            url: '../api/groups/'+data.name+'/',
            headers: {
                "Authorization": "Token " + localStorage.getItem("token"),
                "Content-Type": "application/json; charset=utf-8"
            }
        });
        request.fail(function(data) {
            $(button).parent().prepend('<div class="invalid-feedback">' + data.responseJSON['detail'] + '</div>')
            console.log(data.responseJSON);
        });
        request.done(function(data) {
            var table = $('#example').DataTable()
            table.row(row).remove().draw( false );
        });
    });
    return button;
}

function groupInfo(data, row) {
    var tmpl = $('<div>', {'class': 'card'}).append(
        $('<div>', {'class': 'card-body'}).append($('<form>', {'id': 'updateGroupForm'}))
    );
    var form = tmpl.find('form')
    var formGroup = $('<div>', {'class': 'form-group row'}).append(
        $('<label>', {'for': 'name', 'class': 'col-sm-2 col-form-label'}).text('Group Name'),
        $('<div>', {'class': 'col-sm-10'}).append(
            $('<input>', {'type': 'text',
                        'class': 'form-control',
                        'id': 'name',
                        'placeholder': 'Group Name',
                        'value': data['name']}))
        );
    form.append(formGroup);
    if ( ! isAdmin ) {
        formGroup.find('input').attr('readonly', 'readonly');
    } else {
        form.append($('<button>', {'class': 'btn btn-primary', 'type': 'submit', 'id':'updateGroupName'}).text('Update Group Name'));
    }
    
    $(form).unbind('submit').bind('submit', function(event) {
        var name = data.name;
        var request = $.ajax({
            dataType: 'json',
            type: 'patch',
            url: '../api/groups/'+data.name+'/',
            headers: {
                "Authorization": "Token " + localStorage.getItem("token"),
                "Content-Type": "application/json; charset=utf-8"
            },
            data: JSON.stringify({'name': name}),
        });

        request.fail(function (data) {
            console.log(data.responseJSON)
        });

        request.done(function (data) {
            AnimateButton($('#updateGroupName'));
            row.data(data);
        });
        event.preventDefault();
    });

    return form
    };

function ChangeGroupUsers(GroupData, row) {
    var main_block = $('<form>', {'id': 'GroupUsersForm'});

    var groupUsers = $('<div>', {'class': 'group-users'}).append(
        $('<h5>', {'class': 'text-center'}).text('Users in Group'),
        $('<select>', {'id': 'groupUsersSelect', 'class': 'form-control', 'multiple': 'multiple'})
    ).appendTo(main_block);

    var requestGroupDetail = $.ajax({
                    dataType: 'json',
                    type: 'get',
                    url: '../api/groups/'+GroupData.name+'/',
                    headers: {
                        "Authorization": "Token " + localStorage.getItem("token")
                    },
            });

    requestGroupDetail.done(function(data) {
        var usersOfGroup = data.users;

        for ( var i = 0; i< usersOfGroup.length; i++ ) {
            groupUsers.find('select').append(
                $('<option>', {'value': usersOfGroup[i]}).text(usersOfGroup[i])
            )
        }
    if ( isAdmin ) {
        var controls = $('<div>', {'class': 'control-arrows text-center'}).append(
            $('<input>', {'type': 'button', 'id': 'buttonAllRight', 'value': '>>', 'class': 'btn btn-default'}),$('<br/>'),
            $('<input>', {'type': 'button', 'id': 'buttonRight', 'value': '>', 'class': 'btn btn-default'}),$('<br/>'),
            $('<input>', {'type': 'button', 'id': 'buttonLeft', 'value': '<', 'class': 'btn btn-default'}),$('<br/>'),
            $('<input>', {'type': 'button', 'id': 'buttonAllLeft', 'value': '<<', 'class': 'btn btn-default'})
        ).appendTo(main_block)
    
        var allUsers = $('<div>', {'class': 'all-users'}).append(
            $('<h5>', {'class': 'text-center'}).text('All Users'),
            $('<select>', {'id': 'allUsers', 'class': 'form-control', 'multiple': 'multiple'})
        ).appendTo(main_block)

        var requestUsers = $.ajax({
                    dataType: 'json',
                    type: 'get',
                    url: '../api/users/',
                    headers: {
                        "Authorization": "Token " + localStorage.getItem("token")
                    },
        });

        requestUsers.done( function (data) { 
            var UsersArray = [];

            for (var i = 0; i < data.length; i++) {
                UsersArray.push(data[i].username);
            }
            var diff = $(UsersArray).not(usersOfGroup).get();
            for ( var i = 0; i < diff.length; i++ ) {
                allUsers.find('select').append(
                    $('<option>', {'value': diff[i]}).text(diff[i])
                )
            }
            main_block.append($('<button>', {'class': 'btn btn-primary', 'type': 'submit', 'id': 'updateGroupUsers'}).text('Update Groups'));

            $('#buttonRight').click(function( event ) {
                var selectedOpts = $('#groupUsersSelect option:selected');
                $('#allUsers').append($(selectedOpts).clone());
                $(selectedOpts).remove();
                event.preventDefault();
            });

            $('#buttonAllRight').click(function( event ) {
                var selectedOpts = $('#groupUsersSelect option');
                $('#allUsers').append($(selectedOpts).clone());
                $(selectedOpts).remove();
                event.preventDefault();
            });

            $('#buttonLeft').click(function( event ) {
                var selectedOpts = $('#allUsers option:selected');
                $('#groupUsersSelect').append($(selectedOpts).clone());
                $(selectedOpts).remove();
                event.preventDefault();
            });

            $('#buttonAllLeft').click(function( event ) {
                var selectedOpts = $('#allUsers option');
                $('#groupUsersSelect').append($(selectedOpts).clone());
                $(selectedOpts).remove();
                event.preventDefault();
            });

            $(main_block).unbind('submit').bind('submit', function(event) {
                main_block.find('.invalid-feedback').remove();
                var users = groupUsers.find('select').children();
                var usersNames = [];
                $.each(users, function(i, user) {
                    usersNames.push($(user).val());
                });
                
                var groupName = GroupData.name;
                var request = $.ajax({
                    dataType: 'json',
                    type: 'patch',
                    url: '/api/groups/'+groupName+'/',
                    headers: {
                        "Authorization": "Token " + localStorage.getItem("token"),
                        "Content-Type": "application/json; charset=utf-8"
                    },
                    data: JSON.stringify({'users': usersNames}),
                });
            
                request.fail( function (data) {
                    $(main_block).prepend('<div class="invalid-feedback">' + data.responseJSON['users'] + '</div>')
                    console.log(data.responseJSON);
                });
                request.done( function (data) {
                    AnimateButton($('#updateGroupUsers'));
                    row.data(data);
                });
                event.preventDefault();
            });
    });
    }
    });
    return main_block
};