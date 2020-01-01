import os
from multiprocessing import Pool
import functools
import datetime
from enum import Enum
import requests
import bs4


class Newspaper(Enum):
    """
    The ids used by banca sapo for each newspaper.
    """
    Abola = 4137
    Record = 4139
    Ojogo = 4138


class Resolution(Enum):
    R320x398 = (320, 398)
    R640x795 = (640, 795)
    R910x1131 = (910, 1131)
    R870x1081 = (870, 1081)
    R1050x1305 = (1050, 1305)

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def html_str(self):
        return f'W={self.width}&H={self.height}'


def _days_range(start, end):
    day = start
    while day <= end:
        yield day
        day += datetime.timedelta(days=1)


class Crawler(object):
    """Crawls the covers of sports newspapers from sapo 24

    """
    def __init__(self):
        super(Crawler, self).__init__()
        self._newspaper = Newspaper.Abola
        self._start = datetime.date.today()
        self._end = datetime.date.today()
        self._resolution = Resolution.R1050x1305

    @property
    def newspaper(self):
        return self._newspaper

    @newspaper.setter
    def newspaper(self, np: Newspaper):
        self._newspaper = np

    @property
    def resolution(self):
        return self._resolution

    @resolution.setter
    def resolution(self, res: Resolution):
        self._resolution = res

    def timerange(self,
                  start: datetime.date,
                  end: datetime.date = datetime.date.today()):
        if start > end:
            raise 'Mispecified time range: start later than end.'

        self._start = start
        self._end = end

    def crawl(self, out_dir='.'):
        p = Pool(5)
        crawl_fn = functools.partial(Crawler._crawl,
                                     newspaper=self._newspaper,
                                     resolution=self._resolution,
                                     out_dir=out_dir)
        results = p.map(crawl_fn, _days_range(self._start, self._end))

    @staticmethod
    def _crawl(day: datetime.date, newspaper, resolution, out_dir):
        filename = f'{newspaper.name}_{day}'
        print(f'{filename}: Downloading')
        response = requests.get(Crawler.url(newspaper, day))
        if response.status_code != 200:
            print(f'{filename}: Error getting page')
            return

        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        picture_tag = soup.findAll('picture')[0]
        if not picture_tag:
            print(f'{filename}: No picture tag found. Skipping')
            return

        image_url = Crawler.filter_image_sources_by_resolution(
            picture_tag, resolution)
        if not image_url:
            print(f'{filename}: No image url found')
            return

        with open(os.path.join(out_dir, filename + '.jpeg'), 'wb') as f:
            f.write(requests.get(image_url).content)
            f.close()

        return (filename, image_url)

    @staticmethod
    def url(newspaper: Newspaper, date: datetime.date):
        return f'https://24.sapo.pt/jornais/desporto/{newspaper.value}/{date.isoformat()}'

    @staticmethod
    def filter_image_sources_by_resolution(pic_tag, res: Resolution):
        for pc in pic_tag.descendants:
            not_html_tag = type(pc) != bs4.element.Tag
            if not_html_tag:
                continue
            jpeg_image = pc['type'] == 'image/jpeg'
            correct_resolution = res.html_str() not in pc['srcset']
            if jpeg_image and correct_resolution:
                return 'http:' + pc['data-srcset']

        return None


def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', '--out', type=str, default='./data/covers/')
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    crawler = Crawler()
    crawler.newspaper = Newspaper.Abola
    today = datetime.date.today()
    crawler.timerange(start=datetime.date(2019, 1, 1), end=datetime.date(2019, 12, 31))
    crawler.crawl(out_dir=args.out)

    crawler.newspaper = Newspaper.Record
    crawler.timerange(start=datetime.date(2019, 1, 1), end=datetime.date(2019, 12, 31))
    crawler.crawl(out_dir=args.out)

    crawler.newspaper = Newspaper.Ojogo
    crawler.timerange(start=datetime.date(2019, 1, 1), end=datetime.date(2019, 12, 31))
    crawler.crawl(out_dir=args.out)


if __name__ == '__main__':
    main()
