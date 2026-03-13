from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    @staticmethod
    def force_https_on_url(url):
        if not url:
            return url
        if "https" not in url and "http" in url:
            return url.replace("http", "https")
        return url

    def get_next_link(self):
        return self.force_https_on_url(super().get_next_link())

    def get_previous_link(self):
        return self.force_https_on_url(super().get_previous_link())
