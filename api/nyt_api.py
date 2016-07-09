import requests


def get_top_articles():
    articles = []
    url = "https://api.nytimes.com/svc/mostpopular/v2/mostviewed" \
          "/all-sections/1.json"
    url += '?' + "api-key=4149d1e3df254bc1b8bac5dca3ba38cb"
    r = requests.get(url)
    for i in range(0, 5):
        image_url = r.json()['results'][i]['media'][0]['media-metadata'][0]['url']
        # print image_url
        # print r.json()['results'][i]['title']
        # print r.json()['results'][i]['url']
        print "made it here"
        article = {}
        article["title"] = r.json()['results'][i]['title']
        article["subtitle"] = "temp"
        article["item_url"] = r.json()['results'][i]['url']
        article["image_url"] = image_url

        buttons = [{"type": "postback", "title" : "Read here",
                    "payload"
                    : "payload for yelp homies"}]
        article["buttons"] = buttons
        articles.append(article)
    return articles
