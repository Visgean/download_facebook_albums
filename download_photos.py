#!/usr/bin/env python
import os
import urllib
from multiprocessing.dummy import Pool as ThreadPool

import facebook
from slugify import slugify


class ImageDownloader:
    def __init__(self, token, data_folder='data', pool_size=10):
        self.graph_api = facebook.GraphAPI(token)
        self.data_folder = data_folder
        self.pool_size = pool_size

        self.image_pool = []

    def process_pages(self, root_url, after=None):
        data = self.graph_api.get_object(root_url, after=after) if after else self.graph_api.get_object(root_url)
        albums = data['data']
        if 'paging' in data and 'after' in data['paging']['cursors']:
            albums += self.process_pages(root_url, after=data['paging']['cursors']['after'])
        return albums

    def process_album(self, album, after=None):
        album_url = '{album_id}/photos'.format(album_id=album['id'])
        fields = ['images']
        data = self.graph_api.get_object(album_url, after=after, fields=fields) if after else self.graph_api.get_object(album_url, fields=fields)
        image_blobs = data['data']
        if 'paging' in data and 'after' in data['paging']['cursors']:
            image_blobs += self.process_album(album, after=data['paging']['cursors']['after'])
        return image_blobs

    def scrap_user(self, user):
        root = '/{user}/albums'.format(user=user)
        for f_album in self.process_pages(root):
            folder_name = os.path.join(self.data_folder, slugify(user), slugify(f_album['name']))
            if not os.path.isdir(folder_name):
                os.makedirs(folder_name)
            self.image_pool += [(blob['images'][0]['source'], folder_name) for blob in self.process_album(f_album)]

    def scrap_friends(self):
        friends = [f['username'] if f.has_key('username') else f['id'] for f in self.graph_api.get_object('/me/friends/', fields = ['username'], limit=5000)['data']]
        for friend in friends:
            self.scrap_user(friend)

    def download_image(self, tupple_args):
        url_to_grab, image_folder = tupple_args
        basename = os.path.basename(url_to_grab)
        urllib.urlretrieve(url_to_grab, os.path.join(image_folder, basename))

    def start_pool(self):
        pool = ThreadPool(self.pool_size)
        pool.map(self.download_image, self.image_pool)


if __name__ == '__main__':
    oauth_access_token = raw_input('Token from https://developers.facebook.com/tools/explorer/: ')
    fd = ImageDownloader(oauth_access_token)
    fd.scrap_user('me')
    # fd.scrap_friends()            # this takes a long time - you would need better token
    print 'Downloading images'
    fd.start_pool()
