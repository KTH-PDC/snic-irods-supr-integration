/*  Authors:
 *    Petr Vobornik <pvoborni@redhat.com>
 *
 * Copyright (C) 2010 Red Hat
 * see file 'COPYING' for use and warranty information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

/* This web page implements the password change portal using SUPR
   authentication. It is a re-work of the IPA password change page. */

/* Page. */
var RP = {};

/* Main function which will be called on submit. */

RP.set_password = function(password, verification) {

    //possible results: 'ok', 'unauthenticated', 'policy-error'

    var status, result, reason, invalid, failure, data, request;

    /* Session ID. */
    var session;

    /* Default return status/result is failure. */
    status = 'invalid';
    result = {
        status: status,
        message: "Password change was not successful."
    };

    /* Return on success. */

    function success_handler(data, text_status, xhr) {

        result.status = xhr.getResponseHeader("X-IPA-Portal-Result") || status;

        /* Negative result. */
        if (result.status === 'unauthenticated') {
            result.message = "You do not posess a valid token from SUPR.";
        }

        /* Otherwise just return. */
        return result;
    }

    function error_handler(xhr, text_status, error_thrown) {
        return result;
    }

    /* Get session cookie. */
    session = Cookies.get("session");
    if (session === undefined) {
        console.log ("No session cookie");
        RP.show_error("No session cookie");
        return result;
    }

    /* Build the request. */
    data = {
        session: session,
        password: password,
        verification: verification
    };

    /* Debug log, need to be disabled. */
    console.log ("Request data as follows");
    console.log (data);

    request = {
        url: '/ipa/session/portal',
        data: data,
        contentType: 'application/x-www-form-urlencoded',
        processData: true,
        dataType: 'html',
        async: false,
        type: 'POST',
        success: success_handler,
        error: error_handler
    };

    /* !!!! Debug.
    alert ('Sending request');
    */
    $.ajax(request);

    return result;
};

/* Verify that required field is not empty. */

RP.verify_required = function(field, value) {

    var valid = true;

    if (!value || value === '') {
        valid = false;
        RP.show_error(field +" is required");
    }

    return valid;
};

/* Action on submit. */

RP.on_submit = function() {

    /* Get the fields from the form. */
    var password = $('#password').val();
    var verification = $('#verification').val();

    /* Checks. */
    if (!RP.verify_required('password', password)) return;
    if (!RP.verify_required('verification', verification)) return;
    if (password !== verification) {
        RP.show_error("Verification password did not match");
        return;
    }

    /* Check session cookie. */
    session = Cookies.get("session");
    if (session === undefined) {
        console.log ("No session cookie");
        RP.show_error("You don't have a session cookie");
        return;
    }


    /* Call the main function. */
    var result = RP.set_password(password, verification);

    /* Display results. */
    if (result.status !== 'ok') {
        RP.show_error(result.message);
    } else {
        RP.reset_form();
        RP.show_success("Password change was successful.");
        RP.redirect();
    }
};

/* Service functions as customary. */

RP.reset_form = function() {
    $('.alert-danger').css('display', 'none');
    $('.alert-success').css('display', 'none');
};

RP.show_error = function(message) {

    $('.alert-danger > p').text(message);
    $('.alert-danger').css('display', '');
    $('.alert-success').css('display', 'none');
};

RP.show_info = function(message) {

    $('.alert-info > p').text(message || '');
    if (!message) {
        $('.alert-info').css('display', 'none');
    } else {
        $('.alert-info').css('display', '');
    }
};

RP.show_success = function(message) {

    $('.alert-success > p').text(message);
    $('.alert-danger').css('display', 'none');
    $('.alert-success').css('display', '');
};

RP.parse_uri = function() {
    var opts = {};
    if (window.location.search.length > 1) {
        var couples = window.location.search.substr(1).split("&");
        for (var i=0,l=couples.length; i < l; i++) {
            var couple = couples[i].split("=");
            var key = decodeURIComponent(couple[0]);
            var value = couple.length > 1 ? decodeURIComponent(couple[1]) : '';
            opts[key] = value;
        }
    }
    return opts;
};

RP.redirect = function() {

    var opts = RP.parse_uri();
    var url = opts['url'];
    var delay = parseInt(opts['delay'], 10);

    var msg_cont = $('.alert-success > p');
    $('.redirect', msg_cont).remove();

    // button for manual redirection
    if (url) {
        var redir_cont = $('<span/>', { 'class': 'redirect' }).
            append(' ').
            append($('<a/>', {
                href: url,
                text: 'Continue to next page'
            })).
            appendTo(msg_cont);
    } else {
        return;
    }

    if (delay <= 0 || delay > 0) { // NaN check
        RP.redir_url = url;
        RP.redir_delay = delay;
        RP.redir_count_down();
    }
};

RP.redir_count_down = function() {

    RP.show_info("You will be redirected in " + Math.max(RP.redir_delay, 0) + "s");
    if (RP.redir_delay <= 0) {
        window.location = RP.redir_url;
        return;
    }
    window.setTimeout(RP.redir_count_down, 1000);
    RP.redir_delay--;
};

/* Init function. */

RP.init = function() {
    var opts = RP.parse_uri();
    if (opts['user']) {
        $("#user").val(opts['user']);
    }

    $('#set_password').submit(function() {
        RP.on_submit();
        return false;
    });
};

/* main (document onready event handler) */

$(function() {
    RP.init();
});

