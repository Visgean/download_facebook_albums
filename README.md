

```python
if __name__ == '__main__':
    oauth_access_token = raw_input('Token from https://developers.facebook.com/tools/explorer/: ')

    fd = ImageDownloader(oauth_access_token)

    # scrap my own albums
    fd.scrap_user('me')

    # download all my friends albums
    fd.scrap_friends()

    # start downloading
    fd.start_pool()

```