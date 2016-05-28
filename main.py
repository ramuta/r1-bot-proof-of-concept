import webapp2
import json
import logging
from google.appengine.api import urlfetch
from secret import get_verify_token, get_page_access_token


class MainHandler(webapp2.RequestHandler):
    def get(self):
        return self.response.write('Hello world!')


def send_to_messenger(sender_id, message):
    respond = "User with ID %s said: %s" % (sender_id, message)
    json_data = {
        "recipient": {"id": sender_id},
        "message": {"text": respond}
    }
    url = "https://graph.facebook.com/v2.6/me/messages?access_token=" + get_page_access_token()
    logging.info(url)
    data = json.dumps(json_data)
    result = urlfetch.fetch(url=url, payload=data, method=urlfetch.POST, headers={"Content-Type": "application/json"})
    logging.info(str(result.content))


class WebhookHandler(webapp2.RequestHandler):
    def get(self):
        if self.request.get("hub.verify_token") == get_verify_token():
            return self.response.write(self.request.get("hub.challenge"))
        return self.response.write("Error! Wrong Verify Token")

    def post(self):
        messaging_events = json.loads(str(self.request.body).decode("utf-8"))
        logging.info(messaging_events)

        sender_id = messaging_events["entry"][0]["messaging"][0]["sender"]["id"]

        try:
            message = messaging_events["entry"][0]["messaging"][0]["message"]["text"]
            logging.info("%s: %s" % (sender_id, message))
            send_to_messenger(sender_id, message)
            return self.response.write("success")
        except Exception, e:
            error = "A POST without 'message' field."
            logging.info(error)
            return self.response.write("error: " + error)

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/webhook', WebhookHandler),
    webapp2.Route('/webhook/', WebhookHandler),
], debug=True)
