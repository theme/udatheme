import webapp2

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write("<h1>welcome</h1>")

app = webapp2.WSGIApplication([
    webapp2.Route(r'/', handler = MainPage, name='home')
    ], debug=True)

