$(function () {

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', csrf_token);
            }
        }
    });
    // hide or show tag edit form
    $('#tag-btn').click(function () {
        $('#tags').hide();
        $('#tag-form').show();
    });
    $('#cancel-tag').click(function () {
        $('#tag-form').hide();
        $('#tags').show();
    });
    // hide or show description edit form
    $('#description-btn').click(function () {
        $('#description').hide();
        $('#description-form').show();
    });
    $('#cancel-description').click(function () {
        $('#description-form').hide();
        $('#description').show();
    });
    // delete confirm modal
    $('#confirm-delete').on('show.bs.modal', function (e) {
        $('.delete-form').attr('action', $(e.relatedTarget).data('href'));
    });

    $("[data-toggle='tooltip']").tooltip({ title: moment($(this).data('timestamp')).format('lll') })


    var flash = null;

    function toast(body) {
        clearTimeout(flash);
        var $toast = $('#toast');
        $toast.text(body).fadeIn();
        flash = setTimeout(function () {
            $toast.fadeOut();
        }, 3000);
    }

    var hover_timer = null;

    function show_profile_popover(e) {
        var $el = $(e.target);

        hover_timer = setTimeout(function () {
            hover_timer = null;
            $.ajax({
                type: 'GET',
                url: $el.data('href'),
                success: function (data) {
                    $el.popover({
                        html: true,
                        content: data,
                        trigger: 'manual',
                        animation: false
                    });
                    $el.popover('show');
                    $('.popover').on('mouseleave', function () {
                        setTimeout(function () {
                            $el.popover('hide');
                        }, 200);
                    });
                },
                error: function (error) {
                    toast('Server error, please try again later.');
                }
            });
        }, 500);
    }

    function hide_profile_popover(e) {
        var $el = $(e.target);

        if (hover_timer) {
            clearTimeout(hover_timer);
            hover_timer = null;
        } else {
            setTimeout(function () {
                if (!$('.popover:hover').length) {
                    $el.popover('hide');
                }
            }, 200);
        }
    }

    $('.profile-popover').hover(show_profile_popover.bind(this), hide_profile_popover.bind(this));

    $(function () {
        function render_time() {
            return moment($(this).data('timestamp')).format('lll')
        }
        $('[data-toggle="tooltip"]').tooltip(
            { title: render_time }
        );
    });

    /* $(document).ready(function(){
        $(".card").mouseover(function(){
            $(this).css({"box-shadow":'5px 5px 20px #cec8c8'});
          });
        $(".card").mouseout(function(){
            $(this).css({"box-shadow":''});
          });
        $("pre").addClass("p-3 mb-2");
        $(".flask-pagedown-preview").addClass("p-3 mb-2 bg-light text-dark");
          
    }) */
    $(document).ajaxError(function (event, request, settings) {
        var message = null;
        if (request.responseJSON && request.responseJSON.hasOwnProperty('message')) {
            message = request.responseJSON.message;
        } else if (request.responseText) {
            var IS_JSON = true;
            try {
                var data = JSON.parse(request.responseText);
            }
            catch (err) {
                IS_JSON = false;
            }
            if (IS_JSON && data !== undefined && data.hasOwnProperty('message')) {
                message = JSON.parse(request.responseText).message;
            } else {
                message = default_error_message;
            }
        } else {
            message = default_error_message;
        }
        toast(message, 'error');
    });



    var flash = null;

    function toast(body) {
        clearTimeout(flash);
        var $toast = $('#toast');
        $toast.text(body).fadeIn();
        flash = setTimeout(function () {
            $toast.fadeOut();
        }, 3000);
    }

    var hover_timer = null;

    function show_profile_popover(e) {
        var $el = $(e.target);

        hover_timer = setTimeout(function () {
            hover_timer = null;
            $.ajax({
                type: 'GET',
                url: $el.data('href'),
                success: function (data) {
                    $el.popover({
                        html: true,
                        content: data,
                        trigger: 'manual',
                        animation: false
                    });
                    $el.popover('show');
                    $('.popover').on('mouseleave', function () {
                        setTimeout(function () {
                            $el.popover('hide');
                        }, 200);
                    });
                },
            });
        }, 500);
    }


    function update_follower_count(id) {
        var $el = $('#followers-count-' + id);
        $.ajax({
            type: 'GET',
            url: $el.data('href'),
            success: function (data) {
                $el.text(data.count)
            }
        });
    }

    function follow(e) {
        var $el = $(e.target);
        var id = $el.data('id')
        $.ajax({
            type: 'POST',
            url: $el.data('href'),
            success: function (data) {
                $el.prev().show();
                $el.hide();
                update_follower_count(id);
                toast(data.message);
            }
        });
    }

    function unfollow(e) {
        var $el = $(e.target);
        var id = $el.data('id');

        $.ajax({
            type: 'POST',
            url: $el.data('href'),
            success: function (data) {
                $el.next().show();
                $el.hide();
                update_follower_count(id);
                toast(data.message);
            }
        });
    }

    function hide_profile_popover(e) {
        var $el = $(e.target);

        if (hover_timer) {
            clearTimeout(hover_timer);
            hover_timer = null;
        } else {
            setTimeout(function () {
                if (!$('.popover:hover').length) {
                    $el.popover('hide');
                }
            }, 200);
        }
    }

    $('.profile-popover').hover(show_profile_popover.bind(this), hide_profile_popover.bind(this));
    $(document).on('click', '.follow-btn', follow.bind(this));
    $(document).on('click', '.unfollow-btn', unfollow.bind(this));

});