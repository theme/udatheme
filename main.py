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
<h2>Enter some text to ROT13:</h2>
<form method="post">
    <textarea style="height:100px; width: 400px;" name="text">%(txt)s</textarea>
    <br>
    <input type="submit">
</form>
"""

def escape_html(s):
    return cgi.escape(s)

c1="ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz"
c2="NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm"


class MainPage(webapp2.RequestHandler):
    def write_form(self, text=""):
        self.response.out.write(form % {"txt": escape_html(text)})

    def post(self):
        usr_text = self.request.get("text")
        text = escape_html(usr_text)
        rot13_text = ""

        for c in usr_text:
            if c in c1: 
                rot13_text += c2[c1.find(c)] 
            else:
                rot13_text += c

        self.write_form(rot13_text)

    def get(self):
        self.write_form()

app = webapp2.WSGIApplication([	('/', MainPage),],
				 				debug=True)
