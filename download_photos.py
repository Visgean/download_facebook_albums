#!/usr/bin/env python
import os
import urllib
from multiprocessing.dummy import Pool as ThreadPool

import facebook
from slugify import slugify


class ImageDownloader:
    def __init__(self, token, target=None, data_folder='data', pool_size=10):
        self.graph_api = facebook.GraphAPI(token)
        self.target = target
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
        data = self.graph_api.get_object(album_url, after=after, fields=fields) if after else self.graph_api.get_object(
            album_url,
            fields=fields)
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
            self.image_pool += [(blob['images'][0]['source'], folder_name) for blob in self.process_album(f_album) if
                                blob]


    def download_image(self, tupple_args):
        url_to_grab, image_folder = tupple_args
        basename = os.path.basename(url_to_grab)
        urllib.urlretrieve(url_to_grab, os.path.join(image_folder, basename))

    def start_pool(self):
        pool = ThreadPool(10)
        pool.map(self.image_pool, self.download_image())


if __name__ == '__main__':
    oauth_access_token = raw_input('Token from https://developers.facebook.com/tools/explorer/: ')

    user = raw_input('user/page: ')

    print 'Starting pools'

