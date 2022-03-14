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
    png = SimpleUploadedFile("tiny.png", valid_png_bin)
    return png

POST_DATA = {
    'title': 'A post title about a post about web dev',
    'description': 'This post discusses stuff -- brief',
    'content_type': ContentType.PLAIN,
    'content': 'Þā wæs on burgum Bēowulf Scyldinga, lēof lēod-cyning, longe þrāge folcum gefrǣge (fæder ellor hwearf, aldor of earde), oð þæt him eft onwōc hēah Healfdene; hēold þenden lifde, gamol and gūð-rēow, glæde Scyldingas. Þǣm fēower bearn forð-gerīmed in worold wōcun, weoroda rǣswan, Heorogār and Hrōðgār and Hālga til; hȳrde ic, þat Elan cwēn Ongenþēowes wæs Heaðoscilfinges heals-gebedde. Þā wæs Hrōðgāre here-spēd gyfen, wīges weorð-mynd, þæt him his wine-māgas georne hȳrdon, oð þæt sēo geogoð gewēox, mago-driht micel. Him on mōd bearn, þæt heal-reced hātan wolde, medo-ærn micel men gewyrcean, þone yldo bearn ǣfre gefrūnon, and þǣr on innan eall gedǣlan geongum and ealdum, swylc him god sealde, būton folc-scare and feorum gumena. Þā ic wīde gefrægn weorc gebannan manigre mǣgðe geond þisne middan-geard, folc-stede frætwan. Him on fyrste gelomp ǣdre mid yldum, þæt hit wearð eal gearo, heal-ærna mǣst; scōp him Heort naman, sē þe his wordes geweald wīde hæfde. Hē bēot ne ālēh, bēagas dǣlde, sinc æt symle. Sele hlīfade hēah and horn-gēap: heaðo-wylma bād, lāðan līges; ne wæs hit lenge þā gēn þæt se ecg-hete āðum-swerian 85 æfter wæl-nīðe wæcnan scolde. Þā se ellen-gǣst earfoðlīce þrāge geþolode, sē þe in þȳstrum bād, þæt hē dōgora gehwām drēam gehȳrde hlūdne in healle; þǣr wæs hearpan swēg, swutol sang scopes. Sægde sē þe cūðe frum-sceaft fīra feorran reccan',
    'categories': 'web, tutorial',
    'visibility': Post.Visibility.PUBLIC,
    'unlisted': False,
}

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
