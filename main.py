# -*- coding: utf-8 -*-

import webapp2
import os
import jinja2
from webapp2_extras import json
from webapp2_extras import sessions

from datetime import datetime

from google.appengine.ext import ndb
import facebook


# Facebook app details
FB_APP_ID = '436609680013936'
FB_APP_NAME = 'CampFinder'
FB_APP_SECRET = '5b71a69e0c707ae1b968546bc6366aa6'


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class User(ndb.Model):
    id = ndb.StringProperty(nullable=False, primary_key=True)
    created = ndb.DateTimeProperty(default=datetime.utcnow, nullable=False)
    updated = ndb.DateTimeProperty(default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)
    name = ndb.StringProperty(nullable=False)
    profile_url = ndb.StringProperty(nullable=False)
    access_token = ndb.StringProperty(nullable=False)



class MyHandler(webapp2.RequestHandler):
    # ...
    @property
    def current_user(self):
        # check if user logged in during this session
        if self.session.get("user"):
            # user is logged in
            return self.session.get("user")
        else:
            # either user just logged in or just saw the first page
            # we'll see here
            fb_user = facebook.get_user_from_cookie(self.request.cookies, FB_APP_ID, FB_APP_SECRET)
            if fb_user:
                # okay so user logged in.
                # now, check to see if existing user

                graph = facebook.GraphAPI(fb_user["access_token"])
                profile = graph.get_object("me")

                # DB # user = User.get_by_key_name(PREFIX+fb_user["uid"])
                # NDB # user = ndb.Key("User",PREFIX+str(profile["id"])).get()
                user = ndb.Key("User",str(profile["id"])).get()
                # you can add prefix if you're using multiple social networks (g+, twitter)
                if not user:
                    # not an existing user so get user info
                    # DB # user = User(key_name = PREFIX+str(profile["id"]), OTHER DATA)
                    # NDB # user = User(id = PREFIX+str(profile["id"]), OTHER DATA)
                    user = User(id = str(profile["id"]), name = str(profile["name"]))
                    user.put()
                elif user.SOMETHING_THAT_MIGHT_CHANGE != fb_user["SOMETHING_THAT_MIGHT_CHANGE"]:
                    # update values that changed since las check to database
                    user.SOMETHING_THAT_MIGHT_CHANGE = fb_user["SOMETHING_THAT_MIGHT_CHANGE"]
                    user.put()
                # User is now logged in
                # Save often used values to session so you don't have to query database all the time
                self.session["user"] = dict(
                    id = str(profile["id"]),
                    email = profile["email"],
                    access_token = fb_user["access_token"]
                )
                return self.session.get("user")
            return None


    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()


class GetJSon(webapp2.RequestHandler):
    def get(self):
        self.response.content_type = 'application/json'
        obj = {
            'Hello': 'World',
            'Connected to': 'Awesome fagprojekt!',
        }
        self.response.write(json.encode(obj))

class MainHandler(webapp2.RequestHandler):
    def get(self):

        current_user = self.current_user
        graph = facebook.GraphAPI(self.current_user['access_token'])

        output="""
        Nope
        """
        self.response.write(output + " ")



# remember to pass config to webapp2.WSGIApplication:
app = webapp2.WSGIApplication(
    [('/', MainHandler),
     '/data', GetJSon], #handlers
    debug=True # debug state
)



