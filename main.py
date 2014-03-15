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
<form method="post">
    Your birthday?
    <br>
    <label> Month 
        <input type="text" name="month" value="%(month)s">
    </label>
    <label> Day 
        <input type="text" name="day" value="%(day)s">
    </label>
    <label> Year
        <input type="text" name="year" value="%(year)s">
    </label>

    <div style="color:red">%(error)s</div>
    <br>
    <br>
    <input type="submit">
</form>
"""

months = ['January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December']

month_abbvs = dict((m[:3].lower(),m) for m in months)

def escape_html(s):
    return cgi.escape(s)

def valid_month(month):
    if month:
        short_month = month[:3].lower()
        return month_abbvs.get(short_month)

def valid_day(day):
    if day and day.isdigit():
        d = int(day)
        if 0 < d and d < 32:
            return d

def valid_year(year):
    if year and year.isdigit():
        y = int(year)
        if 1900 < y and y < 2020:
            return y


class MainPage(webapp2.RequestHandler):
    def write_form(self, error="", month="", day="", year=""):
        self.response.out.write(form % {"error": error,
                                        "month": escape_html(month),
                                        "day": escape_html(day),
                                        "year": escape_html(year)})

    def post(self):
        usr_month = self.request.get("month")
        usr_day = self.request.get("day")
        usr_year = self.request.get("year")


        month = valid_month(usr_month)
        day = valid_day(usr_day)
        year = valid_year(usr_year)

        if not ( month and day and year ):
            self.write_form("invalid",
                usr_month,usr_day,usr_year)
        else:
            self.redirect("/thanks")

    def get(self):
        self.write_form()

class ThanksHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Thanks! Valid")
        


app = webapp2.WSGIApplication([	('/', MainPage),
                                ('/thanks', ThanksHandler),],
				 				debug=True)
