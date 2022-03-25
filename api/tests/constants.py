from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, ContentType


def get_test_image_jpeg():
    jpeg = SimpleUploadedFile('img.jpeg', '', content_type='image/jpeg')
    return jpeg

# by dsalaj on Stack Overflow at https://stackoverflow.com/a/42502775


def get_test_image_png():
    valid_png_hex = ['\x89', 'P', 'N', 'G', '\r', '\n', '\x1a', '\n', '\x00',
                     '\x00', '\x00', '\r', 'I', 'H', 'D', 'R', '\x00',
                     '\x00', '\x00', '\x01', '\x00', '\x00', '\x00', '\x01',
                     '\x08', '\x02', '\x00', '\x00', '\x00', '\x90',
                     'w', 'S', '\xde', '\x00', '\x00', '\x00', '\x06', 'b', 'K',
                     'G', 'D', '\x00', '\x00', '\x00', '\x00',
                     '\x00', '\x00', '\xf9', 'C', '\xbb', '\x7f', '\x00', '\x00',
                     '\x00', '\t', 'p', 'H', 'Y', 's', '\x00',
                     '\x00', '\x0e', '\xc3', '\x00', '\x00', '\x0e', '\xc3',
                     '\x01', '\xc7', 'o', '\xa8', 'd', '\x00', '\x00',
                     '\x00', '\x07', 't', 'I', 'M', 'E', '\x07', '\xe0', '\x05',
                     '\r', '\x08', '%', '/', '\xad', '+', 'Z',
                     '\x89', '\x00', '\x00', '\x00', '\x0c', 'I', 'D', 'A', 'T',
                     '\x08', '\xd7', 'c', '\xf8', '\xff', '\xff',
                     '?', '\x00', '\x05', '\xfe', '\x02', '\xfe', '\xdc', '\xcc',
                     'Y', '\xe7', '\x00', '\x00', '\x00', '\x00',
                     'I', 'E', 'N', 'D', '\xae', 'B', '`', '\x82']
    valid_png_bin = bytes("".join(valid_png_hex), "utf-8")
    png = SimpleUploadedFile(name="test.png", content=valid_png_bin, content_type='image/png')
    return png


POST_IMG_DATA = {
    'title': 'Test Image',
    'description': 'This post is an image :P',
    'content_type': ContentType.PNG,
    'content': 'No',
    'img_content': get_test_image_png(),
    'categories': 'test',
    'visibility': Post.Visibility.PUBLIC,
    'unlisted': False,
}

# TODO: Update this when our groupmates have updated their interface
SAMPLE_REMOTE_POST = '''
[{
  "id": "https://psdt11.herokuapp.com/authors/28b32de4-e5cc-4840-a6ea-8c05dca9dae6/posts/a8cd37e4-be1c-4f86-99cb-b20b1440606f",
  "type": "post",
  "author": {
    "type": "author",
    "id": "https://psdt11.herokuapp.com/authors/28b32de4-e5cc-4840-a6ea-8c05dca9dae6",
    "url": "https://psdt11.herokuapp.com/authors/28b32de4-e5cc-4840-a6ea-8c05dca9dae6",
    "host": "https://psdt11.herokuapp.com/",
    "display_name": "Jarrett Knauer",
    "github": "https://github.com/jlknauer"
  },
  "comment_src": [
    {
      "type": "comment",
      "author": {
        "type": "author",
        "id": "https://psdt11.herokuapp.com/authors/28b32de4-e5cc-4840-a6ea-8c05dca9dae6",
        "url": "https://psdt11.herokuapp.com/authors/28b32de4-e5cc-4840-a6ea-8c05dca9dae6",
        "host": "https://psdt11.herokuapp.com/",
        "display_name": "Jarrett Knauer",
        "github": "https://github.com/jlknauer"
      },
      "comment": "First comment on the post!",
      "published": "2022-03-23T00:01:32Z",
      "id": "https://psdt11.herokuapp.com/authors/28b32de4-e5cc-4840-a6ea-8c05dca9dae6/posts/a8cd37e4-be1c-4f86-99cb-b20b1440606f/comments/e1b71a73-f302-4999-916a-2f5d57c4c626"
    }
  ],
  "title": "Hello from Team 11",
  "source": "",
  "origin": "",
  "description": "This is a test post",
  "content_type": "text/plain",
  "content": "Web dev sucks",
  "count": 0,
  "comments": "https://psdt11.herokuapp.com/authors/28b32de4-e5cc-4840-a6ea-8c05dca9dae6/posts/a8cd37e4-be1c-4f86-99cb-b20b1440606f/comments",
  "published": "2022-03-23T00:01:32Z",
  "visibility": "PUBLIC",
  "unlisted": false
}]'''

SAMPLE_REMOTE_AUTHOR = '''
{
    "type": "authors",
    "items": [
        {
        "id": "32d6cbd8-3a30-4a78-a4c4-c1d99e208f6a",
        "host": "https://cmput404-project-t12.herokuapp.com/",
        "displayName": "zhijian1",
        "github": "https://github.com/Zhijian-Mei",
        "profileImage": "/mysite/img/default_mSfB41u.jpeg"
        }
    ]
}'''
