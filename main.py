#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import webapp2
import cgi

form="""
<head>
    <title>Sign Up</title>
    <style type="text/css">
      .label {text-align: right}
      .error {color: red}
    </style>

  </head>

  <body>
    <h2>Signup</h2>
    <form method="post">
      <table>
        <tbody><tr>
          <td class="label">
            Username
          </td>
          <td>
            <input name="username" value="%(username)s" type="text">
          </td>
          <td class="error">
            %(error_username)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Password
          </td>
          <td>
            <input name="password" value="%(password)s" type="password">
          </td>
          <td class="error">
            %(error_password)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Verify Password
          </td>
          <td>
            <input name="verify" value="%(passverify)s" type="password">
          </td>
          <td class="error">
            %(error_passverify)s
          </td>
        </tr>

        <tr>
          <td class="label">
            Email (optional)
          </td>
          <td>
            <input name="email" value="%(email)s" type="text">
          </td>
          <td class="error">
            %(error_email)s
          </td>
        </tr>
      </tbody></table>

      <input type="submit">
    </form>
  

</body>

"""

def escape_html(s):
    return cgi.escape(s)

import re

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile("^.{3,20}$")
EMAIL_RE = re.compile("^[\S]+@[\S]+\.[\S]+$")

def valid_username(username):
	return USER_RE.match(username)

def valid_password(p):
	return PASS_RE.match(p)

def valid_email(email):
    if email:
        return EMAIL_RE.match(email)
    else:
        return True

class MainPage(webapp2.RequestHandler):
    def write_form(self,
            username="",
            error_username="",
            password="",
            passverify="",
            error_password="",
            error_passverify="",
            email="",
            error_email=""):

        self.response.out.write(form % {
            "username": username,
            "error_username": error_username,
            "password": password,
            "passverify": passverify,
            "error_password": error_password,
            "error_passverify": error_passverify,
            "email": email,
            "error_email": error_email})

    def post(self):
        usr_username = self.request.get("username")
        usr_password = self.request.get("password")
        usr_passverify = self.request.get("verify")
        usr_email = self.request.get("email")

        error_username = ""
        error_password = ""
        error_passverify = ""
        error_email = ""

        if not valid_username(usr_username):
            error_username = "invalid user name"

        if not usr_password == usr_passverify :
            error_passverify = "not correspand"
            usr_password = ""
            usr_passverify = ""

        elif not valid_password(usr_password):
            error_password = "invalid password"
            usr_password = ""
            usr_passverify = ""

        if not valid_email(usr_email):
            error_email = "invalid email"

        if ( error_username + error_password + error_passverify + error_email != "" ):
            self.write_form(usr_username, error_username,
				"", "", error_password, error_passverify,
				usr_email, error_email)
        else:
            self.redirect("/welcome?name=%s" % usr_username)

    def get(self):
        self.write_form()

class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
	usr_username = self.request.get("name")
        self.response.out.write("Welcome! %s" % usr_username)

app = webapp2.WSGIApplication([	('/', MainPage),
                                ('/welcome', WelcomeHandler),],
                                debug=True)
