import os
import app.crawlers.data_handlers.utils as api_utils
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.core.config import settings


def test_save_image():
    basedir = 'test'
    links_in = [
        'https://download.samplelib.com/png/sample-boat-400x300.png',
        'https://download.samplelib.com/png/sample-clouds2-400x300.png',
        'https://download.samplelib.com/png/sample-blue-400x300.png'
    ]
    links_out = api_utils.save_image(
        links_in=links_in,
        basedir=basedir,
        smm_engine=SmmEngine.twitter
    )
    assert len(links_out) > 0
    for link in links_out:
        filepath = os.path.join(settings.PATH_MEDIA, basedir, link)
        assert os.path.isfile(filepath)


def test_save_video():
    basedir = 'test'
    links_in = [
        'https://download.samplelib.com/mp4/sample-5s.mp4',
        'https://download.samplelib.com/mp4/sample-10s.mp4'
    ]
    links_out = api_utils.save_video(
        links_in=links_in,
        basedir=basedir,
        smm_engine=SmmEngine.twitter
    )
    assert len(links_out) > 0
    for link in links_out:
        filepath = os.path.join(settings.PATH_MEDIA, basedir, link)
        assert os.path.isfile(filepath)
