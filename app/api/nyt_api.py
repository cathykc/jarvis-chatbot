import requests


def get_top_articles():
    articles = []
    url = "https://api.nytimes.com/svc/mostpopular/v2/mostviewed" \
          "/all-sections/1.json"
    url += '?' + "api-key=4149d1e3df254bc1b8bac5dca3ba38cb"
    r = requests.get(url)

    for i in range(0, 5):
        print "success"
        image_url = r.json()['results'][i]['media'][0]['media-metadata'][0]['url']
        abstract = r.json()['results'][i]['abstract']
        article = {}
        article["title"] = r.json()['results'][i]['title']
        article["subtitle"] = abstract
        article["item_url"] = r.json()['results'][i]['url']
        article["image_url"] = image_url

        buttons = [{"type": "postback", "title" : "Read here",
                    "payload"
                    : "nyt"}]
        article["buttons"] = buttons
        articles.append(article)
    return articles

get_top_articles()
