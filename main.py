import webapp2
import json
import logging
from google.appengine.api import urlfetch
from secret import get_verify_token, get_page_access_token, get_api_ai_client_access_token


class MainHandler(webapp2.RequestHandler):
    def get(self):
        return self.response.write('Hello world! I am a bot :)')


def send_to_messenger(sender_id, message):
    json_data = {
        "recipient": {"id": sender_id},
        "message": {"text": message}
    }
    url = "https://graph.facebook.com/v2.6/me/messages?access_token=" + get_page_access_token()
    logging.info(url)
    data = json.dumps(json_data)
    result = urlfetch.fetch(url=url, payload=data, method=urlfetch.POST, headers={"Content-Type": "application/json"})
    logging.info(str(result.content))


def send_to_api_ai(message, sender_id):
    auth = get_api_ai_client_access_token()
    url = "https://api.api.ai/v1/query"
    params = {"query": message, "v": "20150910", "sessionId": "1234567890", "lang": "en"}
    logging.info(str(params))
    result = urlfetch.fetch(url=url,
                            payload=json.dumps(params),
                            method=urlfetch.POST,
                            headers={'Content-Type': 'application/json; charset=utf-8',
                                     "Authorization": "Bearer %s" % auth})
    logging.info(str(result.content))
    bot_response = json.loads(result.content)
    speech = bot_response["result"]["speech"]
    logging.info(speech)
    if not speech:
        send_to_messenger(sender_id, "Sorry, didn't understand what you mean... Ask me something else :)")
    else:
        send_to_messenger(sender_id, speech)


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
            send_to_api_ai(message, sender_id)
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
