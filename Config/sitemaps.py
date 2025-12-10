from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "monthly"

    def items(self):
        return [
            "home:home",      # صفحه اصلی
            "zlink:recode",   # صفحه Mode X / ReCode
        ]

    def location(self, item):
        return reverse(item)
